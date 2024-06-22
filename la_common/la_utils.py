"""
General-purpose utilities.
"""

import decimal
import json


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

    for arg in args:
        if arg is not None:
            return arg

    for val in kwargs.items():
        if val is not None:
            return val

    return None


def get_first_element(l: list):
    """
    Returns the first element of a list, in case such an element exists.
    """

    return l[0] if l else None


def str_is_none_or_empty(s) -> bool:
    """
    Returns `True` in case the input argument is `None` or evaluates to an
    empty string, or `False` otherwise.
    """

    if s is None:
        return True

    return s.strip() == "" if isinstance(s, str) else str(s).strip() == ""


def is_numeric(x) -> bool:
    """
    Returns `True` in case the input argument is numeric. An argument is
    considered numeric if it is either an `int`, a `float`, or a `string`
    that may or may not have a plus (`+`) or minus sign (`-`) followed by
    digits between `0` and `9`.
    """

    if x is None:
        return False

    if isinstance(x, (int, float)):
        return True

    x_str = str(x).strip()

    if len(x_str) > 0 and x[0] in ("+", "-"):
        x_str = x_str[1:]

    return x_str.isnumeric()


def log_object(obj, title=None, log_limit: int = 150):
    """
    Logs an object to the console, truncate the content if large.
    If the object is a dictionary, it logs the keys and recursively logs the values.
    If the object is a list, it logs the first 10 elements and recursively logs them.
    """

    def _indentation_helper(level: int = 1, base_chars: str = "---") -> str:
        return "\r" + (base_chars * level)

    def generate_log_helper(obj, level: int = 0, log_limit: int = log_limit) -> str:
        type_str = f"[TYPE: {type(obj)}] "
        obj_str = str(obj)
        obj_str = type_str + obj_str

        # limit the object string length to avoid logging too much information
        if len(obj_str) <= log_limit:
            # object is small enough to log it entirely
            return _indentation_helper(level=level) + obj_str
        # else:
        # object is too large, truncate it
        obj_str = obj_str[:log_limit] + "..."

        if type(obj) in [dict, list]:
            # update the string to show only the type
            obj_str = type_str

        # indenting the object string
        obj_str = _indentation_helper(level=level) + obj_str

        # updating the indentation to show sub-elements in case of dictionaries and lists
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj_str += _indentation_helper(level=level) + f"{key} = "
                obj_str += generate_log_helper(value, level + 1)
        elif isinstance(obj, list):
            obj_str += (
                _indentation_helper(level=level) + f"Length: {len(obj)}. Sample: "
            )
            for i, item in enumerate(obj):
                if i >= 3:
                    break
                obj_str += generate_log_helper(item, level + 1)

        return obj_str

    if title:
        print(title)

    print(generate_log_helper(obj))
