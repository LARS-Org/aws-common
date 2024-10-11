"""
General-purpose utilities.
"""

import decimal
import json
import subprocess
import sys
from collections import deque


class DecimalEncoder(json.JSONEncoder):
    """
    Utility class to encode `decimal.Decimal` objects as strings.
    """

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super().default(o)


def get_first_non_none(*args, **kwargs):
    """
    Returns the first argument that is not None, in case such an argument
    exists.
    """

    return next(
        (arg for arg in list(args) + list(kwargs.values()) if arg is not None), None
    )


def get_first_element(lst: list):
    """
    Returns the first element of a list, in case such an element exists.
    """

    if not isinstance(lst, list):
        raise TypeError(f"Expected list, got {type(lst).__name__}")

    return lst[0] if lst else None


def str_is_none_or_empty(s) -> bool:
    """
    Returns `True` in case the input argument is `None` or evaluates to an
    empty string, or `False` otherwise.
    """

    if s is None:
        return True
    if isinstance(s, str):
        return s.strip() == ""
    if str(s).strip() == "":
        return True
    return False


def is_numeric(x) -> bool:
    """
    Returns `True` in case the input argument is numeric. An argument is
    considered numeric if it is either an `int`, a `float`, or a string
    representing a number.
    """

    if x is None:
        return False

    try:
        float(x)
        return True
    except ValueError:
        return False


def do_log(obj, title=None, log_limit: int = 150):
    """
    Logs an object to the console, truncating the content if large.
    If the object is a dictionary, it logs the keys and values.
    If the object is a list, it logs the first 2 elements, indicating it's a sample.
    """

    def _indent(level: int = 1, base_chars: str = "---") -> str:
        # Generate indentation string based on the given level
        return "\n" + (base_chars * level)

    output_lines = []
    stack = deque([(obj, 0)])

    while stack:
        current_obj, level = stack.pop()
        if isinstance(current_obj, str):
            # Handle string objects directly, applying truncation if needed
            output_lines.append(
                _indent(level)
                + (
                    current_obj[:log_limit] + "..."
                    if len(current_obj) > log_limit
                    else current_obj
                )
                + "\n"
            )

        elif isinstance(current_obj, dict):
            # Handle dictionary objects, logging each key and value
            output_lines.append(_indent(level) + f"[TYPE: {type(current_obj)}]\n")
            for key, value in reversed(current_obj.items()):
                stack.append((value, level + 2))
                output_lines.append(_indent(level + 1) + key + "\n")

        elif isinstance(current_obj, list):
            # Handle list objects, logging the first 2 elements as a sample
            output_lines.append(
                _indent(level) + f"[TYPE: {type(current_obj)}] Sample:\n"
            )
            for item in reversed(current_obj[:2]):
                stack.append((item, level + 1))

        else:
            # Default case for other object types, applying truncation if needed
            obj_str = str(current_obj)
            output_lines.append(
                _indent(level)
                + (obj_str[:log_limit] + "..." if len(obj_str) > log_limit else obj_str)
                + "\n"
            )

    if title:
        # Print the title if provided
        print(title)

    # Print the generated log for the given object
    print("".join(output_lines))


def run_command(command, cwd=None, shell=False):
    """
    Run a shell command in the specified directory.

    :param command: The command to run.
    :param cwd: The directory to run the command in.
    :param shell: Whether to use a shell to run the command.
    """
    # TODO: #17 Fix it getting the correct path from the user's Windows environment
    # Replace 'python3.11' with the current Python executable
    if isinstance(command, list):
        command = [sys.executable if arg == "python3.11" else arg for arg in command]
    elif isinstance(command, str):
        command = command.replace("python3.11", sys.executable)

    result = subprocess.run(command, shell=shell, cwd=cwd)

    if result.returncode != 0:
        sys.exit(result.returncode)
