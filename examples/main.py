import asyncio
import logging
import random
import time

from timeit_decorator import timeit_sync, timeit_async


class TimeItTestClass:

    @timeit_sync(detailed=True)
    def timeit_detailed(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit_sync()
    def timeit_simple(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit_sync(detailed=True, log_level=logging.INFO)
    def timeit_detailed_logged(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit_sync(log_level=logging.INFO)
    def timeit_simple_logged(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit_sync(use_multiprocessing=True, runs=5, workers=5)
    def timeit_multiprocessing(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit_sync(runs=5, workers=5)
    def timeit_multithreading(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit_sync(use_multiprocessing=True, runs=5, workers=5, detailed=True)
    def timeit_multiprocessing_detailed(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit_sync(runs=5, workers=5, detailed=True)
    def timeit_multithreading_detailed(self, a: int, b: int = 2):
        time.sleep(random.randint(a, b))

    @timeit_sync(log_level=logging.INFO, timeout=0.1, detailed=True, runs=5)
    def timeit_timeout(self):
        time.sleep(0.5)

    @timeit_sync(log_level=logging.INFO, timeout=0.1, enforce_timeout=True, runs=5, workers=2, detailed=True)
    def timeit_timeout_enforced(self):
        time.sleep(0.5)

    @timeit_sync(log_level=logging.INFO, runs=5, workers=5)
    def test_function(self, a: int, b: int = 2):
        print(f"Executing test_function with args: {a}, {b}")


@timeit_async(runs=3, workers=2, timeout=0.1, enforce_timeout=False, detailed=True)
async def async_timeout_not_enforced():
    await asyncio.sleep(0.2)
    return "done"


@timeit_async(runs=3, workers=2, timeout=0.1, enforce_timeout=True, detailed=True)
async def async_timeout_enforced():
    await asyncio.sleep(0.2)
    return "done"


if __name__ == '__main__':
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
    testClass.timeit_timeout_enforced()

    asyncio.run(async_timeout_not_enforced())
    asyncio.run(async_timeout_enforced())
