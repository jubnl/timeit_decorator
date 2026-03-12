import importlib
import logging
import multiprocessing
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from multiprocessing import Pool
from typing import Optional, Callable

from ._shared import _NO_RESULT, _single_run_output, _multi_run_output, _first_valid_result


def _multiprocessing_instance_method_call(instance, method_name, *args, **kwargs):
    """Call an instance method by name using reflection (used in multiprocessing)."""
    method = getattr(instance, method_name)
    return method(*args, **kwargs)


def _timeit_worker(worker_args):
    """Worker function that executes a function and records execution time."""
    logger = logging.getLogger("timeit.decorator._timeit_worker")
    try:
        if isinstance(worker_args[0], str):
            # Module-level function referenced by module name + qualname (multiprocessing path).
            # Looking up by name retrieves the wrapper, whose non-MainProcess short-circuit
            # then calls through to the original function directly.
            module_name, qualname, func_args, func_kwargs, timeout, enforce_timeout = worker_args
            module = sys.modules.get(module_name) or importlib.import_module(module_name)
            obj = module
            for part in qualname.split('.'):
                obj = getattr(obj, part)
            wrapped_func = lambda: obj(*func_args, **func_kwargs)
        elif isinstance(worker_args[1], str):
            # Instance method referenced by name on its instance.
            instance, method_name, method_args, method_kwargs, timeout, enforce_timeout = worker_args
            wrapped_func = lambda: getattr(instance, method_name)(*method_args, **method_kwargs)
        else:
            # Regular function object (threading path only).
            func, func_args, func_kwargs, timeout, enforce_timeout = worker_args
            wrapped_func = lambda: func(*func_args, **func_kwargs)

        timed_out = False

        execution_start = time.time()
        func_result = wrapped_func()
        execution_time = time.time() - execution_start

        # Log if execution time exceeded timeout but was not forcibly stopped
        if timeout is not None and execution_time > timeout and not enforce_timeout:
            logger.warning(
                f"Timeout exceeded (took {execution_time}s, timeout was {timeout}s), but execution continued.")
            timed_out = True

        return execution_time, func_result, timed_out

    except Exception as e:
        logging.error(f"Error in _timeit_worker: {e}")
        return None, _NO_RESULT, None


def _collect_threaded_results(futures, enforce_timeout, timeout, logger):
    """Collect results from thread futures, applying optional timeout enforcement."""
    results = []
    for i, future in enumerate(futures):
        try:
            result = future.result(timeout=timeout) if enforce_timeout and timeout is not None else future.result()
            results.append(result)
        except TimeoutError:
            logger.warning(f"Function execution {i} exceeded timeout of {timeout}s and was canceled.")
            future.cancel()
            results.append((timeout, _NO_RESULT, True))
        except Exception as e:
            logger.error(f"Function execution {i} failed with: {e}")
            results.append((None, _NO_RESULT, None))
    return results


def _build_worker_args(func, args, kwargs, runs, timeout, enforce_timeout, use_multiprocessing=False):
    """Build per-run worker argument tuples."""
    if args and hasattr(args[0], func.__name__):
        return [(args[0], func.__name__, args[1:], kwargs, timeout, enforce_timeout) for _ in range(runs)]
    if use_multiprocessing and '<locals>' not in func.__qualname__:
        # Pass by module + qualname instead of function object to avoid PicklingError when the
        # decorator syntax (@timeit_sync) replaces the module-level name with the wrapper.
        # Only applicable to module-level functions; nested/local functions fall through to the
        # function-object path (which may fail to pickle, matching pre-existing behaviour).
        return [(func.__module__, func.__qualname__, args, kwargs, timeout, enforce_timeout) for _ in range(runs)]
    return [(func, args, kwargs, timeout, enforce_timeout) for _ in range(runs)]


def _execute_parallel_runs(worker_args, workers, use_multiprocessing, enforce_timeout, timeout, logger):
    """Run worker tasks using thread pool or process pool and return results."""
    mode = 'multiprocessing' if use_multiprocessing else 'threading'
    logger.debug(f"Starting {mode} tasks with {workers} workers")
    if use_multiprocessing:
        if enforce_timeout:
            raise ValueError("enforce_timeout=True is not supported with use_multiprocessing=True")
        with Pool(workers) as pool:
            return pool.map(_timeit_worker, worker_args)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_timeit_worker, wa) for wa in worker_args]
        return _collect_threaded_results(futures, enforce_timeout, timeout, logger)


def _run_single_and_log(func, args, kwargs, log_level, detailed, timeout, enforce_timeout, logger):
    """Execute func once (fast path), warn if enforce_timeout was set, and log the result."""
    if enforce_timeout and timeout:
        logger.warning(
            "enforce_timeout=True is ignored when runs=1 and workers=1 in sync mode — no parallelism or cancellation is possible.")
    start_time = time.time()
    result = func(*args, **kwargs)
    execution_time = time.time() - start_time
    logger.log(log_level, _single_run_output(func, args, kwargs, execution_time, detailed))
    return result


def _sync_decorator(func, runs, workers, log_level, use_multiprocessing, detailed, timeout, enforce_timeout):
    """Build the sync wrapper for a given function and timing configuration."""
    logger = logging.getLogger("timeit.decorator")

    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        if threading.current_thread() is not threading.main_thread() or \
                multiprocessing.current_process().name != 'MainProcess':
            return func(*args, **kwargs)

        if runs == 1 and workers == 1:
            return _run_single_and_log(func, args, kwargs, log_level, detailed, timeout, enforce_timeout, logger)

        worker_args = _build_worker_args(func, args, kwargs, runs, timeout, enforce_timeout, use_multiprocessing)
        results = _execute_parallel_runs(worker_args, workers, use_multiprocessing, enforce_timeout, timeout, logger)

        times = [r[0] for r in results if r and r[0] is not None]
        valid_results = [r[1] for r in results if r and r[1] is not _NO_RESULT]

        if not times:
            logger.error(f"{func.__name__}: All function executions failed or returned None.")
            return None if not detailed else []

        logger.log(log_level, _multi_run_output(func, args, kwargs, runs, workers, times, results, detailed))
        return _first_valid_result(valid_results)

    return sync_wrapper


def timeit_sync(
        runs: int = 1,
        workers: int = 1,
        log_level: Optional[int] = logging.INFO,
        use_multiprocessing: bool = False,
        detailed: bool = False,
        timeout: Optional[float] = None,
        enforce_timeout: bool = False
):
    """
        Time the execution of a function with options for multiple runs and workers.

        This decorator can use either threading or multiprocessing for executing the
        function multiple times in parallel, depending on the nature of the task.
        It measures and logs the execution time, reporting the average and median times.

        :param runs: Number of times to run the function (minimum 1).
        :type runs: int
        :param workers: Number of concurrent workers (minimum 1, max equals 'runs').
        :type workers: int
        :param log_level: Logging level for timing information (e.g., logging.INFO).
        :type log_level: Optional[int]
        :param use_multiprocessing: Use multiprocessing if True, otherwise use threading.
                                    Suitable for CPU-bound tasks when True.
        :type use_multiprocessing: bool
        :param detailed: get a detailed output with different stats about the execution time.
        :type detailed: bool
        :param timeout: An optional timeout in seconds for each function execution.
        :type timeout: Optional[float]
        :param enforce_timeout: Enforce timeout. False by default. If True and the timeout is reached, it will cancel the
                                execution. Does not work in single execution in sync mode.
        :type enforce_timeout: bool
        :return: The return value of the function from its first execution.
        :rtype: Any
        :raises ValueError: If 'runs' or 'workers' are set to less than 1.

        For I/O-bound tasks (like file operations, network calls), threading is generally
        more efficient due to lower overhead and the GIL's release during I/O operations.
        For CPU-bound tasks, multiprocessing bypasses the GIL and may provide better performance.

        .. note::
           Choose the execution mode (threading or multiprocessing) based on the task at hand.
           Threading is the default mode for its efficiency with I/O-bound tasks.

        **Example**::

            @timeit(runs=10, workers=4, log_level=logging.DEBUG, use_multiprocessing=True)
            def cpu_intensive_function(n):
                # Function implementation

            @timeit(runs=5, workers=2)
            def io_bound_function(n):
                # Function implementation
        """

    if runs < 1 or workers < 1:
        raise ValueError("Both runs and workers must be at least 1")

    workers = min(workers, runs)

    if log_level is None:
        log_level = logging.INFO

    def decorator(func: Callable):
        return _sync_decorator(func, runs, workers, log_level, use_multiprocessing, detailed, timeout, enforce_timeout)

    return decorator
