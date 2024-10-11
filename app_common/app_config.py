"""
Configuration parameters for the whole application.
"""

import os
import re


def is_valid_email(email: str) -> bool:
    """Check if the provided email is valid using a regex pattern."""
    email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    return re.match(email_regex, email) is not None


try:
    email_recipients_parameter = os.environ["AppDefaultEmailRecipients"]
    if (
        email_recipients_parameter.strip()
    ):  # Check if the string is non-empty after stripping spaces
        AppDefaultEmailRecipients = [
            x.strip()
            for x in email_recipients_parameter.split(",")
            if is_valid_email(x.strip())
        ]
    else:
        AppDefaultEmailRecipients = []  # Handle the case where it's an empty string
except KeyError:
    AppDefaultEmailRecipients = []
