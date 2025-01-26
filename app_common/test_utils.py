"""
This module contains utility functions meant to be used in tests.
"""

import os


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
