import inspect
import logging
from typing import Callable, Optional

from ._shared import _func_qualname
from .async_wrapper import timeit_async
from .sync_wrapper import timeit_sync


def timeit(
        runs: int = 1,
        workers: int = 1,
        log_level: Optional[int] = logging.INFO,
        use_multiprocessing: bool = False,
        detailed: bool = False,
        timeout: Optional[float] = None,
        enforce_timeout: bool = False
):
    """
    Auto-detecting decorator that times both sync and async functions.

    Inspects the decorated function at decoration time and forwards to
    :func:`timeit_sync` for regular functions or :func:`timeit_async` for
    coroutines. All parameters are passed through unchanged, except that
    ``use_multiprocessing=True`` is silently ignored for async functions
    (async concurrency is always managed via ``asyncio.Semaphore``).

    :param runs: Number of times to run the function (minimum 1).
    :type runs: int
    :param workers: Number of concurrent workers (minimum 1, max equals ``runs``).
    :type workers: int
    :param log_level: Logging level for timing output (e.g. ``logging.INFO``).
    :type log_level: Optional[int]
    :param use_multiprocessing: Use ``multiprocessing.Pool`` instead of threads.
                                Ignored for async functions.
    :type use_multiprocessing: bool
    :param detailed: Log a full stats table (avg, median, min, max, stddev, total)
                     instead of the default one-liner.
    :type detailed: bool
    :param timeout: Per-run timeout in seconds. ``None`` means no timeout.
    :type timeout: Optional[float]
    :param enforce_timeout: Cancel the run when the timeout is reached.
                            Has no effect in single sync runs (no parallelism available).
                            Incompatible with ``use_multiprocessing=True``.
    :type enforce_timeout: bool
    :return: The return value of the decorated function's first successful execution.
    :rtype: Any
    :raises ValueError: If ``runs`` or ``workers`` are less than 1, or if
                        ``enforce_timeout=True`` is combined with ``use_multiprocessing=True``.

    **Example**::

        @timeit(runs=5, workers=2)
        def fetch_data(url: str) -> dict:
            ...

        @timeit(runs=3, workers=3, detailed=True)
        async def call_api(endpoint: str) -> dict:
            ...
    """

    def decorator(func: Callable):
        if inspect.iscoroutinefunction(func):
            if use_multiprocessing:
                logging.getLogger("timeit.decorator").warning(
                    f"{_func_qualname(func)}: use_multiprocessing=True is not supported for async functions and will be ignored."
                )
            return timeit_async(
                runs=runs,
                workers=workers,
                log_level=log_level,
                detailed=detailed,
                timeout=timeout,
                enforce_timeout=enforce_timeout
            )(func)
        return timeit_sync(
            runs=runs,
            workers=workers,
            log_level=log_level,
            detailed=detailed,
            timeout=timeout,
            enforce_timeout=enforce_timeout,
            use_multiprocessing=use_multiprocessing
        )(func)

    return decorator
