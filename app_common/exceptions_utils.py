"""
This module contains the exceptions that should be handled internally
and not exposed to the user.
"""


class NonUserFacingException(Exception):
    """
    Exception raised for errors that should be handled internally
    and not exposed to the user.

    Attributes:
        message -- explanation of the error
    """

    def __init__(
        self,
        message="An internal error occurred.",
    ):
        self.message = message
        super().__init__(self.message)
