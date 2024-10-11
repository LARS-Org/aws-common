import json
import decimal
import pytest
from app_common.app_utils import DecimalEncoder, get_first_non_none, get_first_element, str_is_none_or_empty, is_numeric, do_log

class TestDecimalEncoder:
    def test_decimal_encoder_with_decimal(self):
        # Test that a decimal.Decimal is converted to a string
        data = {"value": decimal.Decimal("10.25")}
        json_data = json.dumps(data, cls=DecimalEncoder)
        assert json_data == '{"value": "10.25"}'

    def test_decimal_encoder_with_non_decimal(self):
        # Test that non-decimal objects are encoded normally (e.g., strings and integers)
        data = {"string": "example", "int": 5, "float": 3.14}
        json_data = json.dumps(data, cls=DecimalEncoder)
        assert json_data == '{"string": "example", "int": 5, "float": 3.14}'

    def test_decimal_encoder_with_mixed_data(self):
        # Test a mixture of decimal.Decimal and other types
        data = {
            "decimal": decimal.Decimal("99.99"),
            "string": "example",
            "int": 42,
            "float": 1.234
        }
        json_data = json.dumps(data, cls=DecimalEncoder)
        expected_json = '{"decimal": "99.99", "string": "example", "int": 42, "float": 1.234}'
        assert json_data == expected_json

    def test_decimal_encoder_with_nested_data(self):
        # Test that decimal.Decimal objects inside nested data structures are encoded correctly
        data = {
            "nested": {
                "price": decimal.Decimal("199.99"),
                "description": "example product"
            }
        }
        json_data = json.dumps(data, cls=DecimalEncoder)
        expected_json = '{"nested": {"price": "199.99", "description": "example product"}}'
        assert json_data == expected_json

    def test_decimal_encoder_invalid_data(self):
        # Test that the encoder raises a TypeError for objects that can't be encoded (without handling by DecimalEncoder)
        with pytest.raises(TypeError):
            class CustomObject:
                pass
            json.dumps({"obj": CustomObject()}, cls=DecimalEncoder)

class TestGetFirstNonNone:
    def test_get_first_non_none_with_all_none_args(self):
        """
        Test when all positional arguments are None.
        """
        result = get_first_non_none(None, None, None)
        assert result is None

    def test_get_first_non_none_with_mixed_positional_args(self):
        """
        Test when there is a mix of None and non-None positional arguments.
        """
        result = get_first_non_none(None, 42, None)
        assert result == 42

    def test_get_first_non_none_with_all_non_none_positional_args(self):
        """
        Test when all positional arguments are non-None.
        """
        result = get_first_non_none(1, 2, 3)
        assert result == 1

    def test_get_first_non_none_with_all_none_kwargs(self):
        """
        Test when all keyword arguments are None.
        """
        result = get_first_non_none(a=None, b=None)
        assert result is None

    def test_get_first_non_none_with_mixed_kwargs(self):
        """
        Test when there is a mix of None and non-None keyword arguments.
        """
        result = get_first_non_none(a=None, b=10)
        assert result == 10

    def test_get_first_non_none_with_all_non_none_kwargs(self):
        """
        Test when all keyword arguments are non-None.
        """
        result = get_first_non_none(a=5, b=10)
        assert result == 5

    def test_get_first_non_none_with_positional_and_kwargs(self):
        """
        Test when there are both positional and keyword arguments.
        """
        result = get_first_non_none(None, None, a=100, b=None)
        assert result == 100

    def test_get_first_non_none_positional_takes_precedence(self):
        """
        Test that positional arguments take precedence over keyword arguments.
        """
        result = get_first_non_none(None, 99, a=100, b=None)
        assert result == 99

class TestGetFirstElement:
    def test_get_first_element_empty_list(self):
        """
        Test that get_first_element returns None for an empty list.
        """
        result = get_first_element([])
        assert result is None

    def test_get_first_element_single_element_list(self):
        """
        Test that get_first_element returns the only element in a list with one element.
        """
        result = get_first_element([42])
        assert result == 42

    def test_get_first_element_multiple_elements_list(self):
        """
        Test that get_first_element returns the first element in a list with multiple elements.
        """
        result = get_first_element([1, 2, 3, 4, 5])
        assert result == 1

    def test_get_first_element_non_list_input(self):
        """
        Test that get_first_element raises an error when the input is not a list.
        """
        with pytest.raises(TypeError, match="Expected list, got int"):
            get_first_element(42)   # Passing a non-list value
        with pytest.raises(TypeError, match="Expected list, got str"):
            get_first_element("string") # Passing a string
        with pytest.raises(TypeError, match="Expected list, got NoneType"):
            get_first_element(None) # Passing None

class TestStrIsNoneOrEmpty:
    def test_str_is_none(self):
        """
        Test when the input is None. The function should return True.
        """
        result = str_is_none_or_empty(None)
        assert result is True

    def test_str_is_empty_string(self):
        """
        Test when the input is an empty string. The function should return True.
        """
        result = str_is_none_or_empty("")
        assert result is True

    def test_str_is_whitespace(self):
        """
        Test when the input is a string containing only whitespace. The function should return True.
        """
        result = str_is_none_or_empty("   ")
        assert result is True

    def test_str_is_non_empty_string(self):
        """
        Test when the input is a non-empty string. The function should return False.
        """
        result = str_is_none_or_empty("Hello")
        assert result is False

    def test_str_is_number(self):
        """
        Test when the input is a number. The function should return False.
        """
        result = str_is_none_or_empty(123)
        assert result is False

    def test_str_is_empty_converted_number(self):
        """
        Test when the input is zero. The function should return False because '0' is not an empty string.
        """
        result = str_is_none_or_empty(0)
        assert result is False

    def test_str_is_object_with_empty_str_representation(self):
        """
        Test when the input is an object whose string representation is an empty string. The function should return True.
        """
        class EmptyStr:
            def __str__(self):
                return ""

        result = str_is_none_or_empty(EmptyStr())
        assert result is True

    def test_str_is_object_with_non_empty_str_representation(self):
        """
        Test when the input is an object whose string representation is non-empty. The function should return False.
        """
        class NonEmptyStr:
            def __str__(self):
                return "NonEmpty"

        result = str_is_none_or_empty(NonEmptyStr())
        assert result is False

class TestIsNumeric:
    def test_is_numeric_with_none(self):
        """
        Test that None returns False.
        """
        result = is_numeric(None)
        assert result is False

    def test_is_numeric_with_integer(self):
        """
        Test that an integer returns True.
        """
        result = is_numeric(42)
        assert result is True

    def test_is_numeric_with_float(self):
        """
        Test that a float returns True.
        """
        result = is_numeric(3.14)
        assert result is True

    def test_is_numeric_with_positive_string_integer(self):
        """
        Test that a positive integer string returns True.
        """
        result = is_numeric("42")
        assert result is True

    def test_is_numeric_with_negative_string_integer(self):
        """
        Test that a negative integer string returns True.
        """
        result = is_numeric("-42")
        assert result is True

    def test_is_numeric_with_positive_string_float(self):
        """
        Test that a positive float string returns True.
        """
        result = is_numeric("3.14")
        assert result is True

    def test_is_numeric_with_negative_string_float(self):
        """
        Test that a negative float string returns True.
        """
        result = is_numeric("-3.14")
        assert result is True

    def test_is_numeric_with_plus_sign_string(self):
        """
        Test that a string with a plus sign followed by digits returns True.
        """
        result = is_numeric("+123")
        assert result is True

    def test_is_numeric_with_non_numeric_string(self):
        """
        Test that a non-numeric string returns False.
        """
        result = is_numeric("abc")
        assert result is False

    def test_is_numeric_with_whitespace_string(self):
        """
        Test that a string with only whitespace returns False.
        """
        result = is_numeric("   ")
        assert result is False

import pprint
from unittest.mock import patch
from app_common.app_utils import do_log

class TestDoLog:
    @patch('builtins.print')
    def test_do_log_string(self, mock_print):
        """
        Test logging a simple string.
        """
        test_str = "Hello, this is a test."
        do_log(test_str)
        mock_print.assert_called_once_with("\nHello, this is a test.\n")

    @patch('builtins.print')
    def test_do_log_truncated_string(self, mock_print):
        """
        Test logging a long string that should be truncated.
        """
        test_str = "a" * 200
        do_log(test_str, log_limit=50)
        mock_print.assert_called_once_with("\naaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa...\n")

    @patch('builtins.print')
    def test_do_log_with_title(self, mock_print):
        """
        Test logging with a title.
        """
        test_str = "Test string"
        do_log(test_str, title="Title")
        mock_print.assert_any_call("Title")
        mock_print.assert_any_call("\nTest string\n")

    @patch('builtins.print')
    def test_do_log_dictionary(self, mock_print):
        """
        Test logging a dictionary.
        """
        test_dict = {"key1": "value1", "key2": {"subkey1": "subvalue1"}}
        do_log(test_dict, log_limit=50)
        calls = [call[0][0] for call in mock_print.call_args_list]
        assert "\n[TYPE: <class 'dict'>]\n\n---key2\n\n---key1\n\n------value1\n\n------[TYPE: <class 'dict'>]\n\n---------subkey1\n\n------------subvalue1\n" in calls

    @patch('builtins.print')
    def test_do_log_list(self, mock_print):
        """
        Test logging a list.
        """
        test_list = ["element1", "element2", "element3"]
        do_log(test_list, log_limit=50)
        calls = [call[0][0] for call in mock_print.call_args_list]
        assert "\n[TYPE: <class 'list'>] Sample:\n\n---element1\n\n---element2\n" in calls

    @patch('builtins.print')
    def test_do_log_empty_dictionary(self, mock_print):
        """
        Test logging an empty dictionary.
        """
        do_log({})
        mock_print.assert_called_once_with("\n[TYPE: <class 'dict'>]\n")

    @patch('builtins.print')
    def test_do_log_empty_list(self, mock_print):
        """
        Test logging an empty list.
        """
        do_log([])
        mock_print.assert_called_once_with("\n[TYPE: <class 'list'>] Sample:\n")

    @patch('builtins.print')
    def test_do_log_default_case_int(self, mock_print):
        """
        Test logging an integer (default case).
        """
        do_log(42, log_limit=50)
        mock_print.assert_called_once_with("\n42\n")

    @patch('builtins.print')
    def test_do_log_default_case_float(self, mock_print):
        """
        Test logging a float (default case).
        """
        do_log(3.14159, log_limit=50)
        mock_print.assert_called_once_with("\n3.14159\n")

    @patch('builtins.print')
    def test_do_log_default_case_object(self, mock_print):
        """
        Test logging an object instance (default case).
        """
        class SampleObject:
            def __str__(self):
                return "SampleObjectRepresentation"

        obj = SampleObject()
        do_log(obj, log_limit=50)
        mock_print.assert_called_once_with("\nSampleObjectRepresentation\n")

    @patch('builtins.print')
    def test_do_log_truncated_object(self, mock_print):
        """
        Test logging a long object string representation that should be truncated.
        """
        class SampleObject:
            def __str__(self):
                return "A" * 200

        obj = SampleObject()
        do_log(obj, log_limit=50)
        mock_print.assert_called_once_with("\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA...\n")

from unittest.mock import call
import subprocess, sys
from app_common.app_utils import run_command

class TestRunCommand:
    @patch('subprocess.run')
    def test_run_command_success(self, mock_subprocess_run):
        """
        Test that run_command runs successfully.
        """
        mock_subprocess_run.return_value.returncode = 0
        run_command(["echo", "Hello World"])
        mock_subprocess_run.assert_called_once_with(["echo", "Hello World"], shell=False, cwd=None)

    @patch('subprocess.run')
    @patch('sys.exit')
    def test_run_command_failure(self, mock_sys_exit, mock_subprocess_run):
        """
        Test that run_command exits on failure.
        """
        mock_subprocess_run.return_value.returncode = 1
        run_command(["invalid_command"])
        mock_subprocess_run.assert_called_once_with(["invalid_command"], shell=False, cwd=None)
        mock_sys_exit.assert_called_once_with(1)

    @patch('subprocess.run')
    def test_run_command_with_shell(self, mock_subprocess_run):
        """
        Test that run_command runs successfully with shell=True.
        """
        mock_subprocess_run.return_value.returncode = 0
        run_command(["echo Hello World"], shell=True)
        mock_subprocess_run.assert_called_once_with(["echo Hello World"], shell=True, cwd=None)

    @patch('subprocess.run')
    def test_run_command_with_cwd(self, mock_subprocess_run):
        """
        Test that run_command runs successfully with a specific working directory.
        """
        mock_subprocess_run.return_value.returncode = 0
        run_command(["ls"], cwd="/home/user")
        mock_subprocess_run.assert_called_once_with(["ls"], shell=False, cwd="/home/user")

    @patch('subprocess.run')
    def test_run_command_replace_python(self, mock_subprocess_run):
        """
        Test that run_command replaces 'python3.11' with the current Python executable.
        """
        mock_subprocess_run.return_value.returncode = 0
        run_command(["python3.11", "--version"])
        mock_subprocess_run.assert_called_once_with([sys.executable, "--version"], shell=False, cwd=None)

    @patch('subprocess.run')
    def test_run_command_string_command(self, mock_subprocess_run):
        """
        Test run_command with a string command to ensure replacement of 'python3.11' with sys.executable.
        """
        mock_subprocess_run.return_value.returncode = 0
        run_command("python3.11 --version", shell=True)
        mock_subprocess_run.assert_called_once_with(f"{sys.executable} --version", shell=True, cwd=None)

    @patch('subprocess.run')
    def test_run_command_string_command_no_replacement(self, mock_subprocess_run):
        """
        Test run_command with a string command that does not require replacement.
        """
        mock_subprocess_run.return_value.returncode = 0
        run_command("echo Hello World", shell=True)
        mock_subprocess_run.assert_called_once_with("echo Hello World", shell=True, cwd=None)
