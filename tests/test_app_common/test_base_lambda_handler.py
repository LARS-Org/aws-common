import traceback
from unittest.mock import patch

from app_common.base_lambda_handler import BaseLambdaHandler


# Create a concrete subclass for testing purposes
class TestLambdaHandler(BaseLambdaHandler):
    def _handle(self):
        # Simple implementation for testing
        return "Test handle executed"


def test_test_lambda_handler_initialization():
    """
    Test that the TestLambdaHandler initializes with None for
    event, context, body, and headers.
    """
    handler = TestLambdaHandler()

    assert handler.event is None
    assert handler.context is None
    assert handler.body is None
    assert handler.headers is None


def test_test_lambda_handler_on_error():
    """
    Test that the _on_error method correctly handles exceptions and
    prints the error and traceback.
    """
    handler = TestLambdaHandler()
    error_message = "Test Exception"

    with patch("builtins.print") as mock_print:
        try:
            raise Exception(error_message)
        except Exception as e:
            traceback_info = (
                traceback.format_exc()
            )  # Capture the traceback within the except block
            handler._on_error(e, traceback_info)

        # Check that the error message is printed
        mock_print.assert_any_call(
            f"BaseLambdaHandler::OnError():: Error occurred:\n{error_message}"
        )

        # Check if the debug statements are showing correct values
        mock_print.assert_any_call(traceback_info)


def test_test_lambda_handler_handle():
    """
    Test that the _handle method in the TestLambdaHandler works as expected.
    """
    handler = TestLambdaHandler()
    result = handler._handle()
    assert result == "Test handle executed"
