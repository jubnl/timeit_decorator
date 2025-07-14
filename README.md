# Timeit Decorator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Downloads](https://static.pepy.tech/badge/timeit-decorator)](https://pepy.tech/projects/timeit-decorator)
[![PyPI Downloads](https://static.pepy.tech/badge/timeit-decorator/month)](https://pepy.tech/projects/timeit-decorator)
[![PyPI version](https://badge.fury.io/py/timeit-decorator.svg)](https://pypi.org/project/timeit-decorator/)
[![Python versions](https://img.shields.io/pypi/pyversions/timeit-decorator.svg)](https://pypi.org/project/timeit-decorator/)
[![Build](https://img.shields.io/github/actions/workflow/status/jubnl/timeit_decorator/.github%2Fworkflows%2Fpython-publish.yml)](https://github.com/jubnl/timeit_decorator/actions/workflows/python-publish.yml)
[![codecov](https://codecov.io/gh/jubnl/timeit_decorator/graph/badge.svg?token=7KGVJM29YP)](https://codecov.io/gh/jubnl/timeit_decorator)
[![GitHub Issues](https://img.shields.io/github/issues/jubnl/timeit_decorator)](https://github.com/jubnl/timeit_decorator/issues)
![GitHub Repo stars](https://img.shields.io/github/stars/jubnl/timeit_decorator)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Flexible Logging](#flexible-logging)
- [Installation](#installation)
- [Usage](#usage)
  - [Basic Usage](#basic-usage)
  - [Efficient Execution for Single Run/Worker](#efficient-execution-for-single-runworker)
  - [Using Multiprocessing](#using-multiprocessing)
  - [Using Threading (Default)](#using-threading-default)
  - [Detailed Output Option](#detailed-output-option)
  - [Timeout Handling](#timeout-handling)
  - [Async Support](#async-support)
- [Limitations](#limitations)
  - [Incompatibility with Static Methods and Multiprocessing](#incompatibility-with-static-methods-and-multiprocessing)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [License](#license)
- [Changelog](#changelog)


## Overview

`timeit_decorator` is a flexible Python library for benchmarking function execution. It supports repeated runs, parallel
execution with threads or processes, detailed timing statistics, and native support for both sync and async functions.

## Features

- **Multiple Runs and Workers**: Run functions multiple times with configurable concurrency.
- **Sync and Async Support**: Use @timeit_sync or @timeit_async for full feature parity across sync and async code.
- **Per-Task Timeout Handling**: Enforce or log timeouts individually for each execution.
- **Multiprocessing and Threading**: Choose concurrency model for CPU- or I/O-bound workloads.
- **Detailed Statistics**: Enable detailed=True to log timing metrics like average, median, min/max, stddev.
- **Instance, Class, and Static Method Support**: Fully supports method decorators (with limitations for
  multiprocessing).
- **Structured Logging Only**: All output is logged using Python’s logging module.

##### Use Cases

- **Performance Analysis**: Use the `detailed` parameter to get a comprehensive overview of the function's performance
  across multiple runs.
- **Debugging**: The detailed statistics can help identify inconsistencies or anomalies in function execution, aiding in
  debugging efforts.

Remember that enabling detailed output can increase the verbosity of the output, especially for functions executed
multiple times. It is recommended to use this feature judiciously based on the specific needs of performance analysis or
debugging.

## Flexible Logging

All output is handled exclusively through Python’s `logging` module. The `timeit_decorator` automatically configures a
default logger if none exists. You can customize verbosity using the `log_level` parameter (default: `logging.INFO`).

## Installation

To install `timeit_decorator`, run the following command:

```bash
pip install timeit-decorator
```

## Usage

#### Example Available

You can find a runnable example in [examples/main.py](examples/main.py).\
The corresponding output is written to [examples/example_output.log](examples/example_output.log).

### Basic Usage

Here's how to use the timeit decorator:

```py
import logging
from timeit_decorator import timeit_sync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


@timeit_sync(runs=5, workers=2, log_level=logging.INFO)
def sample_function():
    # Function implementation
    pass


# Call the decorated function
sample_function()
```

### Efficient Execution for Single Run/Worker

For single executions, the decorator directly runs the function:

```py
import logging
from timeit_decorator import timeit_sync

# Configure logging
logging.basicConfig(level=logging.INFO)


# Default parameters
# @timeit_sync(
#       runs=1,
#       workers=1,
#       log_level=logging.INFO,
#       use_multiprocessing=False,
#       detailed=False,
#       timeout=None,
#       enforce_timeout=False
# )
@timeit_sync()
def quick_function():
    # Function implementation for a quick task
    pass


# Call the decorated function
quick_function()
```

### Using Multiprocessing

For CPU-bound tasks, you can enable multiprocessing:

```py
import logging
from timeit_decorator import timeit_sync

# Configure logging
logging.basicConfig(level=logging.DEBUG)


@timeit_sync(runs=10, workers=4, use_multiprocessing=True, log_level=logging.DEBUG)
def cpu_intensive_function():
    # CPU-bound function implementation
    pass


# Call the decorated function
cpu_intensive_function()
```

### Using Threading (Default)

For I/O-bound tasks, the default threading is more efficient:

```py
import logging
from timeit_decorator import timeit_sync

# Configure logging
logging.basicConfig(level=logging.INFO)


@timeit_sync(runs=5, workers=2)
def io_bound_function():
    # I/O-bound function implementation
    pass


# Call the decorated function
io_bound_function()
```

### Detailed Output Option

The `timeit` decorator includes an optional detailed parameter that provides more extensive statistics about the
function
execution time when set to True. This feature is particularly useful for in-depth performance analysis and debugging, as
it gives users a broader view of how the function behaves under different conditions.

#### Usage of the `detailed` Parameter

**Purpose**: When set to True, the timeit decorator provides a detailed tabulated output including average, median,
minimum,
and maximum execution times, standard deviation, and total execution time for all runs.

##### Example

```py
@timeit_sync(runs=5, workers=2, detailed=True)
def sample_function(a, b, c="some value"):
    # Function implementation
    pass


sample_function("arg1", "arg2", c="value overwrite")
```

This will output a detailed tabulated summary after the function execution, similar to the following:

```
Function       <function sample_function at 0x000002612FFD9E40>
Args           ('arg1', 'arg2')
Kwargs         {'c': 'value overwrite'}
Runs           5
Workers        2
Average Time   0.2s
Median Time    0.19s
Min Time       0.18s
Max Time       0.22s
Std Deviation  0.015s
Total Time     1.0s
```

### Timeout Handling

You can specify a `timeout` (in seconds) to monitor execution duration for each run. The `enforce_timeout` parameter
controls how timeouts are handled:

- `enforce_timeout=False` (default): Logs a warning if a run exceeds the timeout but allows it to complete.
- `enforce_timeout=True`: Cancels the execution if the timeout is reached (only supported with threading and async).

#### Example (Non-Enforced Timeout)

```python
import logging
from timeit_decorator import timeit_sync

logging.basicConfig(level=logging.INFO)


@timeit_sync(timeout=0.1)
def slow_function():
    import time
    time.sleep(0.2)


slow_function()
```

Example (Enforced Timeout with Cancellation)

```python
@timeit_sync(timeout=0.1, enforce_timeout=True)
def fast_abort():
    import time
    time.sleep(0.2)


fast_abort()
```

#### Behavior Summary

- If execution completes before timeout -> normal result
- If enforce_timeout=False and timeout is exceeded -> logs warning, allows completion
- If enforce_timeout=True and timeout is exceeded -> run is cancelled and marked as timed out

> Note: Enforced timeout is not supported with use_multiprocessing=True due to Python’s process model.

### Async Support

`timeit_decorator` fully supports asynchronous functions via the `@timeit_async` decorator.

You can configure it with the same options as the sync version, including:

- `runs`, `workers`
- `timeout`, `enforce_timeout`
- `detailed`, `log_level`

Async execution uses an internal `asyncio.Semaphore` to manage concurrency and supports both enforced and non-enforced
timeouts via `asyncio.wait_for()` and `asyncio.shield()`.

```python
import asyncio
from timeit_decorator import timeit_async


@timeit_async(runs=3, workers=2, timeout=0.1, enforce_timeout=False)
async def async_task():
    await asyncio.sleep(0.2)
    return "done"


asyncio.run(async_task())
```

> If `enforce_timeout=False`, timeouts are logged but the coroutine is allowed to finish using `asyncio.shield()`.
> If `enforce_timeout=True`, the task is cancelled if it exceeds the timeout limit.

## Limitations

While `timeit_decorator` is designed to be highly flexible, a few constraints exist due to Python's concurrency model:

### Incompatibility with Static Methods and Multiprocessing

- **Static Methods and Multiprocessing**: The `timeit` decorator currently does not support the use of multiprocessing (
  `use_multiprocessing=True`) with `@staticmethod`. Attempting to use the `timeit` decorator with multiprocessing on
  static
  methods can lead to unexpected behavior or errors, specifically a `PicklingError`.

**Reason for the Limitation**: This issue arises because Python's multiprocessing module requires objects to be
serialized (pickled) for transfer between processes. However, static methods pose a challenge for Python's pickling
mechanism due to the way they are referenced internally. This can result in a `PicklingError` stating that the static
method is not the same object as expected.

**Example of the issue**:

```py
# This will raise a PicklingError when executed
class ExampleClass:
    @staticmethod
    @timeit(use_multiprocessing=True, runs=2)
    def example_static_method():
        # method implementation
        pass
```

Example of exception :

```
_pickle.PicklingError: Can't pickle <function ExampleClass.example_static_method at 0x...>: it's not the same object as __main__.ExampleClass.example_static_method
```

**Recommended Workaround**: To avoid this issue, consider using instance methods or regular functions, which are not
subject to the same serialization constraints as static methods. Alternatively, refrain from using
`use_multiprocessing=True` with static methods.

This limitation stems from inherent characteristics of Python's multiprocessing and pickling mechanisms. Users are
encouraged to structure their code accordingly to prevent encountering this issue. We are continuously working to
enhance the `timeit` decorator and mitigate such limitations wherever possible. If you encounter any other issues or
limitations, please feel free to report them in the project's issue tracker.

## Requirements

`timeit_decorator` requires Python 3.7+

## Contributing

Contributions to `timeit_decorator` are welcome! Please read our [contributing guidelines](./CONTRIBUTING.md) for more
details.

## License

`timeit_decorator` is released under the [MIT License](./LICENSE).

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for a full list of changes, fixes, and new features introduced in each release.
