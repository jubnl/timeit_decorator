import asyncio
import logging
import pickle
import threading
import time

import pytest

from timeit_decorator import timeit_sync, timeit_async
from timeit_decorator._shared import _NO_RESULT, _fmt_duration, _func_qualname

pytestmark = pytest.mark.asyncio
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def cpu_bound_function(n):
    # Simulating a CPU-bound task
    for _ in range(1000000):
        n += 1
    return n


def cpu_intensive_task():
    # Simulating a CPU-intensive task
    total = 0
    for i in range(1000000):
        total += i
    return total


def task_with_multiprocessing(n):
    time.sleep(0.1)
    return "multi"


def task_with_threading(n):
    time.sleep(0.1)
    return "thread"


@timeit_sync(runs=3, workers=3)
def multiple_workers_multiple_runs(n: float):
    time.sleep(n)
    return n


@timeit_sync(runs=3)
def single_worker_multiple_runs(n: float):
    time.sleep(n)
    return n


@timeit_sync(workers=3)
def multiple_workers_single_run(n: float):
    time.sleep(n)
    return n


@timeit_sync()
def single_worker_single_run(n: float):
    time.sleep(n)
    return n


@timeit_sync(runs=2, workers=2)
def io_bound_function(n):
    # Simulating an I/O-bound task
    time.sleep(n)
    return n


def sample_function(a, b):
    time.sleep(0.1)
    return a + b


class SampleClass:
    @staticmethod
    @timeit_sync(use_multiprocessing=False, runs=2, workers=2)
    def sample_static_method(a, b):
        time.sleep(0.1)
        return a + b

    @classmethod
    @timeit_sync(use_multiprocessing=True, runs=2, workers=2)
    def sample_class_method(cls, a, b):
        time.sleep(0.1)
        return a + b

    @timeit_sync(use_multiprocessing=True, runs=2, workers=2)
    def sample_instance_method(self, a, b):
        time.sleep(0.1)
        return a + b


def slow_cpu_task():
    time.sleep(0.2)  # Exceeds timeout
    return "should timeout"


@timeit_sync(runs=2, workers=2, use_multiprocessing=True)
def _mp_decorated_func():
    return "ok"


def test_multiple_workers_multiple_runs():
    result = multiple_workers_multiple_runs(0.1)
    assert result == 0.1


def test_single_worker_multiple_runs():
    result = single_worker_multiple_runs(0.1)
    assert result == 0.1


def test_multiple_workers_single_run():
    result = multiple_workers_single_run(0.1)
    assert result == 0.1


def test_single_worker_single_run():
    result = single_worker_single_run(0.1)
    assert result == 0.1


def test_timing_accuracy():
    start_time = time.time()
    single_worker_single_run(0.1)
    end_time = time.time()
    measured_time = end_time - start_time
    assert abs(measured_time - 0.1) <= 0.05


def test_concurrency_effectiveness():
    single_start_time = time.time()
    single_worker_multiple_runs(0.1)
    single_end_time = time.time()

    multi_start_time = time.time()
    multiple_workers_multiple_runs(0.1)
    multi_end_time = time.time()

    assert (multi_end_time - multi_start_time) < (single_end_time - single_start_time)


def test_error_handling():
    @timeit_sync()
    def error_function():
        raise ValueError("Intentional Error")

    with pytest.raises(ValueError):
        error_function()


def test_return_values_consistency():
    results = [multiple_workers_multiple_runs(0.1) for _ in range(5)]
    assert all(result == 0.1 for result in results)


def test_function_with_different_argument_types():
    @timeit_sync()
    def test_func(arg):
        return arg

    assert test_func("string") == "string"
    assert test_func(123) == 123
    assert test_func([1, 2, 3]) == [1, 2, 3]


def test_function_with_keyword_arguments():
    @timeit_sync()
    def test_func(a, b=0):
        return a + b

    assert test_func(10, b=20) == 30


def test_decorator_stacking():
    def another_decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    @timeit_sync()
    @another_decorator
    def test_func():
        return "decorated"

    assert test_func() == "decorated"


def test_function_with_no_return():
    @timeit_sync()
    def test_func():
        pass

    assert test_func() is None


def test_zero_time_execution():
    @timeit_sync(runs=5)
    def quick_func():
        pass

    assert quick_func() is None


def test_function_with_multiple_return_values():
    @timeit_sync(runs=3)
    def varying_return_func(call_count=[0]):
        call_count[0] += 1
        return call_count[0]

    assert varying_return_func() in [1, 2, 3]


def test_large_number_of_workers():
    @timeit_sync(runs=2, workers=10)
    def imbalanced_workers_func():
        time.sleep(0.1)
        return "done"

    assert imbalanced_workers_func() == "done"


def test_decorator_with_generator_function():
    @timeit_sync()
    def generator_func():
        yield from range(3)

    gen = generator_func()
    assert next(gen) == 0
    assert next(gen) == 1
    assert next(gen) == 2


def test_cpu_bound_function_multiprocessing():
    decorated_func = timeit_sync(runs=2, workers=2, use_multiprocessing=True)(cpu_bound_function)
    result = decorated_func(0)
    assert result == 0 + 1000000


def test_io_bound_function_threading():
    result = io_bound_function(0.1)
    assert result == 0.1


def test_multiprocessing_with_high_cpu_load():
    decorated_func = timeit_sync(runs=4, workers=4, use_multiprocessing=True)(cpu_intensive_task)
    result = decorated_func()
    assert result is not None


def test_threading_with_high_io_load():
    @timeit_sync(runs=4, workers=4)
    def io_intensive_task():
        time.sleep(0.1)
        return "completed"

    result = io_intensive_task()
    assert result == "completed"


def test_switching_multiprocessing_mode():
    decorated_func_multiprocessing = timeit_sync(runs=2, workers=2, use_multiprocessing=True)(task_with_multiprocessing)
    decorated_func_threading = timeit_sync(runs=2, workers=2)(task_with_threading)

    assert decorated_func_multiprocessing(0) == "multi"
    assert decorated_func_threading(0) == "thread"


def test_regular_function():
    # Test the decorator on a regular function
    decorated_func = timeit_sync(runs=2, workers=1)(sample_function)
    assert decorated_func(1, 2) == 3


def test_static_method():
    # Test the decorator on a static method
    assert SampleClass.sample_static_method(1, 2) == 3


def test_class_method():
    # Test the decorator on a class method
    assert SampleClass.sample_class_method(1, 2) == 3


def test_instance_method():
    # Test the decorator on an instance method
    instance = SampleClass()
    assert instance.sample_instance_method(1, 2) == 3


def test_single_run():
    # Test the decorator with a single run
    decorated_func = timeit_sync(runs=1, workers=1)(sample_function)
    assert decorated_func(1, 2) == 3


def test_multiple_runs():
    # Test the decorator with multiple runs
    decorated_func = timeit_sync(runs=3, workers=1)(sample_function)
    assert decorated_func(1, 2) == 3


def test_multiprocessing():
    # Test the decorator with multiprocessing
    decorated_func = timeit_sync(use_multiprocessing=True, runs=2, workers=2)(sample_function)
    assert decorated_func(1, 2) == 3


def test_timeout_exceeded():
    @timeit_sync(timeout=0.1)
    def slow_function():
        time.sleep(0.2)
        return "completed"

    result = slow_function()
    assert result == "completed"


def test_timeout_not_exceeded():
    @timeit_sync(timeout=0.3)
    def fast_function():
        time.sleep(0.1)  # Within timeout
        return "completed"

    result = fast_function()
    assert result == "completed"  # Should complete successfully


def test_timeout_with_multiple_runs():
    @timeit_sync(runs=3, timeout=0.15)
    def sometimes_slow(i):
        time.sleep(0.1 if i % 2 == 0 else 0.2)  # Some executions exceed timeout
        return i

    results = sometimes_slow(1)
    assert results == 1


def test_timeout_with_multiprocessing():
    decorated_func = timeit_sync(runs=2, workers=2, timeout=0.1, use_multiprocessing=True)(slow_cpu_task)
    result = decorated_func()
    assert result == "should timeout"


def test_enforce_timeout_cancel():
    @timeit_sync(runs=2, workers=2, timeout=0.1, enforce_timeout=True)
    def slow_func():
        time.sleep(0.2)
        return "too slow"

    result = slow_func()
    # Only one result will be returned (first valid)
    assert result is None or result == "too slow"  # Depends on which call returns in time


def test_enforce_timeout_not_triggered():
    @timeit_sync(runs=2, workers=2, timeout=0.3, enforce_timeout=True)
    def fast_func():
        time.sleep(0.1)
        return "ok"

    result = fast_func()
    assert result == "ok"


@pytest.mark.asyncio
async def test_async_basic():
    @timeit_async()
    async def fast_async():
        await asyncio.sleep(0.1)
        return "done"

    result = await fast_async()
    assert result == "done"


@pytest.mark.asyncio
async def test_async_enforce_timeout_disabled():
    @timeit_async(timeout=0.05, enforce_timeout=False)
    async def slow_async():
        await asyncio.sleep(0.1)
        return "finished"

    result = await slow_async()
    assert result == "finished"  # Shielded, allowed to complete


@pytest.mark.asyncio
async def test_async_enforce_timeout_enabled():
    @timeit_async(timeout=0.05, enforce_timeout=True)
    async def slow_async():
        await asyncio.sleep(0.1)
        return "finished"

    result = await slow_async()
    assert result is None  # Enforced timeout canceled execution


@pytest.mark.asyncio
async def test_async_multiple_runs():
    @timeit_async(runs=3, workers=2)
    async def async_func():
        await asyncio.sleep(0.1)
        return "done"

    result = await async_func()
    assert result == "done"


# --- detailed=True output paths ---

def test_detailed_single_run():
    @timeit_sync(detailed=True)
    def my_func(a, b):
        return a + b

    assert my_func(1, 2) == 3


def test_detailed_multiple_runs():
    @timeit_sync(runs=3, workers=2, detailed=True)
    def my_func():
        time.sleep(0.01)
        return "done"

    assert my_func() == "done"


@pytest.mark.asyncio
async def test_async_detailed_multiple_runs():
    @timeit_async(runs=3, workers=2, detailed=True)
    async def my_func():
        await asyncio.sleep(0.01)
        return "done"

    assert await my_func() == "done"


# --- deprecated @timeit dispatcher ---

def test_timeit_deprecated_sync():
    from timeit_decorator import timeit

    with pytest.warns(DeprecationWarning):
        @timeit()
        def my_func():
            return "sync"

    assert my_func() == "sync"


@pytest.mark.asyncio
async def test_timeit_deprecated_async():
    from timeit_decorator import timeit

    with pytest.warns(DeprecationWarning):
        @timeit()
        async def my_func():
            return "async"

    assert await my_func() == "async"


# --- parameter validation ---

def test_timeit_sync_invalid_runs():
    with pytest.raises(ValueError):
        timeit_sync(runs=0)(lambda: None)


def test_timeit_sync_invalid_workers():
    with pytest.raises(ValueError):
        timeit_sync(workers=0)(lambda: None)


def test_timeit_sync_log_level_none():
    @timeit_sync(log_level=None)
    def my_func():
        return "done"

    assert my_func() == "done"


def test_timeit_async_invalid_runs():
    with pytest.raises(ValueError):
        timeit_async(runs=0)(lambda: None)


def test_timeit_async_log_level_none():
    @timeit_async(log_level=None)
    async def my_func():
        return "done"

    # just ensure decoration succeeds (validation only)
    assert my_func is not None


# --- async error handling ---

@pytest.mark.asyncio
async def test_async_error_handling_single_run():
    @timeit_async()
    async def failing_func():
        raise ValueError("async error")

    result = await failing_func()
    assert result is None


@pytest.mark.asyncio
async def test_async_error_handling_with_timeout():
    @timeit_async(timeout=1.0, enforce_timeout=True)
    async def failing_func():
        raise ValueError("async error with timeout")

    result = await failing_func()
    assert result is None


# --- async timeout: task completes before timeout fires ---

@pytest.mark.asyncio
async def test_async_task_completes_before_timeout_non_enforced():
    @timeit_async(timeout=1.0, enforce_timeout=False)
    async def quick_func():
        await asyncio.sleep(0.01)
        return "done"

    assert await quick_func() == "done"


@pytest.mark.asyncio
async def test_async_task_completes_before_timeout_enforced():
    @timeit_async(timeout=1.0, enforce_timeout=True)
    async def quick_func():
        await asyncio.sleep(0.01)
        return "done"

    assert await quick_func() == "done"


# --- async: all runs fail (exception path, duration=None) ---

@pytest.mark.asyncio
async def test_async_all_runs_fail():
    @timeit_async(runs=3, workers=2)
    async def always_fails():
        raise RuntimeError("always fails")

    assert await always_fails() is None


@pytest.mark.asyncio
async def test_async_all_runs_fail_detailed():
    @timeit_async(runs=3, workers=2, detailed=True)
    async def always_fails():
        raise RuntimeError("always fails")

    assert await always_fails() == []


# --- sync: timeout exceeded warning in multi-run (non-enforced) ---

def test_sync_timeout_exceeded_multi_run():
    @timeit_sync(runs=2, timeout=0.05)
    def slow_func():
        time.sleep(0.1)
        return "done"

    assert slow_func() == "done"


# --- sync: all runs fail (exception path, duration=None) ---

def test_sync_all_runs_fail():
    @timeit_sync(runs=3, workers=3)
    def always_fails():
        raise RuntimeError("always fails")

    assert always_fails() is None


# --- multiprocessing + enforce_timeout raises ValueError ---

def test_multiprocessing_decorator_syntax():
    """@timeit_sync(use_multiprocessing=True) must not raise PicklingError."""
    assert _mp_decorated_func() == "ok"


def test_sync_enforce_timeout_with_multiprocessing_raises():
    with pytest.raises(ValueError, match="enforce_timeout"):
        @timeit_sync(runs=2, workers=2, use_multiprocessing=True, enforce_timeout=True)
        def my_func():
            return "done"

        my_func()


# --- sync: enforce_timeout=True on single run emits warning ---

def test_sync_enforce_timeout_single_run_warning():
    @timeit_sync(timeout=1.0, enforce_timeout=True)
    def quick_func():
        return "done"

    assert quick_func() == "done"


# --- _NO_RESULT sentinel: repr and pickle round-trip ---

def test_no_result_repr():
    assert repr(_NO_RESULT) == "_NO_RESULT"


def test_no_result_pickle_roundtrip():
    unpickled = pickle.loads(pickle.dumps(_NO_RESULT))
    assert unpickled is _NO_RESULT


# --- non-main-thread short-circuit paths ---

def test_sync_non_main_thread_short_circuits():
    """Decorated sync function called from a non-main thread should bypass timing."""
    results = []

    @timeit_sync(runs=3)
    def my_func():
        return "done"

    def run():
        results.append(my_func())

    t = threading.Thread(target=run)
    t.start()
    t.join()
    assert results[0] == "done"


def test_async_non_main_thread_short_circuits():
    """Decorated async function called from a non-main thread should bypass timing."""
    results = []

    @timeit_async(runs=3)
    async def my_func():
        return "done"

    def run():
        loop = asyncio.new_event_loop()
        results.append(loop.run_until_complete(my_func()))
        loop.close()

    t = threading.Thread(target=run)
    t.start()
    t.join()
    assert results[0] == "done"


# --- _fmt_duration unit scaling ---

def test_fmt_duration_microseconds():
    assert _fmt_duration(0.0000188) == "18.80µs"


def test_fmt_duration_milliseconds():
    assert _fmt_duration(0.01234) == "12.34ms"


def test_fmt_duration_seconds():
    assert _fmt_duration(2.045) == "2.045s"


def test_fmt_duration_boundary_1ms():
    assert _fmt_duration(0.001) == "1.00ms"


def test_fmt_duration_boundary_1s():
    assert _fmt_duration(1.0) == "1.000s"


# --- _func_qualname ---

def test_func_qualname_regular_function():
    def my_function():
        pass
    my_function.__module__ = "mymodule"
    my_function.__qualname__ = "my_function"
    assert _func_qualname(my_function) == "mymodule.my_function"


def test_func_qualname_main_module_included():
    def my_function():
        pass
    my_function.__module__ = "__main__"
    my_function.__qualname__ = "my_function"
    assert _func_qualname(my_function) == "__main__.my_function"


def test_func_qualname_nested_class():
    def my_method():
        pass
    my_method.__module__ = "mymodule"
    my_method.__qualname__ = "MyClass.my_method"
    assert _func_qualname(my_method) == "mymodule.MyClass.my_method"


def test_func_qualname_no_module():
    def my_function():
        pass
    del my_function.__module__
    my_function.__qualname__ = "my_function"
    assert _func_qualname(my_function) == "my_function"


# --- output format integration checks ---

def test_single_run_output_uses_scaled_units(caplog):
    import logging
    with caplog.at_level(logging.INFO, logger="timeit.decorator"):
        @timeit_sync()
        def quick():
            pass
        quick()
    assert "Exec:" in caplog.text
    # Should not contain raw scientific notation seconds like 1.8e-05s
    assert "e-" not in caplog.text


def test_multi_run_output_uses_scaled_units(caplog):
    import logging
    with caplog.at_level(logging.INFO, logger="timeit.decorator"):
        @timeit_sync(runs=3)
        def quick():
            pass
        quick()
    assert "Avg:" in caplog.text
    assert "Med:" in caplog.text
    assert "e-" not in caplog.text


def test_detailed_single_run_qualname(caplog):
    import logging
    with caplog.at_level(logging.INFO, logger="timeit.decorator"):
        @timeit_sync(detailed=True)
        def my_named_func():
            pass
        my_named_func()
    assert "my_named_func" in caplog.text
    assert "<function" not in caplog.text


def test_detailed_multi_run_qualname(caplog):
    import logging
    with caplog.at_level(logging.INFO, logger="timeit.decorator"):
        @timeit_sync(runs=3, detailed=True)
        def my_named_func():
            pass
        my_named_func()
    assert "my_named_func" in caplog.text
    assert "<function" not in caplog.text


def test_detailed_args_shown_for_regular_function(caplog):
    import logging
    with caplog.at_level(logging.INFO, logger="timeit.decorator"):
        @timeit_sync(detailed=True)
        def my_func(a, b):
            return a + b
        my_func(1, 2)
    assert "(1, 2)" in caplog.text


def test_detailed_args_shown_for_multi_run(caplog):
    import logging
    with caplog.at_level(logging.INFO, logger="timeit.decorator"):
        @timeit_sync(runs=3, detailed=True)
        def my_func(a, b):
            return a + b
        my_func(3, 4)
    assert "(3, 4)" in caplog.text


def test_detailed_args_strips_self_for_instance_method(caplog):
    import logging

    class MyClass:
        @timeit_sync(detailed=True)
        def my_method(self, x):
            return x

    with caplog.at_level(logging.INFO, logger="timeit.decorator"):
        MyClass().my_method(99)
    assert "99" in caplog.text
    assert "MyClass" not in caplog.text.split("Args")[1].split("\n")[0]
