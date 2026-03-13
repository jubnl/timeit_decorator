"""
Playground for timeit_decorator — covers a broad range of features and edge cases.
Run with:  uv run python main.py
"""

import asyncio
import logging
import time

from timeit_decorator import timeit

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

SEPARATOR = "-" * 60


def section(title: str) -> None:
    print(f"\n{SEPARATOR}\n  {title}\n{SEPARATOR}")


# ---------------------------------------------------------------------------
# 1. Single run — fast path, no concurrency
# ---------------------------------------------------------------------------

@timeit
def single_run(n: int) -> int:
    time.sleep(0.05)
    return n * 2


# ---------------------------------------------------------------------------
# 2. Multiple runs with threading
# ---------------------------------------------------------------------------

@timeit(runs=6, workers=3)
def threaded_runs(n: int) -> int:
    time.sleep(0.1)
    return n


# ---------------------------------------------------------------------------
# 3. Multiple runs with multiprocessing — @decorator syntax (was PicklingError before v2.2.0)
# ---------------------------------------------------------------------------

@timeit(runs=4, workers=4, use_multiprocessing=True)
def cpu_bound(n: int) -> int:
    total = 0
    for i in range(500_000):
        total += i
    return total + n


# ---------------------------------------------------------------------------
# 4. detailed=True — tabulated stats
# ---------------------------------------------------------------------------

@timeit(runs=5, workers=3, detailed=True)
def detailed_output(n: int) -> int:
    time.sleep(0.05)
    return n


# ---------------------------------------------------------------------------
# 5. Timeout — non-enforced (logs warning, lets function complete)
# ---------------------------------------------------------------------------

@timeit(runs=3, timeout=0.05)
def timeout_not_enforced() -> str:
    time.sleep(0.1)
    return "completed despite timeout"


# ---------------------------------------------------------------------------
# 6. Timeout — enforced (cancels the future)
# ---------------------------------------------------------------------------

@timeit(runs=4, workers=4, timeout=0.05, enforce_timeout=True)
def timeout_enforced() -> str:
    time.sleep(0.2)
    return "should be cancelled"


# ---------------------------------------------------------------------------
# 7. Function returns None legitimately
# ---------------------------------------------------------------------------

@timeit(runs=3)
def returns_none() -> None:
    time.sleep(0.02)


# ---------------------------------------------------------------------------
# 8. Function raises an exception — multi-run (all fail → returns None)
# ---------------------------------------------------------------------------

@timeit(runs=3, workers=3)
def always_raises() -> str:
    raise RuntimeError("intentional error")


# ---------------------------------------------------------------------------
# 9. Instance method — multiprocessing and threading
# ---------------------------------------------------------------------------

class MyService:
    def __init__(self, multiplier: int):
        self.multiplier = multiplier

    @timeit(runs=4, workers=4, use_multiprocessing=True)
    def compute(self, n: int) -> int:
        total = 0
        for i in range(500_000):
            total += i
        return total * self.multiplier + n

    @timeit(runs=4, workers=4)
    def io_task(self, n: int) -> int:
        time.sleep(0.05)
        return n * self.multiplier


# ---------------------------------------------------------------------------
# 10. Async — basic single run
# ---------------------------------------------------------------------------

@timeit
async def async_single() -> str:
    await asyncio.sleep(0.05)
    return "async done"


# ---------------------------------------------------------------------------
# 11. Async — multiple runs with semaphore-bounded concurrency
# ---------------------------------------------------------------------------

@timeit(runs=6, workers=3, detailed=True)
async def async_multi() -> str:
    await asyncio.sleep(0.05)
    return "async multi done"


# ---------------------------------------------------------------------------
# 12. Async timeout — non-enforced (logs warning, awaits completion)
# ---------------------------------------------------------------------------

@timeit(runs=3, timeout=0.05, enforce_timeout=False)
async def async_timeout_soft() -> str:
    await asyncio.sleep(0.1)
    return "finished late"


# ---------------------------------------------------------------------------
# 13. Async timeout — enforced (cancels the coroutine)
# ---------------------------------------------------------------------------

@timeit(runs=4, workers=4, timeout=0.05, enforce_timeout=True)
async def async_timeout_hard() -> str:
    await asyncio.sleep(0.2)
    return "should be cancelled"


# ---------------------------------------------------------------------------
# 14. Async — all runs fail
# ---------------------------------------------------------------------------

@timeit(runs=3, workers=3)
async def async_always_fails() -> str:
    raise ValueError("async intentional error")


# ---------------------------------------------------------------------------
# 15. Single run + enforce_timeout=True (warns that enforce is a no-op here)
# ---------------------------------------------------------------------------

@timeit(timeout=1.0, enforce_timeout=True)
def single_run_enforce_warn() -> str:
    return "fast"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run_async_cases() -> None:
    section("10. Async — single run")
    result = await async_single()
    print(f"  result: {result!r}")

    section("11. Async — multiple runs, detailed=True")
    result = await async_multi()
    print(f"  result: {result!r}")

    section("12. Async timeout — non-enforced (completes late)")
    result = await async_timeout_soft()
    print(f"  result: {result!r}")

    section("13. Async timeout — enforced (all cancelled → None)")
    result = await async_timeout_hard()
    print(f"  result: {result!r}")

    section("14. Async — all runs raise (→ None)")
    result = await async_always_fails()
    print(f"  result: {result!r}")


if __name__ == "__main__":
    section("1. Single run (fast path)")
    print(f"  result: {single_run(21)!r}")

    section("2. Multiple runs — threading (runs=6, workers=3)")
    print(f"  result: {threaded_runs(7)!r}")

    section("3. Multiple runs — multiprocessing @decorator syntax (runs=4, workers=4)")
    print(f"  result: {cpu_bound(0)!r}")

    section("4. detailed=True output (runs=5, workers=3)")
    print(f"  result: {detailed_output(99)!r}")

    section("5. Timeout non-enforced — warns but lets function complete")
    print(f"  result: {timeout_not_enforced()!r}")

    section("6. Timeout enforced — all cancelled (→ None)")
    print(f"  result: {timeout_enforced()!r}")

    section("7. Function returns None legitimately")
    print(f"  result: {returns_none()!r}")

    section("8. All runs raise — returns None")
    print(f"  result: {always_raises()!r}")

    section("9a. Instance method — multiprocessing")
    svc = MyService(multiplier=2)
    print(f"  result: {svc.compute(1)!r}")

    section("9b. Instance method — threading")
    print(f"  result: {svc.io_task(5)!r}")

    section("15. Single run + enforce_timeout=True (no-op warning)")
    print(f"  result: {single_run_enforce_warn()!r}")

    asyncio.run(run_async_cases())
