"""
Email utility functions
"""

import os

import resend

from app_common.app_config import AppDefaultEmailRecipients


def send_email(subject, msg_html, to=AppDefaultEmailRecipients):
    """
    Send an email using Resend API
    """
    if not msg_html or not subject or not to:
        print("*** No email to send")
        return  # no message to send

    # removing any scape characters from subject
    subject = subject.replace("\\", "")

    try:
        resend.api_key = os.environ["ResendAPIKey"]
        email_params = {
            "from": "Acme <onboarding@resend.dev>",
            "to": to,
            "subject": subject,
            "html": msg_html,
        }
        email_response = resend.Emails.send(email_params)
        print(email_response)
    except Exception as email_error:
        print(f"*** Error sending email: {subject}")
        print(f"Msg: {msg_html}")
        print(f"Error: {email_error}")
