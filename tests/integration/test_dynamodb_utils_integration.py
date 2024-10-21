import decimal
from unittest import TestCase

import boto3
from moto import mock_aws

from app_common.dynamodb_utils import DynamoDBBase


@mock_aws
class TestDynamoDBIntegration(TestCase):
    def setUp(self):
        # Create mock DynamoDB service
        self.dynamodb = boto3.resource("dynamodb")

        # Create mock table for testing
        self.table_name = "TestTable"
        self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
                {"AttributeName": "sort_key", "KeyType": "RANGE"},  # Sort key
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

        # Initialize DynamoDBBase instance
        self.dynamodb_base = DynamoDBBase(self.table_name)

    def test_add_item(self):
        """Test adding an item to the DynamoDB table."""
        item = {"id": "123", "sort_key": 1, "value": 10.1}
        result = self.dynamodb_base.add(item)

        table = self.dynamodb.Table(self.table_name)
        response = table.get_item(Key={"id": "123", "sort_key": decimal.Decimal(1)})

        expected_item = {
            "id": "123",
            "sort_key": decimal.Decimal(1),
            "value": decimal.Decimal("10.1"),
        }
        self.assertEqual(response["Item"], expected_item)
        self.assertEqual(result, item)

    def test_update_existing_item(self):
        """Test updating an existing item in the DynamoDB table."""
        # First, add an item
        item = {"id": "123", "sort_key": 1, "value": 10.1}
        self.dynamodb_base.add(item)

        # Update the existing item using a non-reserved attribute name
        update_expression = "SET updated_value = :val1"
        expression_attribute_values = {":val1": 20.5}

        # Perform the update operation
        self.dynamodb_base.update(
            key={"id": "123", "sort_key": 1},
            update_expression=update_expression,
            expression_attribute_values=expression_attribute_values,
        )

        # Verify the item is updated
        response = self.dynamodb.Table(self.table_name).get_item(
            Key={"id": "123", "sort_key": decimal.Decimal(1)}
        )
        expected_item = {
            "id": "123",
            "sort_key": decimal.Decimal(1),
            "value": decimal.Decimal("10.1"),
            "updated_value": decimal.Decimal("20.5"),
        }
        self.assertEqual(response["Item"], expected_item)

    def test_get_last_items_by_key(self):
        """Test retrieving the last items by key, considering sort key."""
        items = [
            {"id": "id_value", "sort_key": 1, "attribute": "value1"},
            {"id": "id_value", "sort_key": 2, "attribute": "value2"},
            {"id": "id_value", "sort_key": 3, "attribute": "value3"},
        ]
        for item in items:
            self.dynamodb_base.add(item)

        last_items = self.dynamodb_base._get_last_items_by_key(
            key_name="id",
            key_value="id_value",
            k=2,
            scan_index_forward=False,
        )

        # Verify that the last two items are returned, in descending order of sort_key
        self.assertEqual(len(last_items), 2)
        self.assertEqual(last_items[0]["sort_key"], 3)
        self.assertEqual(last_items[1]["sort_key"], 2)

    def test_write_batch_items(self):
        """Test batch writing multiple items to the DynamoDB table."""
        items = [
            {"id": "1", "sort_key": 1, "value": 10.1},
            {"id": "2", "sort_key": 2, "value": 20.2},
            {"id": "3", "sort_key": 3, "value": 30.3},
        ]

        self.dynamodb_base.write_batch(items)

        table = self.dynamodb.Table(self.table_name)
        for item in items:
            response = table.get_item(
                Key={"id": item["id"], "sort_key": decimal.Decimal(item["sort_key"])}
            )

            # Convert expected item to have Decimal values
            expected_item = {
                "id": item["id"],
                "sort_key": decimal.Decimal(item["sort_key"]),
                "value": decimal.Decimal(str(item["value"])),
            }

            self.assertEqual(response["Item"], expected_item)

    def test_delete_item(self):
        """Test deleting an item from the DynamoDB table."""
        item = {"id": "123", "sort_key": 1, "value": 10.1}
        self.dynamodb_base.add(item)

        # Delete the item
        self.dynamodb_base._del_by_keys(
            primary_key_name="id",
            primary_key_value="123",
            sort_key_name="sort_key",
            sort_key_value=1,
        )

        table = self.dynamodb.Table(self.table_name)
        response = table.get_item(Key={"id": "123", "sort_key": 1})

        # Verify that the item is deleted
        self.assertNotIn("Item", response)
