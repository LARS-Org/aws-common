"""Tests for deploy_all.py script."""

import os
import unittest
from unittest.mock import MagicMock, patch

from deploy_all import deploy_module, retry_on_failure


class TestDeployAll(unittest.TestCase):
    """Test cases for deploy_all.py."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.module_path = os.path.join(self.test_dir, "test_module")
        os.makedirs(self.module_path, exist_ok=True)

        # Create venv structure
        venv_dir = os.path.join(self.module_path, "venv")
        os.makedirs(os.path.join(venv_dir, "bin"), exist_ok=True)

        # Create activate script
        activate_path = os.path.join(venv_dir, "bin", "activate")
        with open(activate_path, "w") as f:
            f.write("# Dummy activate script")
        os.chmod(activate_path, 0o755)

        # Create a dummy app_setup.py
        with open(os.path.join(self.module_path, "app_setup.py"), "w") as f:
            f.write("# Dummy setup file")

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.module_path):
            for root, dirs, files in os.walk(self.module_path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.module_path)

    @patch("deploy_all.run_command")
    def test_deploy_module_success(self, mock_run_command):
        """Test successful deployment."""
        mock_run_command.return_value = True
        result = deploy_module(self.module_path)
        self.assertTrue(result)
        self.assertEqual(mock_run_command.call_count, 2)  # setup and deploy calls

    @patch("deploy_all.run_command")
    def test_deploy_module_retry_and_succeed(self, mock_run_command):
        """Test deployment with retry that eventually succeeds."""
        # First attempt: setup succeeds, deploy fails
        # Second attempt: setup succeeds, deploy succeeds
        mock_run_command.side_effect = [True, False, True, True]

        with patch("time.sleep") as mock_sleep:  # Don't actually sleep in tests
            result = deploy_module(self.module_path)

        self.assertTrue(result)
        self.assertEqual(mock_run_command.call_count, 4)
        self.assertEqual(mock_sleep.call_count, 1)  # Should sleep once between attempts

    @patch("deploy_all.run_command")
    def test_deploy_module_all_attempts_fail(self, mock_run_command):
        """Test deployment that fails all retry attempts."""
        # All attempts fail at setup
        mock_run_command.return_value = False

        with patch("time.sleep") as mock_sleep:  # Don't actually sleep in tests
            result = deploy_module(self.module_path)

        self.assertFalse(result)
        # 3 attempts, each with 1 setup call that fails
        self.assertEqual(mock_run_command.call_count, 3)
        self.assertEqual(
            mock_sleep.call_count, 2
        )  # Should sleep between retry attempts

    def test_retry_decorator(self):
        """Test the retry decorator directly."""
        mock_func = MagicMock()
        mock_func.side_effect = [False, False, True]

        decorated = retry_on_failure(max_attempts=3, delay=1)(mock_func)

        with patch("time.sleep") as mock_sleep:
            result = decorated()

        self.assertTrue(result)
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)


if __name__ == "__main__":
    unittest.main()
