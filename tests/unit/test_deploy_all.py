"""Unit tests for deploy_all.py"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from deploy_all import deploy_module


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for testing."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        yield mock_run


@pytest.fixture
def mock_os_path_exists():
    """Mock os.path.exists for testing."""
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = True
        yield mock_exists


@pytest.fixture
def mock_os_chmod():
    """Mock os.chmod for testing."""
    with patch("os.chmod") as mock_chmod:
        yield mock_chmod


def test_deploy_module_git_operations(
    mock_subprocess_run, mock_os_path_exists, mock_os_chmod
):
    """Test that git fetch and pull operations are performed before deployment."""
    module_path = "/test/module"

    # Call deploy_module
    result = deploy_module(module_path)

    assert result is True

    # Check that git commands were called in the correct order
    calls = mock_subprocess_run.call_args_list

    # First call should be git checkout main
    assert calls[0].kwargs["cwd"] == module_path
    assert calls[0].args[0] == ["git", "checkout", "main"]

    # Second call should be git fetch
    assert calls[1].kwargs["cwd"] == module_path
    assert calls[1].args[0] == ["git", "fetch"]

    # Third call should be git pull
    assert calls[2].kwargs["cwd"] == module_path
    assert calls[2].args[0] == ["git", "pull"]


def test_deploy_module_git_fetch_failure(
    mock_subprocess_run, mock_os_path_exists, mock_os_chmod
):
    """Test that deployment fails if git fetch fails."""
    module_path = "/test/module"

    # Make git fetch fail
    def side_effect(*args, **kwargs):
        if args[0] == ["git", "fetch"]:
            raise subprocess.CalledProcessError(1, "git fetch")
        return MagicMock(returncode=0)

    mock_subprocess_run.side_effect = side_effect

    # Call deploy_module
    result = deploy_module(module_path)

    assert result is False
