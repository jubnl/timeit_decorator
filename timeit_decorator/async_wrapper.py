import asyncio
import logging
import multiprocessing
import threading
import time
from functools import wraps
from statistics import mean, median, stdev
from typing import Optional, Callable

from tabulate import tabulate


def timeit_async(
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
        async def async_wrapper(*args, **kwargs):
            if threading.current_thread() is not threading.main_thread():
                return await func(*args, **kwargs)
            if multiprocessing.current_process().name != 'MainProcess':
                return await func(*args, **kwargs)

            async def run_once():
                try:
                    start_time = time.time()
                    coro = func(*args, **kwargs)

                    if timeout:
                        task = asyncio.create_task(coro)

                        if not enforce_timeout:
                            # Wait for the task with timeout, but don’t cancel on timeout
                            done, pending = await asyncio.wait({task}, timeout=timeout)
                            if task in done:
                                result = await task
                                duration = time.time() - start_time
                                return duration, result, False
                            else:
                                logger.warning(f"{func.__name__} exceeded timeout of {timeout}s but continued running.")
                                result = await task  # allow it to finish
                                duration = time.time() - start_time
                                return duration, result, True
                        else:
                            try:
                                result = await asyncio.wait_for(task, timeout=timeout)
                                duration = time.time() - start_time
                                return duration, result, False
                            except asyncio.TimeoutError:
                                logger.warning(
                                    f"{func.__name__} exceeded enforced timeout of {timeout}s and was canceled.")
                                duration = time.time() - start_time
                                return duration, None, True
                    else:
                        result = await coro
                        duration = time.time() - start_time
                        return duration, result, False

                except Exception as e:
                    logger.error(f"Error during async execution: {e}")
                    return None, None, False

            if runs == 1 and workers == 1:
                duration, result, _ = await run_once()
                if detailed:
                    output = tabulate([
                        ["Function", func],
                        ["Args", args[1:] if args else []],
                        ["Kwargs", kwargs],
                        ["Duration", f"{duration}s"]
                    ], tablefmt="plain")
                else:
                    output = f"{func.__name__}: Exec: {duration:.6f}s"
                logger.log(log_level, output)
                return result

            sem = asyncio.Semaphore(workers)

            async def limited_run():
                async with sem:
                    return await run_once()

            tasks = [limited_run() for _ in range(runs)]
            results = await asyncio.gather(*tasks)

            times = [r[0] for r in results if r and r[0] is not None]
            valid_results = [r[1] for r in results if r and r[1] is not None]
            timed_out = [r[2] for r in results if r and r[2] is not None]

            if not times:
                logger.error(f"{func.__name__}: All async function executions failed or returned None.")
                return None if not detailed else []

            avg_time = mean(times)
            med_time = median(times)
            min_time = min(times)
            max_time = max(times)
            std_dev = stdev(times) if len(times) > 1 else 0
            total_time = sum(times)

            if detailed:
                stats_data = [
                    ["Function", func],
                    ["Args", args[1:] if args else []],
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
                output = f"{func}: Avg: {avg_time:.3f}s, Med: {med_time:.3f}s"

            logger.log(log_level, output)

            for result in valid_results:
                if result is not None:
                    return result

            return None

        return async_wrapper

    return decorator
