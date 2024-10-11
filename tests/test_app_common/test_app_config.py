import os
from unittest.mock import patch

import pytest


# Import the module after environment is mocked
def reload_module():
    """Helper function to reload the module to apply environment changes"""
    import importlib

    import app_common.app_config

    importlib.reload(app_common.app_config)
    return app_common.app_config


def test_app_default_email_recipients_with_env_var():
    # Test when the environment variable is set
    with patch.dict(
        os.environ,
        {"AppDefaultEmailRecipients": "test1@example.com, test2@example.com"},
    ):
        config_module = reload_module()
        assert config_module.AppDefaultEmailRecipients == [
            "test1@example.com",
            "test2@example.com",
        ]


def test_app_default_email_recipients_without_env_var():
    # Test when the environment variable is not set
    with patch.dict(os.environ, {}, clear=True):  # Clear environment variables
        config_module = reload_module()
        assert config_module.AppDefaultEmailRecipients == []


def test_app_default_email_recipients_empty_string():
    # Test when the environment variable is set but the value is an empty string
    with patch.dict(os.environ, {"AppDefaultEmailRecipients": ""}):
        config_module = reload_module()
        assert config_module.AppDefaultEmailRecipients == []


def test_app_default_email_recipients_single_value():
    # Test when the environment variable contains a single value
    with patch.dict(os.environ, {"AppDefaultEmailRecipients": "test@example.com"}):
        config_module = reload_module()
        assert config_module.AppDefaultEmailRecipients == ["test@example.com"]


def test_valid_emails():
    # Test with valid emails
    with patch.dict(
        "os.environ",
        {"AppDefaultEmailRecipients": "test1@example.com, test2@example.com"},
    ):
        config_module = reload_module()
        assert config_module.AppDefaultEmailRecipients == [
            "test1@example.com",
            "test2@example.com",
        ]


def test_invalid_emails():
    # Test with invalid emails
    with patch.dict(
        "os.environ", {"AppDefaultEmailRecipients": "test1@example, invalid-email"}
    ):
        config_module = reload_module()
        assert config_module.AppDefaultEmailRecipients == []


def test_mixed_valid_and_invalid_emails():
    # Test with a mix of valid and invalid emails
    with patch.dict(
        "os.environ",
        {
            "AppDefaultEmailRecipients": "valid1@example.com, invalid-email, valid2@example.com"
        },
    ):
        config_module = reload_module()
        assert config_module.AppDefaultEmailRecipients == [
            "valid1@example.com",
            "valid2@example.com",
        ]
