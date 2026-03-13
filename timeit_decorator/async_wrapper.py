import asyncio
import logging
import multiprocessing
import threading
import time
from functools import wraps
from typing import Optional, Callable

from ._shared import _NO_RESULT, _single_run_output, _multi_run_output, _first_valid_result


async def _run_raw(func, args, kwargs, logger):
    """Execute a coroutine once without timeout handling."""
    try:
        start_time = time.time()
        result = await func(*args, **kwargs)
        return time.time() - start_time, result, False
    except Exception as e:
        logger.error(f"Error during async execution: {e}")
        return None, _NO_RESULT, False


def _make_run_once(func, timeout, enforce_timeout, logger):
    """Create an async callable for a single timed execution (no timeout parameter on the async fn)."""

    async def run_once(args, kwargs):
        if timeout is None:
            return await _run_raw(func, args, kwargs, logger)
        try:
            task = asyncio.create_task(func(*args, **kwargs))
            start_time = time.time()
            if enforce_timeout:
                result = await asyncio.wait_for(asyncio.shield(task), timeout=timeout)
                return time.time() - start_time, result, False
            done, _ = await asyncio.wait({task}, timeout=timeout)
            if task in done:
                return time.time() - start_time, task.result(), False
            logger.warning(f"{func.__name__} exceeded timeout of {timeout}s but continued running.")
            return time.time() - start_time, await task, True
        except asyncio.TimeoutError:
            logger.warning(f"{func.__name__} exceeded enforced timeout of {timeout}s and was canceled.")
            task.cancel()
            return time.time() - start_time, _NO_RESULT, True
        except Exception as e:
            logger.error(f"Error during async execution: {e}")
            return None, _NO_RESULT, False

    return run_once


async def _limited_run(sem, run_once_fn, args, kwargs):
    """Execute run_once_fn with semaphore-bounded concurrency."""
    async with sem:
        return await run_once_fn(args, kwargs)


async def _async_execute(func, runs, workers, log_level, detailed, run_once, logger, args, kwargs):
    """Core execution logic for the async wrapper."""
    if threading.current_thread() is not threading.main_thread() or \
            multiprocessing.current_process().name != 'MainProcess':
        return await func(*args, **kwargs)

    if runs == 1 and workers == 1:
        duration, result, _ = await run_once(args, kwargs)
        if duration is not None:
            logger.log(log_level, _single_run_output(func, args, kwargs, duration, detailed))
        return None if result is _NO_RESULT else result

    sem = asyncio.Semaphore(workers)
    results = await asyncio.gather(*[_limited_run(sem, run_once, args, kwargs) for _ in range(runs)])
    times = [r[0] for r in results if r and r[0] is not None]
    valid_results = [r[1] for r in results if r and r[1] is not _NO_RESULT]

    if not times:
        logger.error(f"{func.__name__}: All async function executions failed or returned None.")
        return None if not detailed else []

    logger.log(log_level, _multi_run_output(func, args, kwargs, runs, workers, times, results, detailed))
    return _first_valid_result(valid_results)


def _async_decorator(func, runs, workers, log_level, detailed, timeout, enforce_timeout):
    """Build the async wrapper for a given function and timing configuration."""
    logger = logging.getLogger("timeit.decorator")

    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    run_once = _make_run_once(func, timeout, enforce_timeout, logger)

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        return await _async_execute(func, runs, workers, log_level, detailed, run_once, logger, args, kwargs)

    return async_wrapper


def timeit_async(
    func: Optional[Callable] = None,
    runs: int = 1,
    workers: int = 1,
    log_level: Optional[int] = logging.INFO,
    detailed: bool = False,
    timeout: Optional[float] = None,
    enforce_timeout: bool = False
):
    """
        Time the execution of an async function with options for multiple runs and workers.

        This decorator uses asyncio.Semaphore to bound concurrency. It measures and logs
        the execution time, reporting the average and median times.

        :param runs: Number of times to run the function (minimum 1).
        :type runs: int
        :param workers: Number of concurrent workers (minimum 1, max equals 'runs').
        :type workers: int
        :param log_level: Logging level for timing information (e.g., logging.INFO).
        :type log_level: Optional[int]
        :param detailed: get a detailed output with different stats about the execution time.
        :type detailed: bool
        :param timeout: An optional timeout in seconds for each function execution.
        :type timeout: Optional[float]
        :param enforce_timeout: Enforce timeout. False by default. If True and the timeout is reached, it will cancel the
                                execution.
        :type enforce_timeout: bool
        :return: The return value of the function from its first execution.
        :rtype: Any
        :raises ValueError: If 'runs' or 'workers' are set to less than 1.

        **Example**::

            @timeit_async(runs=5, workers=2)
            async def io_bound_function(n):
                # Function implementation
        """

    if runs < 1 or workers < 1:
        raise ValueError("Both runs and workers must be at least 1")

    workers = min(workers, runs)

    if log_level is None:
        log_level = logging.INFO

    def decorator(func: Callable):
        return _async_decorator(func, runs, workers, log_level, detailed, timeout, enforce_timeout)

    if func is not None:
        return decorator(func)

    return decorator
