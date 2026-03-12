# Changelog

All notable changes to this project will be documented in this file.

## [2.2.2] - 2026-03-12

### Changed

- **Auto-scaling time units in all output**: Timing values are now displayed in the most readable unit instead of always using seconds.
  - `< 1ms` → microseconds (e.g. `18.83µs`)
  - `>= 1ms` and `< 1s` → milliseconds (e.g. `12.34ms`)
  - `>= 1s` → seconds (e.g. `2.045s`)

  This applies everywhere a duration is formatted: the single-run `Exec:` line, the multi-run `Avg:`/`Med:` summary line, and every time field in the `detailed=True` table.

- **Fully qualified function name in `detailed=True` output**: The `Function` row now shows `module.qualname` (e.g. `mymodule.MyClass.my_method`) instead of the raw `repr()` of the function object (e.g. `<function my_method at 0x...>`).

### Bug Fixes

- **`Args` no longer empty in `detailed=True` output for regular functions**: `args[1:]` was unconditionally stripping the first argument, which was intended to hide `self` for instance methods but silently dropped the first real argument for regular functions. The slice is now only applied when the first element is a bound instance (`hasattr(args[0], func.__name__)`), so both cases are handled correctly.

### Tests

- Added tests for `_fmt_duration` covering µs/ms/s ranges and exact boundary values (1ms, 1s).
- Added tests for `_func_qualname` covering regular functions, `__main__` module, nested class methods, and missing `__module__` attribute.
- Added integration tests via `caplog` verifying that log output uses scaled units (no scientific notation) and shows qualname instead of function repr.
- Added regression tests for `Args` display: args shown correctly for single-run and multi-run regular functions, and `self` correctly stripped for instance methods.

---

## [2.2.1] - 2026-03-12

### Bug Fixes

- **`@timeit_sync(use_multiprocessing=True)` decorator syntax no longer raises `PicklingError`**: When the `@decorator` syntax is used, the module-level name is replaced by the wrapper. Previously, `multiprocessing.Pool` would fail to pickle the original function because pickle looked it up by name and found the wrapper instead. Worker args for module-level functions are now serialized as `(module_name, qualname)` and resolved by name inside the worker process, where the wrapper's non-`MainProcess` short-circuit correctly calls through to the original function. Nested/local functions are unaffected and behave as before.
- **`_NO_RESULT` sentinel now survives multiprocessing round-trips**: The internal sentinel used to distinguish failed runs from legitimate `None` returns was a bare `object()` instance, which became a different object after pickle/unpickle. It is now a singleton class with a `__reduce__` method, ensuring `is` identity checks remain valid after deserialization in worker processes.
- **`timeout=0` no longer silently ignored**: Falsy checks (`if not timeout`) were replaced with explicit `if timeout is None` checks. Previously, passing `timeout=0` or `timeout=0.0` was treated as "no timeout".
- **Logger level no longer mutated globally**: `logger.setLevel(log_level)` was removed from decorator construction. All decorators share the `"timeit.decorator"` logger by name — calling `setLevel` at decoration time caused the last-decorated function's level to silently override all others. Level filtering is now left to the application's logging configuration.
- **Async error path now correctly uses `_NO_RESULT` sentinel**: Exceptions in `_run_raw` and the timeout-handling path in `run_once` now return `_NO_RESULT` instead of `None`, preventing legitimate `None` return values from being incorrectly filtered out.
- **Async single-run path guards against `None` duration**: A `None` duration (returned when the function errors) no longer causes a crash in `_single_run_output`.

### Changed

- **`timeit_async` no longer accepts `use_multiprocessing`**: The parameter was previously accepted but silently ignored. It has been removed. Async concurrency is always managed via `asyncio.Semaphore`. Passing `use_multiprocessing` to the deprecated `@timeit` wrapper on an async function will now raise `TypeError` at decoration time.
- **Minimum Python version is now 3.9**.

### Internal

- **Extracted `_shared.py` module**: Eliminated code duplication between `sync_wrapper.py` and `async_wrapper.py` by moving shared helpers (`_NO_RESULT`, `_single_run_output`, `_multi_run_output`, `_first_valid_result`) to a common module.
- **Reduced cognitive complexity across all functions** to comply with SonarQube S3776 (threshold: 15). Key refactors:
  - All nested closures extracted to module-level functions (`_run_raw`, `_make_run_once`, `_limited_run`, `_async_execute`, `_async_decorator`, `_run_single_and_log`, `_build_worker_args`, `_execute_parallel_runs`, `_sync_decorator`).
  - `_make_run_once` uses a sync factory pattern to avoid passing `timeout` as a parameter on an async function (SonarQube S7483).
  - `_async_execute` extracted from `_async_decorator` to eliminate nesting complexity penalty.

### Tests

- Added 24 new tests (38 → 62 total), bringing new-code coverage to 95%:
  - `detailed=True` output for single and multi-run (sync and async)
  - Deprecated `@timeit` auto-dispatch for both sync and async functions
  - Parameter validation: `runs=0`, `workers=0`, `log_level=None`
  - Async error handling in single-run and timeout-enabled paths
  - Async timeout paths where the task completes before the timeout fires (both enforced and non-enforced)
  - All-runs-fail scenarios via exception-raising functions (sync and async)
  - `use_multiprocessing=True + enforce_timeout=True` raises `ValueError`
  - Sync timeout exceeded warning in multi-run (non-enforced)
  - Single-run `enforce_timeout=True` warning (sync)
  - Non-main-thread short-circuit behavior (sync and async)
  - `_NO_RESULT` sentinel: `__repr__` and pickle round-trip

### Documentation

- Added deprecation notice for `@timeit` to README.
- Fixed incorrect description of `asyncio.shield()` usage (it is only used in the `enforce_timeout=True` path, not `enforce_timeout=False`).
- Removed `use_multiprocessing` from the async parameters list in README.
- Added missing `Timed Out` row to the `detailed=True` output example.
- Updated Python version requirement from 3.7+ to 3.9+ in README and `pyproject.toml`.

---

## [2.1.0] - 2025-07-14

### Added
- **Async support**: Introduced `@timeit_async` for timing `async def` functions.
- **Per-task timeout enforcement** via `enforce_timeout=True` for both sync and async.
- **Support for static, class, and instance methods**, with multiprocessing compatibility.
- **Graceful timeout with `asyncio.shield()`** for non-enforced async timeouts.
- **Detailed logging** output using `tabulate`, replacing all `print()` usage.
- Pytest-based test suite for all sync/async variants, timeout handling, and method types.

### Changed
- `@timeit` is now **deprecated** and issues a `DeprecationWarning`. It automatically redirects to the correct decorator based on function type.
- Logging configuration is initialized only if no handlers are configured (`logging.basicConfig(...)`).
- Multiprocessing mode now explicitly rejects `enforce_timeout=True` with a `ValueError`.

### Tests
- Added over 40 Pytest tests covering:
  - Async/sync behavior
  - Timeout enforcement and fallback
  - CPU-bound, I/O-bound, and error cases
  - Generator functions
  - Class, static, and instance method support

### Internal
- Refactored into separate modules:
  - `timeit_sync.py`
  - `timeit_async.py`
  - `timeit.py` (deprecated redirector)
- Modular structure ready for packaging and long-term maintenance.

---

## [2.0.8] - 2025-06-25

Initial public release.
