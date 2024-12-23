"""Unit tests for deploy_all.py script."""

import subprocess
from unittest.mock import patch

import pytest

import deploy_all


@pytest.fixture
def mock_env():
    """Mock environment setup with test directories."""
    with (
        patch("os.path.exists") as mock_exists,
        patch("os.listdir") as mock_listdir,
        patch("os.path.isdir") as mock_isdir,
        patch("os.getcwd") as mock_getcwd,
    ):

        # Mock current directory
        mock_getcwd.return_value = "/test/dir"

        # Mock subdirectories (excluding test dir)
        mock_listdir.return_value = ["module1", "module2", ".git"]
        mock_isdir.side_effect = lambda x: x.split("/")[-1] in [
            "module1",
            "module2",
            ".git",
        ]

        # Mock file existence checks
        def exists_side_effect(path):
            if path.endswith(".venv"):
                return True
            if path.endswith("app_setup.py"):
                return True
            if path.endswith("activate"):
                return True
            return False

        mock_exists.side_effect = exists_side_effect
        yield


def test_run_command_success():
    """Test successful command execution."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "success"

        assert deploy_all.run_command("test command", shell=True)
        mock_run.assert_called_once()


def test_run_command_failure():
    """Test failed command execution."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "test command", stderr="error"
        )

        assert not deploy_all.run_command("test command", shell=True)


def test_main_aws_sso_failure(mock_env):
    """Test main execution with AWS SSO login failure."""
    with (
        patch("deploy_all.run_command") as mock_run,
        patch("deploy_all.deploy_module"),
        patch("sys.exit") as mock_exit,
    ):

        mock_run.return_value = False  # AWS SSO login fails

        deploy_all.main()

        assert mock_exit.call_count == 1
        assert mock_exit.call_args == ((1,),)
