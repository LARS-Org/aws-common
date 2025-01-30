"""
Unit tests for the exceptions_utils module in app_common.
"""

from unittest import TestCase

from app_common.exceptions_utils import NonUserFacingException


class TestExceptionsUtils(TestCase):
    """
    Test cases for the NonUserFacingException class in exceptions_utils.
    """

    def test_non_user_facing_exception_default_message(self):
        """
        Test that the default message of NonUserFacingException is correct.
        """
        exception = NonUserFacingException()
        self.assertEqual(exception.message, "An internal error occurred.")

    def test_non_user_facing_exception_custom_message(self):
        """
        Test that a custom message can be set for NonUserFacingException.
        """
        custom_message = "Custom error message."
        exception = NonUserFacingException(message=custom_message)
        self.assertEqual(exception.message, custom_message)
