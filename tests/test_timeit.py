import asyncio
import logging
import time

import pytest

from timeit_decorator import timeit_sync, timeit_async

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
