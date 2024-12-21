"""
Tests for app_install_reqs.py
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app_scripts.app_install_reqs import _install_requirements_recursively


@pytest.fixture
def mock_functions():
    """Fixture to provide mock logging and command running functions."""
    do_log_func = MagicMock()
    run_cmd_func = MagicMock()
    return do_log_func, run_cmd_func


def test_install_requirements_recursively_with_client_reqs(mock_functions, tmp_path):
    """Test that client project requirements are installed first."""
    do_log_func, run_cmd_func = mock_functions
    
    # Create a temporary requirements.txt in the client project root
    client_reqs = tmp_path / "requirements.txt"
    client_reqs.write_text("client-specific-package==1.0.0")
    
    # Create a subdirectory with its own requirements.txt
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    subdir_reqs = subdir / "requirements.txt"
    subdir_reqs.write_text("subdir-package==2.0.0")
    
    # Change to the temporary directory and run the function
    with patch('os.getcwd', return_value=str(tmp_path)):
        _install_requirements_recursively(do_log_func, run_cmd_func)
    
    # Verify that client requirements were installed first
    assert run_cmd_func.call_args_list[0].args[0] == [
        "pip", "install", "-r", str(client_reqs), "--quiet"
    ]
    
    # Verify logging
    do_log_func.assert_any_call("*** Installing client project's requirements.txt (will be quiet)...")


def test_install_requirements_recursively_without_client_reqs(mock_functions, tmp_path):
    """Test that function works correctly when no client requirements exist."""
    do_log_func, run_cmd_func = mock_functions
    
    # Create a subdirectory with requirements.txt
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    subdir_reqs = subdir / "requirements.txt"
    subdir_reqs.write_text("subdir-package==2.0.0")
    
    # Change to the temporary directory and run the function
    with patch('os.getcwd', return_value=str(tmp_path)):
        _install_requirements_recursively(do_log_func, run_cmd_func)
    
    # Verify that no client requirements installation was attempted
    assert not any(
        "client project's requirements.txt" in call.args[0]
        for call in do_log_func.call_args_list
    )


def test_install_requirements_recursively_with_dev_reqs(mock_functions, tmp_path):
    """Test that both requirements.txt and requirements-dev.txt are considered."""
    do_log_func, run_cmd_func = mock_functions
    
    # Create both requirements files in the client project root
    client_reqs = tmp_path / "requirements.txt"
    client_reqs.write_text("client-package==1.0.0")
    
    client_dev_reqs = tmp_path / "requirements-dev.txt"
    client_dev_reqs.write_text("client-dev-package==1.0.0")
    
    # Change to the temporary directory and run the function
    with patch('os.getcwd', return_value=str(tmp_path)):
        _install_requirements_recursively(do_log_func, run_cmd_func)
    
    # Verify both requirements files were installed
    install_calls = [call.args[0] for call in run_cmd_func.call_args_list]
    assert ["pip", "install", "-r", str(client_reqs), "--quiet"] in install_calls
    assert ["pip", "install", "-r", str(client_dev_reqs), "--quiet"] in install_calls