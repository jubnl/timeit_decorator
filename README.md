# Timeit Decorator
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
## Overview
`timeit_decorator` is a Python package providing a versatile decorator for timing the execution of functions. It supports executing functions multiple times, in parallel, and can use either threading or multiprocessing depending on the nature of the task.

## Efficient Execution for Single Run/Worker
The decorator is optimized for scenarios where both runs and workers are set to 1. In such cases, it bypasses the overhead of setting up a pool and directly executes the function, which is more efficient for single-run executions.

## Logging Instead of Printing
The `timeit_decorator` outputs timing information exclusively through Python's logging framework, rather than printing directly to the console. This approach offers more flexibility and control, allowing users to customize the output format, level, and destination. It integrates seamlessly with your application's logging configuration.

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
logging.basicConfig(level=logging.INFO)

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

io_bound_function()
```

## Features
- Multiple Runs: Execute the function multiple times for more accurate timing.
- Concurrency: Run tasks in parallel using either threading or multiprocessing.
- Flexible: Suitable for both CPU-bound and I/O-bound tasks.
- Customizable: Control the number of runs and workers, and choose between threading and multiprocessing.

## Requirements
`timeit_decorator` requires Python 3.x.

## Contributing
Contributions to `timeit_decorator` are welcome! Please read our [contributing guidelines](./CONTRIBUTING.md) for more details.

## License
`timeit_decorator` is released under the [MIT License](./LICENSE).
