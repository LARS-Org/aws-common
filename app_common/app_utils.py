"""
General-purpose utilities.
"""

import decimal
import json
import subprocess
import sys


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
    log_limit: int = 100,
    line_break_chars: str = " ",
):
    """
    Logs an object to the console in a single entry,
    truncating long values and handling nested structures.
    """

    def truncate(value, limit):
        """Truncates a string to the specified limit with ellipsis if needed."""
        if not value or is_numeric(value):
            return value
        value = str(value)  # Ensure the input is a string
        if len(value) > limit:
            truncated_value = value[:limit] + "..."
            return truncated_value
        return value

    def process(obj):
        """
        Recursively processes objects (dicts and lists) into
        a flat representation with truncation.
        """
        if isinstance(obj, dict):
            return {k: process(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [process(v) for v in obj]
        else:
            return truncate(obj, log_limit)

    # Process the object
    processed_obj = process(obj)

    # Prepare the log message as a JSON string
    log_message = json.dumps(processed_obj, indent=None)

    # Prepend the title if provided
    if title:
        log_message = f"{title}: {log_message}"

    # Print the log in a single entry
    print(log_message.replace("\n", line_break_chars))


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

    body = json.dumps(json_data) if json_data else None

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
