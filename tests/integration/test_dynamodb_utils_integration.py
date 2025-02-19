import decimal
import json
from unittest import TestCase

import boto3
import pytest
from moto import mock_aws

from app_common.app_utils import (
    DecimalEncoder,
    get_first_element,
    get_first_non_none,
    is_numeric,
    str_is_none_or_empty,
)
from app_common.dynamodb_utils import DynamoDBBase


@pytest.fixture(scope="class")
def dynamodb_fixture():
    """Fixture to set up a mock DynamoDB resource and table."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        table_name = "TestTable"
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"},
                {"AttributeName": "sort_key", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "sort_key", "AttributeType": "N"},
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 10,
                "WriteCapacityUnits": 10,
            },
        )
        dynamodb_base = DynamoDBBase(table_name)
        yield dynamodb, dynamodb_base


class BaseDynamoDBIntegrationTest(TestCase):
    """Base class for DynamoDB integration tests that includes the fixture setup."""

    @pytest.fixture(autouse=True)
    def setup(self, dynamodb_fixture):
        """Set up DynamoDBBase and mock table."""
        self.dynamodb, self.dynamodb_base = dynamodb_fixture

    def get_item_from_table(self, table_name, key):
        """Helper method to retrieve an item from the DynamoDB table."""
        table = self.dynamodb.Table(table_name)
        return table.get_item(Key=key)


@pytest.mark.usefixtures("dynamodb_fixture")
class TestDynamoDBIntegrationWithDecimalEncoder(BaseDynamoDBIntegrationTest):
    def test_add_item_with_decimal_encoder(self):
        """Test adding an item to the DynamoDB table with explicit
        use of DecimalEncoder."""
        item = {"id": "123", "sort_key": 1, "value": decimal.Decimal("10.1")}
        json_encoded_item = json.dumps(item, cls=DecimalEncoder)

        # Load the JSON string back as a dictionary
        item_from_json = json.loads(json_encoded_item, parse_float=decimal.Decimal)

        # Use the deserialized item to add to DynamoDB
        result = self.dynamodb_base.add(item_from_json)

        response = self.get_item_from_table(
            "TestTable", {"id": "123", "sort_key": decimal.Decimal(1)}
        )

        expected_item = {
            "id": "123",
            "sort_key": decimal.Decimal(1),
            "value": "10.1",
        }
        self.assertEqual(response["Item"], expected_item)
        self.assertEqual(result, item_from_json)

    def test_update_existing_item_with_decimal_encoder(self):
        """Test updating an existing item in the DynamoDB table using DecimalEncoder."""
        # First, add an item
        item = {"id": "123", "sort_key": 1, "value": decimal.Decimal("10.1")}
        self.dynamodb_base.add(item)

        # Update the existing item
        update_expression = "SET updated_value = :val1"
        expression_attribute_values = {":val1": decimal.Decimal("20.5")}
        json_encoded_values = json.dumps(
            expression_attribute_values, cls=DecimalEncoder
        )

        # Load JSON back as a dictionary
        expression_values_from_json = json.loads(
            json_encoded_values, parse_float=decimal.Decimal
        )

        # Perform the update operation
        self.dynamodb_base.update(
            key={"id": "123", "sort_key": 1},
            update_expression=update_expression,
            expression_attribute_values=expression_values_from_json,
        )

        # Verify the item is updated
        response = self.get_item_from_table(
            "TestTable", {"id": "123", "sort_key": decimal.Decimal(1)}
        )
        expected_item = {
            "id": "123",
            "sort_key": decimal.Decimal(1),
            "value": decimal.Decimal("10.1"),
            "updated_value": "20.5",
        }
        self.assertEqual(response["Item"], expected_item)

    def test_write_batch_items_with_decimal_encoder(self):
        """Test batch writing multiple items to the DynamoDB table
        with DecimalEncoder."""
        items = [
            {"id": "1", "sort_key": 1, "value": decimal.Decimal("10.1")},
            {"id": "2", "sort_key": 2, "value": decimal.Decimal("20.2")},
            {"id": "3", "sort_key": 3, "value": decimal.Decimal("30.3")},
        ]

        json_encoded_items = json.dumps(items, cls=DecimalEncoder)
        items_from_json = json.loads(json_encoded_items, parse_float=decimal.Decimal)

        self.dynamodb_base.write_batch(items_from_json)

        for item in items_from_json:
            response = self.get_item_from_table(
                "TestTable",
                {"id": item["id"], "sort_key": decimal.Decimal(item["sort_key"])},
            )

            expected_item = {
                "id": item["id"],
                "sort_key": decimal.Decimal(item["sort_key"]),
                "value": str(item["value"]),
            }

            self.assertEqual(response["Item"], expected_item)

    def test_delete_item(self):
        """Test deleting an item from the DynamoDB table."""
        item = {"id": "123", "sort_key": 1, "value": decimal.Decimal("10.1")}
        self.dynamodb_base.add(item)

        # Delete the item
        self.dynamodb_base._del_by_keys(
            partition_key_name="id",
            partition_key_value="123",
            sort_key_name="sort_key",
            sort_key_value=1,
        )

        response = self.get_item_from_table(
            "TestTable", {"id": "123", "sort_key": decimal.Decimal(1)}
        )

        # Verify that the item is deleted
        self.assertNotIn("Item", response)


class TestDynamoDBIntegrationWithGetFirst(BaseDynamoDBIntegrationTest):
    """Integration tests for DynamoDBBase using utility functions
    like get_first_element."""

    def test_get_first_element_from_added_item(self):
        """Test adding an item and retrieving the first element using
        get_first_element."""
        item = {"id": "123", "sort_key": 1, "value": 10.1}
        self.dynamodb_base.add(item)

        response = self.get_item_from_table(
            "TestTable", {"id": "123", "sort_key": decimal.Decimal(1)}
        )
        result_item = response.get("Item")

        first_element = get_first_element(list(result_item.items()))
        self.assertEqual(first_element, ("id", "123"))

    def test_get_first_non_none(self):
        """Test adding an item and retrieving the first non-None value
        using get_first_non_none."""
        item = {"id": "123", "sort_key": 1, "value": None}
        self.dynamodb_base.add(item)

        response = self.get_item_from_table(
            "TestTable", {"id": "123", "sort_key": decimal.Decimal(1)}
        )
        result_item = response.get("Item")

        first_non_none = get_first_non_none(result_item.get("value"), "default")
        self.assertEqual(first_non_none, "default")


class TestDynamoDBIntegrationStringChecks(BaseDynamoDBIntegrationTest):
    """Integration tests for DynamoDBBase with string utility checks."""

    def test_str_is_none_or_empty_in_item(self):
        """Test adding an item and using str_is_none_or_empty to check fields."""
        item = {"id": "123", "sort_key": 1, "description": ""}
        self.dynamodb_base.add(item)

        response = self.get_item_from_table(
            "TestTable", {"id": "123", "sort_key": decimal.Decimal(1)}
        )
        result_item = response.get("Item")

        # Check if description is empty
        is_empty = str_is_none_or_empty(result_item.get("description"))
        self.assertTrue(is_empty)


class TestDynamoDBIntegrationNumericValidation(BaseDynamoDBIntegrationTest):
    """Integration tests for DynamoDBBase and numeric utility validation."""

    def test_is_numeric(self):
        """Test adding an item and checking numeric fields using is_numeric."""
        item = {"id": "123", "sort_key": 1, "value": 10.1}
        self.dynamodb_base.add(item)

        response = self.get_item_from_table(
            "TestTable", {"id": "123", "sort_key": decimal.Decimal(1)}
        )
        result_item = response.get("Item")

        # Validate the numeric field 'sort_key'
        self.assertTrue(is_numeric(result_item.get("sort_key")))
        # Validate the numeric field 'value'
        self.assertTrue(is_numeric(result_item.get("value")))
