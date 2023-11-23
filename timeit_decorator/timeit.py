import time
import logging
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import Pool
from statistics import mean, median


# Top-level function for multiprocessing
def _timeit_worker(args):
    func, args, kwargs = args
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return end_time - start_time, result


def timeit(runs: int = 1, workers: int = 1, log_level: int = logging.INFO, use_multiprocessing: bool = False):
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
    :type log_level: Union[int, str]
    :param use_multiprocessing: Use multiprocessing if True, otherwise use threading.
                                Suitable for CPU-bound tasks when True.
    :type use_multiprocessing: bool
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

        @timeit(runs=5, workers=2, log_level=logging.INFO)
        def io_bound_function(n):
            # Function implementation
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if runs < 1 or workers < 1:
                raise ValueError("Both runs and workers must be at least 1")

            worker_args = [(func, args, kwargs) for _ in range(runs)]

            if use_multiprocessing:
                pool = Pool(workers)
                results = pool.map(_timeit_worker, worker_args)
                pool.close()
                pool.join()
            else:
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    results = list(executor.map(_timeit_worker, worker_args))

            times = [result[0] for result in results]
            avg_time = mean(times)
            med_time = median(times)

            logger = logging.getLogger()
            logger.setLevel(log_level)
            logger.log(log_level, f"Function {func.__name__} executed {runs} times with {workers} workers.")
            logger.log(log_level, f"Average Time: {avg_time} seconds")
            logger.log(log_level, f"Median Time: {med_time} seconds")

            return results[0][1] if results else None

        return wrapper

    return decorator
