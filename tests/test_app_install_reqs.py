import os
import pytest
from unittest.mock import MagicMock

def test_install_requirements_recursively_with_client_reqs(tmp_path):
    """Test that client requirements are installed first."""
    from app_scripts.app_install_reqs import _install_requirements_recursively
    
    # Setup
    mock_log = MagicMock()
    mock_run = MagicMock()
    
    # Create test files
    client_req = tmp_path / "requirements.txt"
    client_req.write_text("client-package==1.0.0")
    
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    subdir_req = subdir / "requirements.txt"
    subdir_req.write_text("sub-package==1.0.0")
    
    # Test
    _install_requirements_recursively(str(tmp_path), ["requirements.txt"], mock_log, mock_run)
    
    # Verify
    assert mock_run.call_count == 2
    assert "client-package" in str(mock_run.call_args_list[0])
    assert "sub-package" in str(mock_run.call_args_list[1])

def test_install_requirements_recursively_no_client_reqs(tmp_path):
    """Test behavior when no client requirements exist."""
    from app_scripts.app_install_reqs import _install_requirements_recursively
    
    mock_log = MagicMock()
    mock_run = MagicMock()
    
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    subdir_req = subdir / "requirements.txt"
    subdir_req.write_text("sub-package==1.0.0")
    
    _install_requirements_recursively(str(tmp_path), ["requirements.txt"], mock_log, mock_run)
    
    assert mock_run.call_count == 1
    assert "sub-package" in str(mock_run.call_args_list[0])
