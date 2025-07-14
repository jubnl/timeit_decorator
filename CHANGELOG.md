# Changelog

All notable changes to this project will be documented in this file.

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
