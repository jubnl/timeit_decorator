import inspect
import warnings
from typing import Callable

from .async_wrapper import timeit_async
from .sync_wrapper import timeit_sync


def timeit(**kwargs):
    """
    Deprecated. Use @timeit_sync or @timeit_async instead.
    Automatically forwards based on the function type.
    """

    def decorator(func: Callable):
        warnings.warn(
            "The @timeit decorator is deprecated. Use @timeit_sync or @timeit_async instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if inspect.iscoroutinefunction(func):
            return timeit_async(**kwargs)(func)
        else:
            return timeit_sync(**kwargs)(func)

    return decorator
