import logging
import random
import time

from timeit_decorator import timeit


class TimeItTestClass:

    @timeit(detailed=True, log_level=None)
    def timeit_detailed(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit(log_level=None)
    def timeit_simple(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit(detailed=True, log_level=logging.INFO)
    def timeit_detailed_logged(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit(log_level=logging.INFO)
    def timeit_simple_logged(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit(log_level=None, use_multiprocessing=True, runs=5, workers=5)
    def timeit_multiprocessing(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit(log_level=None, runs=5, workers=5)
    def timeit_multithreading(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit(log_level=None, use_multiprocessing=True, runs=5, workers=5, detailed=True)
    def timeit_multiprocessing_detailed(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit(log_level=None, runs=5, workers=5, detailed=True)
    def timeit_multithreading_detailed(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit(log_level=logging.INFO, timeout=0.1, detailed=True, runs=5)
    def timeit_timeout(self):
        time.sleep(0.5)

    @timeit(log_level=logging.INFO, runs=5, workers=5)
    def test_function(self, a: int, b: int = 2):
        print(f"Executing test_function with args: {a}, {b}")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    testClass = TimeItTestClass()
    testClass.timeit_detailed(1)
    testClass.timeit_simple(2, b=4)
    testClass.timeit_detailed_logged(1, 3)
    testClass.timeit_simple_logged(2, b=3)
    testClass.timeit_multiprocessing(1, b=3)
    testClass.timeit_multithreading(1)
    testClass.timeit_multiprocessing_detailed(1, 2)
    testClass.timeit_multithreading_detailed(1)
    testClass.test_function(1)
    testClass.timeit_timeout()
