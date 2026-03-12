from statistics import mean, median, stdev

from tabulate import tabulate

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


def _single_run_output(func, args, kwargs, duration, detailed):
    """Build log output for a single execution."""
    if not detailed:
        return f"{func.__name__}: Exec: {duration:.6f}s"
    return tabulate([
        ["Function", func],
        ["Args", args[1:]],
        ["Kwargs", kwargs],
        ["Duration", f"{duration}s"],
    ], tablefmt="plain")


def _multi_run_output(func, args, kwargs, runs, workers, times, results, detailed):
    """Build log output for multi-run executions."""
    avg_time = mean(times)
    med_time = median(times)
    if not detailed:
        return f"{func.__name__}: Avg: {avg_time:.3f}s, Med: {med_time:.3f}s"
    stats_data = [
        ["Function", func],
        ["Args", args[1:]],
        ["Kwargs", kwargs],
        ["Runs", runs],
        ["Workers", workers],
        ["Average Time", f"{avg_time}s"],
        ["Median Time", f"{med_time}s"],
        ["Min Time", f"{min(times)}s"],
        ["Max Time", f"{max(times)}s"],
        ["Std Deviation", f"{stdev(times) if len(times) > 1 else 0}s"],
        ["Total Time", f"{sum(times)}s"],
        ["Timed Out", any(r[2] for r in results if r)],
    ]
    return tabulate(stats_data, tablefmt="plain")


def _first_valid_result(valid_results):
    """Return the first result from successful runs, or None if there are none."""
    return valid_results[0] if valid_results else None
