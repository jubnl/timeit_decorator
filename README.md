# Timeit Decorator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

`timeit_decorator` is a Python package providing a versatile decorator for timing the execution of functions. It
supports executing functions multiple times, in parallel, and can use either threading or multiprocessing depending on
the nature of the task.

## Efficient Execution for Single Run/Worker

The decorator is optimized for scenarios where both runs and workers are set to 1. In such cases, it bypasses the
overhead of setting up a pool and directly executes the function, which is more efficient for single-run executions.

## Flexible Logging

The `timeit_decorator` can either log timing information using Python's logging framework or print it directly to the
console. This behavior is controlled by the `log_level` parameter:

- If a log level is specified (e.g., `logging.INFO`), the timing information will be logged at that level.
- If `log_level` is set to `None`, the timing information will be printed directly to the console.

By default, the `log_level` parameter is set to `logging.INFO`.

## Installation

To install `timeit_decorator`, run the following command:

```bash
pip install timeit-decorator
```

## Usage

### Basic Usage

Here's how to use the timeit decorator:

```py
import logging
from timeit_decorator import timeit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


@timeit(runs=5, workers=2, log_level=logging.INFO)
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
from timeit_decorator import timeit

# Configure logging
logging.basicConfig(level=logging.INFO)


# Default parameters
# @timeit(runs=1, workers=1, log_level=logging.INFO, use_multiprocessing=False)
@timeit()
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
from timeit_decorator import timeit

# Configure logging
logging.basicConfig(level=logging.DEBUG)


@timeit(runs=10, workers=4, use_multiprocessing=True, log_level=logging.DEBUG)
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
from timeit_decorator import timeit

# Configure logging
logging.basicConfig(level=logging.INFO)


@timeit(runs=5, workers=2)
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
@timeit(runs=5, workers=2, detailed=True)
def sample_function(a, b, c="some value"):
    # Function implementation
    pass


sample_function("arg1", "arg2", key="value")
```

This will output a detailed tabulated summary after the function execution, similar to the following:

```
Function       sample_function
Args           ('arg1', 'arg2')
Kwargs         {'key': 'value'}
Runs           5
Workers        2
Average Time   0.2s
Median Time    0.19s
Min Time       0.18s
Max Time       0.22s
Std Deviation  0.015s
Total Time     1.0s
```

##### Use Cases

- **Performance Analysis**: Use the `detailed` parameter to get a comprehensive overview of the function's performance
  across multiple runs.
- **Debugging**: The detailed statistics can help identify inconsistencies or anomalies in function execution, aiding in
  debugging efforts.

Remember that enabling detailed output can increase the verbosity of the output, especially for functions executed
multiple times. It is recommended to use this feature judiciously based on the specific needs of performance analysis or
debugging.

### Timeout Handling

The timeit decorator includes a timeout mechanism to monitor execution time without stopping the function. If the
execution time exceeds the specified timeout, the decorator logs a warning but allows the function to complete.

#### Usage Example

```python
import logging
from timeit_decorator import timeit

# Configure logging
logging.basicConfig(level=logging.INFO)


@timeit(timeout=0.1, log_level=logging.WARNING)
def slow_function():
    import time
    time.sleep(0.2)  # Simulate a slow function


slow_function()
```

#### Behavior

- If the function executes within the timeout, it completes normally.
- If the function exceeds the timeout, a warning is logged:

```log
WARNING: Timeout exceeded (took 0.205s, timeout was 0.1s), but execution continued.
```

The function result is still returned even if the timeout is exceeded.

## Features

- **Multiple Runs and Workers**: Execute the function multiple times in parallel for more accurate timing.
- **Flexible Logging**: Choose between logging framework or direct print to console for output.
- **Optimized for Single Execution**: Efficient for single run/worker scenarios.
- **Supports Multiprocessing and Threading**: Suitable for both CPU-bound and I/O-bound tasks.

## Limitations

While the `timeit` decorator is designed to be versatile and useful in a wide range of scenarios, there are certain
limitations that users should be aware of:

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

**Recommended Workaround**:To avoid this issue, consider using instance methods or regular functions, which are not
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
