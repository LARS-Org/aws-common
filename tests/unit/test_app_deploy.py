"""
Unit tests for app_deploy module.
"""

from unittest.mock import Mock

from app_scripts.app_deploy import do_deploy


def test_do_deploy():
    """Test the do_deploy function."""
    # Create mock functions
    mock_log = Mock()
    mock_run = Mock()

    # Call the function
    do_deploy(mock_log, mock_run)

    # Verify the logs
    mock_log.assert_any_call("deploying...")
    mock_log.assert_any_call("deployed!")

    # Verify the commands were run with correct parameters
    from unittest.mock import call

    expected_calls = [
        call("npm install -g aws-cdk", shell=True),
        call("cdk bootstrap", shell=True),
        call("cdk deploy --require-approval never", shell=True),
    ]
    assert mock_run.call_count == len(expected_calls)
    mock_run.assert_has_calls(expected_calls)
