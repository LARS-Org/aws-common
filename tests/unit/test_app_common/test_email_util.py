import os
import unittest
from unittest.mock import patch

from app_common.email_util import send_email


class TestEmailUtil(unittest.TestCase):

    @patch.dict(os.environ, {"ResendAPIKey": "test_api_key"})
    @patch("resend.Emails.send")
    @patch("builtins.print")
    def test_send_email_success(self, mock_print, mock_send):
        """
        Test that send_email sends an email successfully and logs the response.
        """
        # Arrange
        mock_send.return_value = {"id": "test_email_id"}
        subject = "Test Subject"
        msg_html = "<h1>Test Message</h1>"
        recipient = "nobody@lars-ai.com"

        # Act
        send_email(subject, msg_html, recipient)

        # Assert
        mock_send.assert_called_once_with(
            {
                "from": "Acme <onboarding@resend.dev>",
                "to": recipient,
                "subject": subject,
                "html": msg_html,
            }
        )
        mock_print.assert_called_once_with({"id": "test_email_id"})

    @patch.dict(os.environ, {"ResendAPIKey": "test_api_key"})
    @patch("resend.Emails.send")
    @patch("builtins.print")
    def test_send_email_with_custom_recipient(self, mock_print, mock_send):
        """
        Test sending an email to a custom recipient.
        """
        # Arrange
        mock_send.return_value = {"id": "test_email_id"}
        subject = "Test Subject"
        msg_html = "<h1>Test Message</h1>"
        to = ["custom@example.com"]

        # Act
        send_email(subject, msg_html, to=to)

        # Assert
        mock_send.assert_called_once_with(
            {
                "from": "Acme <onboarding@resend.dev>",
                "to": to,
                "subject": subject,
                "html": msg_html,
            }
        )
        mock_print.assert_called_once_with({"id": "test_email_id"})

    @patch.dict(os.environ, {"ResendAPIKey": "test_api_key"})
    @patch("resend.Emails.send")
    @patch("builtins.print")
    def test_send_email_no_subject(self, mock_print, mock_send):
        """
        Test that no email is sent if the subject is None.
        """
        # Arrange
        subject = None
        msg_html = "<h1>Test Message</h1>"

        # Act
        send_email(subject, msg_html)

        # Assert
        mock_send.assert_not_called()
        mock_print.assert_called_once_with("*** No email to send")

    @patch.dict(os.environ, {"ResendAPIKey": "test_api_key"})
    @patch("resend.Emails.send")
    @patch("builtins.print")
    def test_send_email_no_message_body(self, mock_print, mock_send):
        """
        Test that no email is sent if the message body is None.
        """
        # Arrange
        subject = "Test Subject"
        msg_html = None

        # Act
        send_email(subject, msg_html)

        # Assert
        mock_send.assert_not_called()
        mock_print.assert_called_once_with("*** No email to send")

    @patch.dict(os.environ, {"ResendAPIKey": "test_api_key"})
    @patch("resend.Emails.send")
    @patch("builtins.print")
    def test_send_email_no_recipient(self, mock_print, mock_send):
        """
        Test that no email is sent if the recipient list is empty.
        """
        # Arrange
        subject = "Test Subject"
        msg_html = "<h1>Test Message</h1>"
        to = []

        # Act
        send_email(subject, msg_html, to=to)

        # Assert
        mock_send.assert_not_called()
        mock_print.assert_called_once_with("*** No email to send")

    @patch.dict(os.environ, {"ResendAPIKey": "test_api_key"})
    @patch("resend.Emails.send", side_effect=Exception("Test Error"))
    @patch("builtins.print")
    def test_send_email_exception_handling(self, mock_print, mock_send):
        """
        Test that send_email handles exceptions gracefully.
        """
        # Arrange
        subject = "Test Subject"
        msg_html = "<h1>Test Message</h1>"
        recipient = "nobody@lars-ai.com"

        # Act
        send_email(subject, msg_html, recipient)

        # Assert
        mock_send.assert_called_once()
        mock_print.assert_any_call("*** Error sending email: Test Subject")
        mock_print.assert_any_call(f"Msg: {msg_html}")
        mock_print.assert_any_call("Error: Test Error")

    @patch.dict(os.environ, {"ResendAPIKey": "test_api_key"})
    @patch("resend.Emails.send")
    @patch("builtins.print")
    def test_send_email_escape_characters_in_subject(self, mock_print, mock_send):
        """
        Test that send_email removes escape characters from the subject.
        """
        # Arrange
        mock_send.return_value = {"id": "test_email_id"}
        subject = "Test \\ Subject"
        msg_html = "<h1>Test Message</h1>"
        recipient = "nobody@lars-ai.com"

        # Act
        send_email(subject, msg_html, recipient)

        # Assert
        mock_send.assert_called_once_with(
            {
                "from": "Acme <onboarding@resend.dev>",
                "to": recipient,
                "subject": "Test  Subject",  # Backslash should be removed
                "html": msg_html,
            }
        )
        mock_print.assert_called_once_with({"id": "test_email_id"})


if __name__ == "__main__":
    unittest.main()
