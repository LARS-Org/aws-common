"""
This module contains utility functions meant to be used in tests.
"""

import os

# Constants for export
CONTENT_TYPE = "Content-Type"
APPLICATION_JSON = "application/json"

LAMBDA_AUTH_EVENT_TYPE_REQUEST = "REQUEST"
LAMBDA_AUTH_EVENT_TYPE_TOKEN = "TOKEN"


def set_aws_environment_variables(
    aws_access_key_id: str,
    aws_secret_access_key: str,
    aws_security_token: str,
    aws_session_token: str,
    aws_default_region: str = "us-east-1",
):
    """
    Sets some environment variables used by AWS.
    """
    os.environ["AWS_ACCESS_KEY_ID"] = aws_access_key_id
    os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret_access_key
    os.environ["AWS_SECURITY_TOKEN"] = aws_security_token
    os.environ["AWS_SESSION_TOKEN"] = aws_session_token
    os.environ["AWS_DEFAULT_REGION"] = aws_default_region


def set_fake_aws_environment_variables(aws_default_region: str = "us-east-1"):
    """
    Sets some environment variables used by AWS with fake values.
    This is meant to be used mainly for testing purposes, as some resources provided
    by the ``boto3`` library refuse to initialize when certain environment variables
    are empty.
    """
    set_aws_environment_variables(
        "testing", "testing", "testing", "testing", aws_default_region
    )


def get_fake_aws_lambda_context() -> dict:
    """
    Returns a dictionary containing fake values for information typically found in AWS
    Lambda Context objects. This is meant to be used mainly for testing purposes.
    """
    return {
        "aws_request_id": "testing",
        "log_group_name": "testing",
        "log_stream_name": "testing",
        "function_name": "testing",
        "function_version": "1",
        "invoked_function_arn": "testing",
        "memory_limit_in_mb": "128",
    }


def get_basic_aws_lambda_event(body=None) -> dict:
    """
    Returns a dictionary containing basic values for an AWS Lambda event.
    The keys present in the result dictionary are "body", whose value can be
    provided by the caller, and "headers", which is also a dictionary containing
    only the key "Content-Type" bound to value "application/json".
    """
    return {
        "body": body,
        "headers": {CONTENT_TYPE: APPLICATION_JSON},
    }


def get_aws_lambda_event_for_request_authorizer(
    method_arn="",
    resource="/",
    path="/",
    http_method="GET",
    headers: dict = None,
    multi_value_headers: dict = None,
    query_string_parameters: dict = None,
    multi_value_query_string_parameters: dict = None,
    path_parameters: dict = None,
    stage_variables: dict = None,
) -> dict:
    """
    Returns a dictionary with the typical structure of an event received by a
    request-based Lambda authorizer. This is meant to be used mainly for testing
    purposes.
    """
    if headers is None:
        headers = {}
    if multi_value_headers is None:
        multi_value_headers = {}
    if query_string_parameters is None:
        query_string_parameters = {}
    if multi_value_query_string_parameters is None:
        multi_value_query_string_parameters = {}
    if path_parameters is None:
        path_parameters = {}
    if stage_variables is None:
        stage_variables = {}

    return {
        "type": LAMBDA_AUTH_EVENT_TYPE_REQUEST,
        "methodArn": method_arn,
        "resource": resource,
        "path": path,
        "httpMethod": http_method,
        "headers": headers,
        "multiValueHeaders": multi_value_headers,
        "queryStringParameters": query_string_parameters,
        "multiValueQueryStringParameters": multi_value_query_string_parameters,
        "pathParameters": path_parameters,
        "stageVariables": stage_variables,
    }


def get_aws_lambda_event_for_token_authorizer(
    method_arn="", authorization_token=""
) -> dict:
    """
    Returns a dictionary with the typical structure of an event received by a
    token-based Lambda authorizer. This is meant to be used mainly for testing
    purposes.
    """
    return {
        "type": LAMBDA_AUTH_EVENT_TYPE_TOKEN,
        "methodArn": method_arn,
        "authorizationToken": authorization_token,
    }
