import traceback
from unittest.mock import patch

from app_common.base_lambda_handler import BaseLambdaHandler


# Create a concrete subclass for testing purposes
class TestLambdaHandler(BaseLambdaHandler):
    def _handle(self):
        # Simple implementation for testing
        return "Test handle executed"


class TestBaseLambdaHandler:
    def setup_method(self):
        """
        Set up a new instance of TestLambdaHandler before each test.
        """
        self.handler = TestLambdaHandler()

    def test_initialization(self):
        """
        Test that the TestLambdaHandler initializes with None for event, context,
        body, and headers.
        """
        assert self.handler.event is None
        assert self.handler.context is None
        assert self.handler.body is None
        assert self.handler.headers is None

    @patch("builtins.print")
    def test_on_error(self, mock_print):
        """
        Test that the _on_error method correctly handles exceptions and prints
        the error and traceback.
        """
        error_message = "Test Exception"

        try:
            raise Exception(error_message)
        except Exception as e:
            traceback_info = (
                traceback.format_exc()
            )  # Capture the traceback within the except block
            self.handler._on_error(e, traceback_info)

        # Check that the error message is printed
        mock_print.assert_any_call(
            f"BaseLambdaHandler::OnError():: Error occurred:\n{error_message}"
        )

        # Check if the debug statements are showing correct values
        mock_print.assert_any_call(traceback_info)

    def test_handle(self):
        """
        Test that the _handle method in the TestLambdaHandler works as expected.
        """
        result = self.handler._handle()
        assert result == "Test handle executed"
