# Timeit Decorator
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
## Overview
timeit_decorator is a Python package providing a versatile decorator for timing the execution of functions. It supports 
executing functions multiple times, in parallel, and can use either threading or multiprocessing depending on the nature
of the task.

## Installation
To install timeit_decorator, run the following command:

```bash
pip install timeit_decorator
```

## Usage
### Basic Usage
Here's a simple example of how to use the timeit decorator:

```py
from timeit_decorator import timeit

@timeit(runs=5, workers=2)
def sample_function():
    # Function implementation
```

### Using Multiprocessing
For CPU-bound tasks, you can enable multiprocessing:

```py
from timeit_decorator import timeit

@timeit(runs=10, workers=4, use_multiprocessing=True)
def cpu_intensive_function():
    # CPU-bound function implementation
```

### Using Threading (Default)
For I/O-bound tasks, the default threading is more efficient:

```py
from timeit_decorator import timeit

@timeit(runs=5, workers=2)
def io_bound_function():
    # I/O-bound function implementation
```

## Features
- Multiple Runs: Execute the function multiple times for more accurate timing.
- Concurrency: Run tasks in parallel using either threading or multiprocessing.
- Flexible: Suitable for both CPU-bound and I/O-bound tasks.
- Customizable: Control the number of runs and workers, and choose between threading and multiprocessing.

## Requirements
timeit_decorator requires Python 3.x.

## Contributing
Contributions to timeit_decorator are welcome! Please read our [contributing guidelines](./CONTRIBUTING.md) for more details.

## License
timeit_decorator is released under the MIT License.
