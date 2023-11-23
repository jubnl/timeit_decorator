# Timeit Decorator
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
## Overview
`timeit_decorator` is a Python package providing a versatile decorator for timing the execution of functions. It supports executing functions multiple times, in parallel, and can use either threading or multiprocessing depending on the nature of the task.

## Logging Instead of Printing
The `timeit_decorator` outputs timing information exclusively through Python's logging framework, rather than printing directly to the console. This approach offers more flexibility and control, allowing users to customize the output format, level, and destination. It integrates seamlessly with your application's logging configuration.

## Installation
To install `timeit_decorator`, run the following command:

```bash
pip install timeit-decorator
```

## Usage
### Basic Usage
Here's a simple example of how to use the timeit decorator, including how it integrates with Python's logging system:

```py
import logging
from timeit_decorator import timeit

# Configure logging
logging.basicConfig(level=logging.INFO)
# Default parameters :
# - runs: int = 1,
# - workers: int = 1,
# - log_level: int = logging.INFO,
# - use_multiprocessing: bool = False
@timeit()
def sample_function():
    # Function implementation
```
In this example, the timeit decorator will log the execution time of sample_function using Python's logging framework.

### Using Multiprocessing
For CPU-bound tasks, you can enable multiprocessing:

```py
import logging
from timeit_decorator import timeit

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@timeit(runs=10, workers=4, log_level=logging.DEBUG, use_multiprocessing=True)
def cpu_intensive_function():
    # CPU-bound function implementation
```

### Using Threading (Default)
For I/O-bound tasks, the default threading is more efficient:

```py
import logging
from timeit_decorator import timeit

# Configure logging
logging.basicConfig(level=logging.INFO)

@timeit(runs=5, workers=2, log_level=logging.INFO)
def io_bound_function():
    # I/O-bound function implementation
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
`timeit_decorator` is released under the MIT License.
