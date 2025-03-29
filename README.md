![Preview](./.github/assets/simple.png)

# FlameTracker

![Build Status](https://img.shields.io/github/actions/workflow/status/EtienneMR/flametracker/deploy.yml)
![PyPI Version](https://img.shields.io/pypi/v/flametracker)
![License](https://img.shields.io/github/license/EtienneMR/flametracker)

The `FlameTracker` library provides a way to track and visualize function calls and execution times within Python programs. It includes features like:

- Hierarchical action tracking
- Timing of function calls
- Flamegraph generation for performance visualization
- JSON and string representation of call structures

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
  - [Basic Tracking](#basic-tracking)
  - [Generating a Flamegraph](#generating-a-flamegraph)
  - [Nested Actions](#nested-actions)
  - [Function Wrapping](#function-wrapping)
  - [Tracker Manual Activation](#tracker-manual-activation)
- [Running Tests](#running-tests)
- [License](#license)

## Installation

To use the `FlameTracker` library, install it in your Python environment:

```sh
pip install flametracker
```

## Usage

### Basic Tracking

This example demonstrates how to track a single action using the `Tracker` object.

```python
import flametracker

# Create a tracker and track a single action
with flametracker.Tracker() as tracker:
    for _ in range(10):
        with tracker.action("example_action"):
            # Simulate some computation
            pass

# Print the tracked actions as a string
print(tracker.to_str(
    ignore_args=False # Remove args and results, may be useful in some cases to prevent bloat
))
```

Generated tracking:

```
@root()
│ example_action() 0.00ms
│ example_action() 0.00ms
│ example_action() 0.00ms
│ example_action() 0.00ms
│ example_action() 0.00ms
│ example_action() 0.00ms
│ example_action() 0.00ms
│ example_action() 0.00ms
│ example_action() 0.00ms
│ example_action() 0.00ms
╰─> () 0.01ms {'@root': 1, 'example_action': 10}
```

### Generating a Flamegraph

This example illustrates how to generate a flamegraph from tracked actions and save it as an HTML file.

```python
import flametracker

# Create a tracker and track some actions
with flametracker.Tracker() as tracker:
    with tracker.action("example_action"):
        pass

# Generate a flamegraph and save it to a file
html_output = tracker.to_flamegraph(
    group_min_percent = 0.01, # If use_calls_as_value is False, group short actions together (percentage of total time)
    splited = False, # Split flamegraph by first action
    use_calls_as_value = False # Use number of tracked calls as node value, may be a dict of group value
)
with open("flamegraph.html", "w", encoding="utf-8") as f:
    f.write(html_output)
```

### Nested Actions

This example shows how to track nested actions and set results for specific actions.

```python
import flametracker

# Create a tracker and track nested actions
with flametracker.Tracker() as tracker:
    with tracker.action("parent_action") as parent:
        with tracker.action("child_action") as child:
            # Set a result for the child action
            child.set_result("Hello from child!")

print(tracker.to_str())
```

Generated tracking:

```
@root()
│ parent_action()
│ │ child_action() 0.00ms
│ ╰─> () 0.00ms {'parent_action': 1, 'child_action': 1}
╰─> () 0.01ms {'@root': 1, 'parent_action': 1, 'child_action': 1}
```

### Function Wrapping

This example demonstrates how to use the `@wrap` decorator to automatically track function calls.

```python
import flametracker

# Wrap a function to track its execution
@flametracker.wrap
def my_function(x):
    return x * 2

# Use the tracker to monitor the wrapped function
with flametracker.Tracker() as tracker:
    result = my_function(5)
    print(f"Result: {result}")

print(tracker.to_str())
```

Generated tracking:

```
@root()
│ my_function(5) 0.00ms
╰─> () 0.01ms {'@root': 1, 'my_function': 1}
```

### Tracker Manual Activation

This example demonstrates how to manually activate and deactivate the tracker, and how to check its active state.

```python
import flametracker

# Create a tracker
tracker = flametracker.Tracker()

@flametracker.wrap
def some_action():
    print("Some action done")

@flametracker.wrap
def perform_update():
    # Perform some actions
    some_action()
    some_action()

@flametracker.wrap
def update():
    # Check if the tracker is active
    if tracker.is_active():
        print("Tracker is active")
    else:
        print("Tracker is inactive")
    # Activate or deactivate the tracker based on user input
    inp = input("Enter 'a' to activate or 'd' to deactivate: ")
    if inp == "a":
        tracker.activate()
        print("Tracker activated")
    elif inp == "d":
        if tracker.try_deactivate():
            print("Tracker deactivated")
            print(tracker.to_str())
        else:
            print("Deactivation requested")
    perform_update()

# Continuously update based on user input
while True:
    update()
```

## Running Tests

To run the base test suite using `pytest`, execute:

```sh
pytest tests/test_base.py
```

To generate render tests in `tests/renders`, execute:

```sh
pytest tests/test_renders.py
```

## License

This project is licensed under the MIT License.
