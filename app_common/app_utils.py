"""
General-purpose utilities.
"""

import decimal
import json
import numbers
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

    def _indent(indent_level: int = 1, base_chars: str = "---") -> str:
        # Generate indentation string based on the given level
        return "\n" + (base_chars * indent_level)

    output_lines = []
    stack = deque([(obj, 0)])
    ellipsis_chars = "…"

    while stack:
        current_obj, level = stack.pop()
        if isinstance(current_obj, str):
            # Handle string objects directly, applying truncation if needed
            output_lines.append(
                _indent(level)
                + (
                    current_obj[:log_limit] + ellipsis_chars
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
                + (
                    obj_str[:log_limit] + ellipsis_chars
                    if len(obj_str) > log_limit
                    else obj_str
                )
                + "\n"
            )

    if title:
        # Print the title if provided
        print(title)

    # Print the generated log for the given object
    print("".join(output_lines))


def do_log_2(obj, title=None, log_limit: int = 150, list_sample_size: int = 2):
    """
    Logs an object to the console, truncating the content if large.
    If the object is a dictionary, this method logs its keys and values.
    If the object is a list, this method only logs a sample of its elements,
    according to the sample size specified by the caller.
    """

    def _indent(indent_level: int = 1, base_chars: str = "--") -> str:
        """
        Generates an indentation string based on the given indentation level.
        """
        return base_chars * indent_level

    def _is_str_or_number_or_bool(x) -> bool:
        """
        Returns whether the input parameter is a string, number or boolean.
        """
        return (
            isinstance(x, str) or isinstance(x, numbers.Number) or isinstance(x, bool)
        )

    def _only_contains_str_or_number_or_bool(iterable) -> bool:
        """
        Returns whether the input parameter only contains strings, numbers or
        booleans.
        """
        return all([_is_str_or_number_or_bool(x) for x in iterable])

    output_lines = []
    stack = deque([(obj, 0)])

    base_chars_for_indent = "--"
    ellipsis_chars = "…"
    ellipsis_len = len(ellipsis_chars)

    while stack:
        current_obj, level = stack.pop()
        if isinstance(current_obj, str):
            # Handle string objects directly, applying truncation if needed
            output_lines.append(
                _indent(level, base_chars_for_indent)
                + (
                    current_obj[:log_limit] + ellipsis_chars
                    if len(current_obj) > log_limit
                    else current_obj
                )
            )

        elif isinstance(current_obj, dict):
            # Handle dictionary objects, logging each key and value
            output_lines.append(
                _indent(level, base_chars_for_indent) + f"[TYPE: {type(current_obj)}]; "
                f"Key count = {len(current_obj.items())}"
            )
            keys_are_simple = _only_contains_str_or_number_or_bool(current_obj.keys())
            values_are_simple = _only_contains_str_or_number_or_bool(
                current_obj.values()
            )

            if keys_are_simple and values_are_simple:
                # There are only simple keys and values in the dictionary,
                # let's try to fit as much content as we can in each line.
                # Key/value pairs are sorted in ascending order by the length
                # of the key added to the length of the value.
                keys = list(current_obj.keys())
                keys.sort(key=lambda k: len(str(k)) + len(str(current_obj[k])))
                key_idx = 0
                key_count = len(keys)

                on_first_item_in_line = True
                indented_empty_line = _indent(level + 1, base_chars_for_indent)
                line = indented_empty_line

                while key_idx < key_count:
                    key = str(keys[key_idx])
                    value = str(current_obj[key])
                    key_idx += 1

                    # Stores pending content
                    if len(line) >= log_limit:
                        output_lines.append(line)
                        on_first_item_in_line = True
                        line = indented_empty_line

                    # First try: full key, full value
                    cur_item_preamble = "" if on_first_item_in_line else " "
                    on_first_item_in_line = False
                    cur_key_and_val = cur_item_preamble + key + "=" + value

                    if len(line) + len(cur_key_and_val) <= log_limit:
                        line += cur_key_and_val
                        continue

                    # Second try: full key, partial value
                    cur_key_and_val = cur_item_preamble + key + "="
                    chars_left = (
                        log_limit - len(line) - len(cur_key_and_val) - ellipsis_len
                    )

                    if chars_left > 0:
                        partial_value = value[0 : max(0, chars_left)] + ellipsis_chars
                        cur_key_and_val += partial_value

                        if len(line) + len(cur_key_and_val) <= log_limit:
                            line += cur_key_and_val
                            continue

                    # Third try: partial key, full value
                    chars_left = (
                        log_limit
                        - len(line)
                        - len(cur_item_preamble)
                        - ellipsis_len
                        - len("=")
                        - len(value)
                    )

                    if chars_left > 0:
                        partial_key = key[0 : max(0, chars_left)] + ellipsis_chars
                        cur_key_and_val = cur_item_preamble + partial_key + "=" + value

                        if len(line) + len(cur_key_and_val) <= log_limit:
                            line += cur_key_and_val
                            continue

                    # Fourth try: partial key, partial value
                    chars_left = (
                        log_limit
                        - len(line)
                        - len(cur_item_preamble)
                        - ellipsis_len
                        - len("=")
                        - ellipsis_len
                    )

                    if chars_left > 1:
                        partial_len = chars_left // 2
                        partial_key = (
                            key
                            if len(key) <= partial_len
                            else key[0 : max(0, partial_len)] + ellipsis_chars
                        )
                        partial_value = (
                            value
                            if len(value) <= partial_len
                            else value[0 : max(0, partial_len)] + ellipsis_chars
                        )
                        cur_key_and_val = (
                            cur_item_preamble + partial_key + "=" + partial_value
                        )

                        if len(line) + len(cur_key_and_val) <= log_limit:
                            line += cur_key_and_val
                            continue

                    # We could not fit the key/value pair into the current line.
                    # Let's start a new line and try to process the key/value
                    # pair again.
                    if line != indented_empty_line:
                        output_lines.append(line)
                        on_first_item_in_line = True
                        line = indented_empty_line
                        key_idx -= 1

                # Stores pending content
                if line != indented_empty_line:
                    output_lines.append(line)
            else:
                # There are complex elements in the list, let's stack them for
                # later processing
                for key, value in reversed(current_obj.items()):
                    stack.append((value, level + 2))
                    output_lines.append(_indent(level + 1, base_chars_for_indent) + key)

        elif isinstance(current_obj, list):
            # Handle list objects, logging the first 2 elements as a sample
            output_lines.append(
                _indent(level, base_chars_for_indent) + f"[TYPE: {type(current_obj)}]; "
                f"Size = {len(current_obj)}; Sample:"
            )
            elems_are_simple = _only_contains_str_or_number_or_bool(current_obj)

            if elems_are_simple:
                # There are only simple elements in the list, let's try to fit
                # as much content as we can in each line
                elem_idx = 0
                elem_count = min(len(current_obj), list_sample_size)

                on_first_elem_in_line = True
                indented_empty_line = _indent(level + 1, base_chars_for_indent)
                line = indented_empty_line

                while elem_idx < elem_count:
                    elem = str(current_obj[elem_idx])
                    elem_idx += 1

                    # Stores pending content
                    if len(line) >= log_limit:
                        output_lines.append(line)
                        on_first_elem_in_line = True
                        line = indented_empty_line

                    # First try: full element
                    cur_elem_preamble = "" if on_first_elem_in_line else " "
                    on_first_elem_in_line = False
                    cur_elem_prefix = "[" + str(elem_idx - 1) + "]="
                    cur_elem = cur_elem_preamble + cur_elem_prefix + elem

                    if len(line) + len(cur_elem) <= log_limit:
                        line += cur_elem
                        continue

                    # Second try: partial element
                    cur_elem = cur_elem_preamble + cur_elem_prefix
                    chars_left = log_limit - len(line) - len(cur_elem) - ellipsis_len

                    if chars_left > 0:
                        partial_elem = elem[0 : max(0, chars_left)] + ellipsis_chars
                        cur_elem += partial_elem

                        if len(line) + len(cur_elem) <= log_limit:
                            line += cur_elem
                            continue

                    # We could not fit the element into the current line.
                    # Let's start a new line and try to process the element
                    # again.
                    if line != indented_empty_line:
                        output_lines.append(line)
                        on_first_elem_in_line = True
                        line = indented_empty_line
                        elem_idx -= 1

                # Stores pending content
                if line != indented_empty_line:
                    output_lines.append(line)
            else:
                for item in reversed(current_obj[:2]):
                    stack.append((item, level + 1))

        else:
            # Default case for other object types, applying truncation if needed
            obj_str = str(current_obj)
            output_lines.append(
                _indent(level, base_chars_for_indent)
                + (
                    obj_str[:log_limit] + ellipsis_chars
                    if len(obj_str) > log_limit
                    else obj_str
                )
            )

    # Print the title if provided
    if title:
        print(title)

    # Print the generated log for the given object
    print("\n".join(output_lines))


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
