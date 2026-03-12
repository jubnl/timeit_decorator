from statistics import mean, median, stdev

from tabulate import tabulate


def _fmt_duration(seconds: float) -> str:
    if seconds < 1e-3:
        return f"{seconds * 1e6:.2f}µs"
    if seconds < 1.0:
        return f"{seconds * 1e3:.2f}ms"
    return f"{seconds:.3f}s"


def _func_qualname(func) -> str:
    module = getattr(func, "__module__", None)
    qualname = getattr(func, "__qualname__", func.__name__)
    if not module:
        return qualname
    return f"{module}.{qualname}"


class _NoResultType:
    """Sentinel singleton that survives pickle round-trips (needed for multiprocessing)."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "_NO_RESULT"

    def __reduce__(self):
        # On unpickle, call _NoResultType() which returns the existing singleton.
        return (_NoResultType, ())


# Sentinel to distinguish a run that failed/was cancelled from a run that returned None.
_NO_RESULT = _NoResultType()


def _display_args(func, args):
    """Return args suitable for display, stripping self/cls for bound method calls."""
    if args and hasattr(args[0], func.__name__):
        return args[1:]
    return args


def _single_run_output(func, args, kwargs, duration, detailed):
    """Build log output for a single execution."""
    if not detailed:
        return f"{func.__name__}: Exec: {_fmt_duration(duration)}"
    return tabulate([
        ["Function", _func_qualname(func)],
        ["Args", _display_args(func, args)],
        ["Kwargs", kwargs],
        ["Duration", _fmt_duration(duration)],
    ], tablefmt="plain")


def _multi_run_output(func, args, kwargs, runs, workers, times, results, detailed):
    """Build log output for multi-run executions."""
    avg_time = mean(times)
    med_time = median(times)
    if not detailed:
        return f"{func.__name__}: Avg: {_fmt_duration(avg_time)}, Med: {_fmt_duration(med_time)}"
    stats_data = [
        ["Function", _func_qualname(func)],
        ["Args", _display_args(func, args)],
        ["Kwargs", kwargs],
        ["Runs", runs],
        ["Workers", workers],
        ["Average Time", _fmt_duration(avg_time)],
        ["Median Time", _fmt_duration(med_time)],
        ["Min Time", _fmt_duration(min(times))],
        ["Max Time", _fmt_duration(max(times))],
        ["Std Deviation", _fmt_duration(stdev(times)) if len(times) > 1 else "0.00µs"],
        ["Total Time", _fmt_duration(sum(times))],
        ["Timed Out", any(r[2] for r in results if r)],
    ]
    return tabulate(stats_data, tablefmt="plain")


def _first_valid_result(valid_results):
    """Return the first result from successful runs, or None if there are none."""
    return valid_results[0] if valid_results else None
