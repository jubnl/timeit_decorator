import logging
import multiprocessing
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from multiprocessing import Pool
from statistics import stdev, median, mean
from typing import Optional, Callable

from tabulate import tabulate


def _multiprocessing_instance_method_call(instance, method_name, *args, **kwargs):
    """Call an instance method by name using reflection (used in multiprocessing)."""
    method = getattr(instance, method_name)
    return method(*args, **kwargs)


def _timeit_worker(worker_args):
    """Worker function that executes a function and applies a timeout."""
    logger = logging.getLogger("timeit.decorator._timeit_worker")
    try:
        # Distinguish between instance method and regular function
        if isinstance(worker_args, tuple) and isinstance(worker_args[1], str):
            instance, method_name, method_args, method_kwargs, timeout, enforce_timeout = worker_args
            wrapped_func = lambda: getattr(instance, method_name)(*method_args, **method_kwargs)
        else:
            func, func_args, func_kwargs, timeout, enforce_timeout = worker_args
            wrapped_func = lambda: func(*func_args, **func_kwargs)

        # Enforce timeout using a thread-based executor
        timed_out = False

        # Time the function execution
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
        return None, None, None


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

    # Ensure workers do not exceed number of runs
    workers = min(workers, runs)

    if log_level is None:
        log_level = logging.INFO

    def decorator(func: Callable):
        logger = logging.getLogger("timeit.decorator")
        logger.setLevel(log_level)

        if not logging.getLogger().hasHandlers():
            logging.basicConfig(
                level=log_level,
                format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):

            # Prevent nested decorators inside thread/process workers
            if threading.current_thread() is not threading.main_thread():
                return func(*args, **kwargs)
            if multiprocessing.current_process().name != 'MainProcess':
                return func(*args, **kwargs)

            # Fast path: single run, no concurrency
            if runs == 1 and workers == 1:
                if enforce_timeout and timeout:
                    logger.warning(
                        "enforce_timeout=True is ignored when runs=1 and workers=1 in sync mode — no parallelism or cancellation is possible.")
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                if detailed:
                    output = tabulate([
                        ["Function", func],
                        ["Args", args[1:]],
                        ["Kwargs", kwargs],
                        ["Duration", f"{execution_time}s"]
                    ], tablefmt="plain")
                else:
                    output = f"{func.__name__}: Exec: {execution_time:.6f}s"
                logger.log(log_level, output)
                return result

            # Determine if function is an instance method
            is_instance_method = args and hasattr(args[0], func.__name__)

            if is_instance_method:
                # Prepare arguments for instance method execution
                method_target = args[0]
                worker_args = [
                    (method_target, func.__name__, args[1:], kwargs, timeout, enforce_timeout)
                    # Ensure correct argument structure
                    for _ in range(runs)
                ]
            else:
                # Prepare arguments for function execution
                worker_args = [(func, args, kwargs, timeout, enforce_timeout) for _ in range(runs)]

            logger.debug(
                f"Starting {'multiprocessing' if use_multiprocessing else 'threading'} tasks with {workers} workers")

            # Choose between threading and multiprocessing
            if use_multiprocessing:
                if enforce_timeout:
                    raise ValueError("enforce_timeout=True is not supported with use_multiprocessing=True")
                with Pool(workers) as pool:
                    results = pool.map(_timeit_worker, worker_args)
            else:
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    futures = [executor.submit(_timeit_worker, args) for args in worker_args]

                    results = []

                    if enforce_timeout and timeout:
                        for i, future in enumerate(futures):
                            try:
                                result = future.result(timeout=timeout)
                                results.append(result)
                            except TimeoutError:
                                logger.warning(
                                    f"Function execution {i} exceeded timeout of {timeout}s and was canceled.")
                                future.cancel()
                                results.append((timeout, None, True))
                            except Exception as e:
                                logger.error(f"Function execution {i} failed with: {e}")
                                results.append((None, None, None))
                    else:
                        for i, future in enumerate(futures):
                            try:
                                results.append(future.result())
                            except Exception as e:
                                logger.error(f"Function execution {i} failed with: {e}")
                                results.append((None, None, None))

            # Extract timing and result data
            times = [r[0] for r in results if r and r[0] is not None]
            valid_results = [r[1] for r in results if r and r[1] is not None]
            timed_out = [r[2] for r in results if r and r[2] is not None]

            if not times:
                logger.error(f"{func.__name__}: All function executions failed or returned None.")
                return None if not detailed else []

            # Compute statistics
            avg_time = mean(times)
            med_time = median(times)
            min_time = min(times)
            max_time = max(times)
            std_dev = stdev(times) if len(times) > 1 else 0
            total_time = sum(times)

            if detailed:
                stats_data = [
                    ["Function", func],
                    ["Args", args[1:]],
                    ["Kwargs", kwargs],
                    ["Runs", runs],
                    ["Workers", workers],
                    ["Average Time", f"{avg_time}s"],
                    ["Median Time", f"{med_time}s"],
                    ["Min Time", f"{min_time}s"],
                    ["Max Time", f"{max_time}s"],
                    ["Std Deviation", f"{std_dev}s"],
                    ["Total Time", f"{total_time}s"],
                    ["Timed Out", any(timed_out)],
                ]
                output = tabulate(stats_data, tablefmt="plain")
            else:
                output = f"{func.__name__}: Avg: {avg_time:.3f}s, Med: {med_time:.3f}s"

            logger.log(log_level, output)

            # Return the first successful result
            for result in valid_results:
                if result is not None:
                    return result

            return None  # Fallback if all runs failed

        return sync_wrapper

    return decorator
