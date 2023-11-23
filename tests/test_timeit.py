import unittest
import time

import pytest

from timeit_decorator import timeit


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


@timeit(runs=3, workers=3)
def multiple_workers_multiple_runs(n: float):
    time.sleep(n)
    return n


@timeit(runs=3)
def single_worker_multiple_runs(n: float):
    time.sleep(n)
    return n


@timeit(workers=3)
def multiple_workers_single_run(n: float):
    time.sleep(n)
    return n


@timeit()
def single_worker_single_run(n: float):
    time.sleep(n)
    return n


@timeit(runs=2, workers=2)
def io_bound_function(n):
    # Simulating an I/O-bound task
    time.sleep(n)
    return n


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
    @timeit()
    def error_function():
        raise ValueError("Intentional Error")

    with pytest.raises(ValueError):
        error_function()


def test_return_values_consistency():
    results = [multiple_workers_multiple_runs(0.1) for _ in range(5)]
    assert all(result == 0.1 for result in results)


def test_function_with_different_argument_types():
    @timeit()
    def test_func(arg):
        return arg

    assert test_func("string") == "string"
    assert test_func(123) == 123
    assert test_func([1, 2, 3]) == [1, 2, 3]


def test_function_with_keyword_arguments():
    @timeit()
    def test_func(a, b=0):
        return a + b

    assert test_func(10, b=20) == 30


def test_decorator_stacking():
    def another_decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    @timeit()
    @another_decorator
    def test_func():
        return "decorated"

    assert test_func() == "decorated"


def test_function_with_no_return():
    @timeit()
    def test_func():
        pass

    assert test_func() is None


def test_zero_time_execution():
    @timeit(runs=5)
    def quick_func():
        pass

    assert quick_func() is None


def test_function_with_multiple_return_values():
    @timeit(runs=3)
    def varying_return_func(call_count=[0]):
        call_count[0] += 1
        return call_count[0]

    assert varying_return_func() in [1, 2, 3]


def test_large_number_of_workers():
    @timeit(runs=2, workers=10)
    def imbalanced_workers_func():
        time.sleep(0.1)
        return "done"

    assert imbalanced_workers_func() == "done"


def test_decorator_with_generator_function():
    @timeit()
    def generator_func():
        yield from range(3)

    gen = generator_func()
    assert next(gen) == 0
    assert next(gen) == 1
    assert next(gen) == 2


def test_cpu_bound_function_multiprocessing():
    decorated_func = timeit(runs=2, workers=2, use_multiprocessing=True)(cpu_bound_function)
    result = decorated_func(0)
    assert result == 0 + 1000000


def test_io_bound_function_threading():
    result = io_bound_function(0.1)
    assert result == 0.1


def test_multiprocessing_with_high_cpu_load():
    decorated_func = timeit(runs=4, workers=4, use_multiprocessing=True)(cpu_intensive_task)
    result = decorated_func()
    assert result is not None


def test_threading_with_high_io_load():
    @timeit(runs=4, workers=4)
    def io_intensive_task():
        time.sleep(0.1)
        return "completed"

    result = io_intensive_task()
    assert result == "completed"


def test_switching_multiprocessing_mode():
    decorated_func_multiprocessing = timeit(runs=2, workers=2, use_multiprocessing=True)(task_with_multiprocessing)
    decorated_func_threading = timeit(runs=2, workers=2)(task_with_threading)

    assert decorated_func_multiprocessing(0) == "multi"
    assert decorated_func_threading(0) == "thread"


if __name__ == '__main__':
    unittest.main()
