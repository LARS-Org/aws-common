import json
import decimal
import pytest
from app_common.app_utils import DecimalEncoder, get_first_non_none

def test_decimal_encoder_with_decimal():
    # Test that a decimal.Decimal is converted to a string
    data = {"value": decimal.Decimal("10.25")}
    json_data = json.dumps(data, cls=DecimalEncoder)
    assert json_data == '{"value": "10.25"}'

def test_decimal_encoder_with_non_decimal():
    # Test that non-decimal objects are encoded normally (e.g., strings and integers)
    data = {"string": "example", "int": 5, "float": 3.14}
    json_data = json.dumps(data, cls=DecimalEncoder)
    assert json_data == '{"string": "example", "int": 5, "float": 3.14}'

def test_decimal_encoder_with_mixed_data():
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

def test_decimal_encoder_with_nested_data():
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

def test_decimal_encoder_invalid_data():
    # Test that the encoder raises a TypeError for objects that can't be encoded (without handling by DecimalEncoder)
    with pytest.raises(TypeError):
        class CustomObject:
            pass
        json.dumps({"obj": CustomObject()}, cls=DecimalEncoder)

def test_get_first_non_none_with_all_none_args():
    """
    Test when all positional arguments are None.
    """
    result = get_first_non_none(None, None, None)
    assert result is None

def test_get_first_non_none_with_mixed_positional_args():
    """
    Test when there is a mix of None and non-None positional arguments.
    """
    result = get_first_non_none(None, 42, None)
    assert result == 42

def test_get_first_non_none_with_all_non_none_positional_args():
    """
    Test when all positional arguments are non-None.
    """
    result = get_first_non_none(1, 2, 3)
    assert result == 1

def test_get_first_non_none_with_all_none_kwargs():
    """
    Test when all keyword arguments are None.
    """
    result = get_first_non_none(a=None, b=None)
    assert result is None

def test_get_first_non_none_with_mixed_kwargs():
    """
    Test when there is a mix of None and non-None keyword arguments.
    """
    result = get_first_non_none(a=None, b=10)
    assert result == 10

def test_get_first_non_none_with_all_non_none_kwargs():
    """
    Test when all keyword arguments are non-None.
    """
    result = get_first_non_none(a=5, b=10)
    assert result == 5

def test_get_first_non_none_with_positional_and_kwargs():
    """
    Test when there are both positional and keyword arguments.
    """
    result = get_first_non_none(None, None, a=100, b=None)
    assert result == 100

def test_get_first_non_none_positional_takes_precedence():
    """
    Test that positional arguments take precedence over keyword arguments.
    """
    result = get_first_non_none(None, 99, a=100, b=None)
    assert result == 99

