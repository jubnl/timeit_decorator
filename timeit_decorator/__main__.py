import argparse
import importlib.util
import os
import sys
import logging
import time
from ast import literal_eval
from .timeit import timeit  # Import the decorator


def safe_parse(value):
    """Safely parse a string into a Python literal (int, float, bool, etc.), or leave it as a string."""
    try:
        return literal_eval(value)  # Parses numbers, booleans, lists, dicts, etc.
    except (ValueError, SyntaxError):
        return value  # Return as a string if parsing fails


def run_timed_function(script, func_name, args, kwargs, runs, workers, timeout, use_multiprocessing, detailed):
    # Load the specified script dynamically
    script_path = os.path.abspath(script)
    spec = importlib.util.spec_from_file_location("module.name", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Ensure the function exists
    if not hasattr(module, func_name):
        print(f"Error: Function '{func_name}' not found in '{script}'.")
        sys.exit(1)

    func = getattr(module, func_name)

    # Wrap the function dynamically with the timeit decorator
    timed_func = timeit(
        runs=runs,
        workers=workers,
        timeout=timeout,
        use_multiprocessing=use_multiprocessing,
        detailed=detailed,
        log_level=logging.INFO
    )(func)

    # Call the function with provided arguments
    print(f"Executing '{func_name}' from '{script}' with {runs} runs and {workers} workers...")
    result = timed_func(*args, **kwargs)
    print("Execution completed.")
    return result


def main():
    parser = argparse.ArgumentParser(description="Time the execution of a function from a Python script.")

    parser.add_argument("script", type=str, help="Path to the Python script containing the function.")
    parser.add_argument("function", type=str, help="Function name to execute inside the script.")
    parser.add_argument("--runs", type=int, default=1, help="Number of times to run the function.")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel workers.")
    parser.add_argument("--timeout", type=float, default=None, help="Timeout in seconds for each function execution.")
    parser.add_argument("--multiprocessing", action="store_true", help="Use multiprocessing instead of threading.")
    parser.add_argument("--detailed", action="store_true", help="Show detailed statistics.")
    parser.add_argument("--args", nargs="*", type=str, default=[], help="Positional arguments for the function.")
    parser.add_argument("--kwargs", nargs="*", type=str, default=[],
                        help="Keyword arguments for the function (format: key=value).")

    args = parser.parse_args()

    # Parse keyword arguments safely
    kwargs = {}
    for kwarg in args.kwargs:
        if "=" in kwarg:
            key, value = kwarg.split("=", 1)
            kwargs[key] = safe_parse(value)  # Use safe parsing
        else:
            print(f"Warning: Ignoring malformed keyword argument '{kwarg}'. Expected format: key=value.")

    # Convert positional arguments using safe parsing
    parsed_args = [safe_parse(arg) for arg in args.args]

    # Run the function with the given parameters
    run_timed_function(
        script=args.script,
        func_name=args.function,
        args=parsed_args,
        kwargs=kwargs,
        runs=args.runs,
        workers=args.workers,
        timeout=args.timeout,
        use_multiprocessing=args.multiprocessing,
        detailed=args.detailed,
    )


if __name__ == "__main__":
    main()