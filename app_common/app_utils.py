"""
General-purpose utilities.
"""

import decimal
import json
import subprocess
import sys
import time


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


def json_dumps(data, indent=4, cls=DecimalEncoder) -> str:
    """
    Utility method to serialize data to JSON, including Decimal values.
    """
    return json.dumps(data, indent=indent, cls=cls)


def _do_log(
    obj,
    title=None,
    line_len_limit: int = 100,
    line_break_chars: str = " ",
    list_sample_size: int = 5,
    json_indent: int = 4,
    deep_limit: int = 3,
):
    """
    Logs an object to the console in a single entry, truncating long values
    and handling nested structures. Provides a clear, flat representation of
    the object with truncated values for improved readability.

    Args:
        obj: The object to log. Can be a dict, list, or any other data type.
        title (str, optional): A title to print before the log.
        line_len_limit (int): Maximum length for any single value in the log.
        line_break_chars (str): Characters to replace line breaks in the output.
        list_sample_size (int): Number of list elements to display before truncating.
        json_indent (int): Indentation level for JSON formatting.
        deep_limit (int): Maximum depth for processing nested structures.
    """

    def truncate(value, limit):
        """
        Truncates a string or value to the specified limit,
        adding ellipsis if truncated.

        Args:
            value: The value to truncate. Can be a string, int, or float.
            limit (int): Maximum length of the string.

        Returns:
            str: The truncated value as a string.
        """
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
        value = str(value)  # Ensure the input is a string
        if len(value) > limit:
            return value[:limit] + "..."
        return value

    def process(obj, deep=1):
        """
        Recursively processes objects (dicts and lists) into a flat
        representation with truncation.

        Args:
            obj: The object to process (can be a dict, list, or other type).
            deep (int): Current depth of recursion.

        Returns:
            The processed object with truncation applied.
        """
        if deep >= deep_limit:
            return truncate(obj, line_len_limit)

        if isinstance(obj, dict):
            return {k: process(v, deep + 1) for k, v in obj.items()}
        elif isinstance(obj, list):
            truncated_list = [process(v, deep + 1) for v in obj[:list_sample_size]]
            if len(obj) > list_sample_size:
                truncated_list.append(f"<...and {len(obj) - list_sample_size} more>")
            return truncated_list
        return truncate(obj, line_len_limit)

    # Process the object
    processed_obj = process(obj)

    # Prepare the log message as a JSON string, if necessary
    log_message = ""
    if isinstance(processed_obj, str):
        log_message = processed_obj
    else:
        log_message = json_dumps(processed_obj, indent=json_indent)

    # Replace line breaks with the specified characters
    log_message = log_message.replace("\n", line_break_chars)

    # Print the title if provided
    if title:
        print(title)

    # Print the formatted log message
    print(log_message)


def http_request(
    method, url, headers=None, json_data=None, params=None, timeout=30, **kwargs
):
    """
    Make an HTTP request using urllib3.

    :param method: HTTP method (e.g., "GET", "POST").
    :param url: URL to make the request to.
    :param headers: Dictionary of headers to include in the request.
    :param json_data: JSON payload for the request body.
        If provided, Content-Type will be set to application/json.
    :param params: Dictionary of query parameters to include in the URL.
    :param timeout: Timeout value in seconds for the request.
    :param kwargs: Additional arguments to pass to the urllib3 request method.
    :return: Dictionary containing:
        - status: HTTP status code (int)
        - headers: Response headers (dict)
        - body: Response body (parsed JSON if application/json response,
                string otherwise)
    :raises: JSONDecodeError if the response body is not valid JSON.
    """
    # It's necessary keep this import here to avoid circular dependencies
    import urllib3  # pylint: disable=import-outside-toplevel

    http = urllib3.PoolManager()

    if json_data is not None:
        headers = headers or {}
        headers.setdefault("Content-Type", "application/json")

    body = json_dumps(json_data, indent=None) if json_data else None

    # Append query parameters to the URL if provided
    if params:
        from urllib.parse import urlencode

        url = f"{url}?{urlencode(params)}"

    response = http.request(
        method=method,
        url=url,
        headers=headers,
        body=body,
        timeout=urllib3.Timeout(total=timeout),
        **kwargs,
    )

    response_data = response.data.decode("utf-8") if response.data else None

    if response_data and response.headers.get("Content-Type", "").startswith(
        "application/json"
    ):
        # If there is some parsing error, raise an exception
        response_data = json.loads(response_data)

    return {
        "status": response.status,
        "headers": dict(response.headers),
        "body": response_data,
    }


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


def unix_epoch_now() -> int:
    """
    Utility method to return the current timestamp,
    considering the Unix Epoch reference.
    """
    return int(time.time())
