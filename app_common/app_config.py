"""
Configuration parameters for the whole application.
"""

import os

try:
    email_recipients_parameter = os.environ["AppDefaultEmailRecipients"]
    AppDefaultEmailRecipients = [
        x.strip() for x in email_recipients_parameter.split(",")
    ]
except KeyError:
    AppDefaultEmailRecipients = []