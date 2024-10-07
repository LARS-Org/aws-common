import json
import decimal
import pytest
from app_common.app_utils import DecimalEncoder

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

