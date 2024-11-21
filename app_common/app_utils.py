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


def _do_log(
    obj,
    title=None,
    log_limit: int = 150,
    list_sample_size: int = 2,
    line_break_chars: str = "\r",
):
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

    def _is_dict_or_list(x) -> bool:
        """
        Returns whether the input parameter is a dictionary or a list.
        """
        return isinstance(x, dict) or isinstance(x, list)

    def _is_not_dict_nor_list(x) -> bool:
        """
        Returns whether the input parameter is not a dictionary nor a list.
        """
        return not _is_dict_or_list(x)

    def _does_not_contain_dicts_nor_lists(iterable) -> bool:
        """
        Returns whether the input parameter does not contain dictionaries nor
        lists.
        """
        return all([_is_not_dict_nor_list(x) for x in iterable])

    def _get_dict_descriptor(d: dict) -> str:
        """
        Returns a descriptor of the input dictionary.
        """
        len_items = len(d.items())
        return f"[TYPE: {type(d)}]; Key count = {len_items}" + (
            "; Key/value pairs:" if len_items > 0 else ""
        )

    def _get_list_descriptor(x: list) -> str:
        """
        Returns a descriptor of the input list.
        """
        len_l = len(x)
        return f"[TYPE: {type(x)}]; Size = {len_l}" + ("; Sample:" if len_l > 0 else "")

    output_lines = []
    stack = deque([(obj, 0, True)])

    base_chars_for_indent = "--"
    ellipsis_chars = "…"
    ellipsis_len = len(ellipsis_chars)

    while stack:
        current_obj, level, print_cur_obj_type = stack.pop()

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
            # Handles dictionary objects, logging each key and value
            if print_cur_obj_type:
                output_lines.append(
                    _indent(level, base_chars_for_indent)
                    + _get_dict_descriptor(current_obj)
                )

            # Processes keys whose values are not lists nor dictionaries.
            # Key/value pairs are sorted in descending order by the length of
            # the key added to the length of the value, i.e., longer key/value
            # pairs are processed first.
            keys = [
                k for k in current_obj.keys() if _is_not_dict_nor_list(current_obj[k])
            ]
            keys.sort(
                key=lambda k: len(str(k)) + len(str(current_obj[k])), reverse=True
            )
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
                chars_left = log_limit - len(line) - len(cur_key_and_val) - ellipsis_len

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

            # Processes keys whose values are dictionaries
            keys = [k for k in current_obj.keys() if isinstance(current_obj[k], dict)]
            keys.sort()

            for key in keys:
                next_dict = current_obj[key]
                stack.append((next_dict, level + 1, False))
                stack.append(
                    (str(key) + "=" + _get_dict_descriptor(next_dict), level + 1, False)
                )

            # Processes keys whose values are lists
            keys = [k for k in current_obj.keys() if isinstance(current_obj[k], list)]
            keys.sort()

            for key in keys:
                next_list = current_obj[key]
                stack.append((next_list, level + 1, False))
                stack.append(
                    (str(key) + "=" + _get_list_descriptor(next_list), level + 1, False)
                )

        elif isinstance(current_obj, list):
            # Handles list objects, logging the first few elements as a sample
            if print_cur_obj_type:
                output_lines.append(
                    _indent(level, base_chars_for_indent)
                    + _get_list_descriptor(current_obj)
                )

            if _does_not_contain_dicts_nor_lists(current_obj):
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
                # There are complex elements in the list, let's stack them for
                # later processing
                for item in reversed(current_obj[:list_sample_size]):
                    stack.append((item, level + 1, _is_dict_or_list(item)))

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
    print(line_break_chars.join(output_lines))


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
