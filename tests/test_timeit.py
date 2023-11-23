import unittest
import time
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


class TestTimeitDecorator(unittest.TestCase):

    @timeit(runs=3, workers=3)
    def multiple_workers_multiple_runs(self, n: float):
        time.sleep(n)
        return n

    @timeit(runs=3)
    def single_worker_multiple_runs(self, n: float):
        time.sleep(n)
        return n

    @timeit(workers=3)
    def multiple_workers_single_run(self, n: float):
        time.sleep(n)
        return n

    @timeit()
    def single_worker_single_run(self, n: float):
        time.sleep(n)
        return n

    @timeit(runs=2, workers=2)
    def io_bound_function(self, n):
        # Simulating an I/O-bound task
        time.sleep(n)
        return n

    def test_multiple_workers_multiple_runs(self):
        """Test function with multiple workers and multiple runs."""
        result = self.multiple_workers_multiple_runs(0.1)
        self.assertEqual(result, 0.1)

    def test_single_worker_multiple_runs(self):
        """Test function with a single worker and multiple runs."""
        result = self.single_worker_multiple_runs(0.1)
        self.assertEqual(result, 0.1)

    def test_multiple_workers_single_run(self):
        """Test function with multiple workers and a single run."""
        result = self.multiple_workers_single_run(0.1)
        self.assertEqual(result, 0.1)

    def test_single_worker_single_run(self):
        """Test function with a single worker and a single run."""
        result = self.single_worker_single_run(0.1)
        self.assertEqual(result, 0.1)

    def test_timing_accuracy(self):
        """Test the accuracy of timing measurements."""
        start_time = time.time()
        self.single_worker_single_run(0.1)
        end_time = time.time()
        measured_time = end_time - start_time
        self.assertAlmostEqual(measured_time, 0.1, delta=0.05)

    def test_concurrency_effectiveness(self):
        """Test that multiple workers actually reduce total execution time."""
        single_start_time = time.time()
        self.single_worker_multiple_runs(0.1)
        single_end_time = time.time()

        multi_start_time = time.time()
        self.multiple_workers_multiple_runs(0.1)
        multi_end_time = time.time()

        # Expect the multi-threaded run to be faster than the single-threaded run
        self.assertLess(multi_end_time - multi_start_time, single_end_time - single_start_time)

    def test_error_handling(self):
        """Test that the decorator handles function errors gracefully."""

        @timeit()
        def error_function():
            raise ValueError("Intentional Error")

        with self.assertRaises(ValueError):
            error_function()

    def test_return_values_consistency(self):
        """Test that all runs of the function return consistent values."""
        results = [self.multiple_workers_multiple_runs(0.1) for _ in range(5)]
        self.assertTrue(all(result == 0.1 for result in results))

    def test_function_with_different_argument_types(self):
        @timeit()
        def test_func(arg):
            return arg

        self.assertEqual(test_func("string"), "string")
        self.assertEqual(test_func(123), 123)
        self.assertEqual(test_func([1, 2, 3]), [1, 2, 3])

    def test_function_with_keyword_arguments(self):
        @timeit()
        def test_func(a, b=0):
            return a + b

        self.assertEqual(test_func(10, b=20), 30)

    def test_decorator_stacking(self):
        def another_decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        @timeit()
        @another_decorator
        def test_func():
            return "decorated"

        self.assertEqual(test_func(), "decorated")

    def test_function_with_no_return(self):
        @timeit()
        def test_func():
            pass

        self.assertIsNone(test_func())

    def test_zero_time_execution(self):
        """Test the decorator with a function that has near-zero execution time."""

        @timeit(runs=5)
        def quick_func():
            pass  # Function does nothing

        self.assertIsNone(quick_func())

    def test_function_with_multiple_return_values(self):
        """Test a function that returns different values on each call."""

        @timeit(runs=3)
        def varying_return_func(call_count=[0]):
            call_count[0] += 1
            return call_count[0]

        self.assertIn(varying_return_func(), [1, 2, 3])

    def test_large_number_of_workers(self):
        """Test the decorator with a larger number of workers than runs."""

        @timeit(runs=2, workers=10)
        def imbalanced_workers_func():
            time.sleep(0.1)
            return "done"

        self.assertEqual(imbalanced_workers_func(), "done")

    def test_decorator_with_generator_function(self):
        """Test the decorator with a generator function."""

        @timeit()
        def generator_func():
            yield from range(3)

        gen = generator_func()
        self.assertEqual(next(gen), 0)
        self.assertEqual(next(gen), 1)
        self.assertEqual(next(gen), 2)

    def test_cpu_bound_function_multiprocessing(self):
        """Test CPU-bound function with multiprocessing enabled."""
        decorated_func = timeit(runs=2, workers=2, use_multiprocessing=True)(cpu_bound_function)
        result = decorated_func(0)
        self.assertEqual(result, 0 + 1000000)

    def test_io_bound_function_threading(self):
        """Test I/O-bound function with threading (multiprocessing disabled)."""
        result = self.io_bound_function(0.1)
        self.assertEqual(result, 0.1)

    def test_multiprocessing_with_high_cpu_load(self):
        """Test that multiprocessing handles high CPU load effectively."""

        decorated_func = timeit(runs=4, workers=4, use_multiprocessing=True)(cpu_intensive_task)
        result = decorated_func()
        self.assertIsNotNone(result)

    def test_threading_with_high_io_load(self):
        """Test that threading is effective for I/O bound tasks."""

        @timeit(runs=4, workers=4)
        def io_intensive_task():
            # Simulating an I/O-intensive task
            time.sleep(0.1)
            return "completed"

        result = io_intensive_task()
        self.assertEqual(result, "completed")

    def test_switching_multiprocessing_mode(self):
        """Test switching between multiprocessing and threading modes."""

        decorated_func_multiprocessing = timeit(runs=2, workers=2, use_multiprocessing=True)(task_with_multiprocessing)
        decorated_func_threading = timeit(runs=2, workers=2)(task_with_threading)

        self.assertEqual(decorated_func_multiprocessing(0), "multi")
        self.assertEqual(decorated_func_threading(0), "thread")


if __name__ == '__main__':
    unittest.main()
