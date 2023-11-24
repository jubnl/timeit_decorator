import multiprocessing
import threading
import time
import logging
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from statistics import mean, median, stdev
from typing import Optional, Callable
from tabulate import tabulate


def _multiprocessing_instance_method_call(instance, method_name, *args, **kwargs):
    method = getattr(instance, method_name)
    return method(*args, **kwargs)


def _timeit_worker(args):
    try:
        start_time = time.time()
        if isinstance(args[0], tuple) and hasattr(args[0][0], args[0][1]):
            # Instance method call
            instance, method_name, *method_args = args[0]
            func_result = _multiprocessing_instance_method_call(instance, method_name, *method_args)
        else:
            # Regular function call
            func, args, kwargs = args
            func_result = func(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time, func_result
    except Exception as e:
        print(f"Error in _timeit_worker: {e}")
        return None


def timeit(
        runs: int = 1,
        workers: int = 1,
        log_level: Optional[int] = logging.INFO,
        use_multiprocessing: bool = False,
        detailed: bool = False
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
    :param log_level: Logging level for timing information (e.g., logging.INFO). If None, will print directly in the console.
    :type log_level: Optional[int]
    :param use_multiprocessing: Use multiprocessing if True, otherwise use threading.
                                Suitable for CPU-bound tasks when True.
    :type use_multiprocessing: bool
    :param detailed: get a detailed output with different stats about the execution time.
    :type detailed: bool
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

    def decorator(func: Callable):
        decorator_logger = logging.getLogger("timeit.decorator")
        decorator_logger.debug(f"Decorating function: {func.__name__}")
        method_name = func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            wrapper_logger = logging.getLogger("timeit.decorator.wrapper")
            wrapper_logger.debug(f"Calling function: {func.__name__}")

            # Check if the current thread is the main thread
            if threading.current_thread() is not threading.main_thread():
                # This is a worker thread, execute the function directly
                return func(*args, **kwargs)

            # Check if the current process is the main process
            if multiprocessing.current_process().name != 'MainProcess':
                # This is a child process, execute the function directly
                return func(*args, **kwargs)

            if runs < 1 or workers < 1:
                raise ValueError("Both runs and workers must be at least 1")

            if (runs == 1 and workers == 1) or (runs == 1 and workers > runs):
                # Directly execute the function if only a single run with one worker
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                execution_time = end_time - start_time

                stats_data = [
                    ["Function", func],
                    ["Args", args[1:]],
                    ["Kwargs", kwargs],
                    ["Runs", runs],
                    ["Workers", workers],
                    ["Execution Time", f"{execution_time}s"],
                    ["", ""],
                ]

                if detailed:
                    output = tabulate(stats_data, tablefmt="plain")
                else:
                    output = f"{func}: Exec: {execution_time}s"

                if log_level is not None:
                    logger = logging.getLogger()
                    logger.setLevel(log_level)
                    logger.log(log_level, output)
                else:
                    print(output)
                return result

            is_instance_method = hasattr(args[0], method_name) if args else False
            if is_instance_method:
                worker_args = [((args[0], method_name) + args[1:], {},) for _ in range(runs)]
            else:
                worker_args = [(func, args, kwargs) for _ in range(runs)]

            if use_multiprocessing:
                wrapper_logger.debug("Starting multiprocessing tasks")
                with Pool(workers) as pool:
                    results = pool.map(_timeit_worker, worker_args)
                wrapper_logger.debug("Completed multiprocessing tasks")
            else:
                wrapper_logger.debug("Starting threading tasks")
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    results = list(executor.map(_timeit_worker, worker_args))
                wrapper_logger.debug("Completed threading tasks")

            times = [result[0] for result in results if result is not None]
            if not times:
                raise RuntimeError("No valid results were returned from the timed function.")

            avg_time = mean(times)
            med_time = median(times)
            min_time = min(times)
            max_time = max(times)
            std_dev = stdev(times) if len(times) > 1 else 0
            total_time = sum(times)

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
                ["", ""],
            ]

            if detailed:
                output = tabulate(stats_data, tablefmt="plain")
            else:
                output = f"{func}: Avg: {avg_time:.3f}s, Med: {med_time:.3f}s"

            if log_level is not None:
                logger = logging.getLogger()
                logger.setLevel(log_level)
                logger.log(log_level, output)
            else:
                print(output)

            # Return the result of the first execution
            return results[0][1] if results else None

        return wrapper

    return decorator
