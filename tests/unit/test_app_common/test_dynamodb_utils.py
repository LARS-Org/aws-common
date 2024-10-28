import os
from decimal import Decimal
from unittest import TestCase

import boto3
from botocore.exceptions import ClientError
from moto import mock_aws

from app_common.dynamodb_utils import DynamoDBBase


# Define a simple class to test object conversion
class TestObject:
    def __init__(self, attr1, attr2):
        self.attr1 = attr1
        self.attr2 = attr2


@mock_aws
class TestDynamoDBBase(TestCase):
    @classmethod
    def setUpClass(cls):
        """Print environment variables before executing any tests."""
        aws_region = os.getenv("AWS_REGION", "Not Set")
        aws_default_region = os.getenv("AWS_DEFAULT_REGION", "Not Set")
        print(f"Environment Variable AWS_REGION: {aws_region}")
        print(f"Environment Variable AWS_DEFAULT_REGION: {aws_default_region}")

    def setUp(self):
        boto3.setup_default_session()
        self.dynamodb = boto3.resource("dynamodb")

        # Create a mock table to be used for testing
        self.table_name = "test-table"
        self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"},
                {"AttributeName": "sort_key", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "sort_key", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        self.dynamodb_base = DynamoDBBase(self.table_name)

    def tearDown(self):
        self.dynamodb.Table(self.table_name).delete()

    def test_add_item(self):
        """Test adding an item to the DynamoDB table."""
        # Define the item to be added
        item = {"id": "123", "sort_key": "1", "value": 1.23}

        # Call the add method to add the item
        self.dynamodb_base.add(item)

        # Retrieve the item from the table and check its contents
        table = self.dynamodb.Table(self.table_name)
        response = table.get_item(Key={"id": item["id"], "sort_key": item["sort_key"]})

        # Verify the response
        expected_item = {"id": "123", "sort_key": "1", "value": Decimal("1.23")}
        self.assertEqual(response["Item"], expected_item)

    def test_get_last_items_by_key(self):
        """Test retrieving the last k items by key."""
        # Adding items to the table
        items = [
            {"id": "123", "sort_key": "1", "value": Decimal("1.23")},
            {"id": "123", "sort_key": "2", "value": Decimal("2.34")},
            {"id": "123", "sort_key": "3", "value": Decimal("3.45")},
        ]
        self.dynamodb_base.write_batch(items)

        # Retrieve the last item
        result = self.dynamodb_base._get_last_items_by_key("id", "123", 1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sort_key"], "3")

        # Retrieve the last two items
        result = self.dynamodb_base._get_last_items_by_key("id", "123", 2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["sort_key"], "3")
        self.assertEqual(result[1]["sort_key"], "2")

    def test_get_last_items_by_key_no_items(self):
        """Test retrieving items by key when no matching items exist."""
        # No items are added to the table
        result = self.dynamodb_base._get_last_items_by_key("id", "nonexistent", 1)
        self.assertEqual(result, [])

    def test_get_last_items_by_key_less_than_k(self):
        """Test retrieving items by key when fewer than k items exist."""
        # Adding items to the table
        items = [
            {"id": "123", "sort_key": "1", "value": Decimal("1.23")},
            {"id": "123", "sort_key": "2", "value": Decimal("2.34")},
        ]
        self.dynamodb_base.write_batch(items)

        # Retrieve more items than are present
        result = self.dynamodb_base._get_last_items_by_key("id", "123", 5)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["sort_key"], "2")
        self.assertEqual(result[1]["sort_key"], "1")

    def test_get_last_items_by_key_reverse_order(self):
        """Test retrieving the last k items in reverse order."""
        # Adding items to the table
        items = [
            {"id": "123", "sort_key": "1", "value": Decimal("1.23")},
            {"id": "123", "sort_key": "2", "value": Decimal("2.34")},
            {"id": "123", "sort_key": "3", "value": Decimal("3.45")},
        ]
        self.dynamodb_base.write_batch(items)

        # Retrieve the last two items in reverse order
        result = self.dynamodb_base._get_last_items_by_key(
            "id", "123", 2, scan_index_forward=True
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["sort_key"], "1")
        self.assertEqual(result[1]["sort_key"], "2")

    def test_get_last_items_by_key_invalid_key(self):
        """Test retrieving items by key with an invalid key name."""
        # Adding items to the table
        items = [
            {"id": "123", "sort_key": "1", "value": Decimal("1.23")},
        ]
        self.dynamodb_base.write_batch(items)

        with self.assertRaises(Exception):
            # Attempt to retrieve with a non-existent key
            self.dynamodb_base._get_last_items_by_key("invalid_key", "123", 1)

    def test_update_item(self):
        """Test updating an item in the DynamoDB table."""
        # Add an item to update
        item = {"id": "123", "sort_key": "abc", "attr_value": Decimal("1.23")}
        self.dynamodb_base.add(item)

        # Update the item (change value from Decimal("1.23") to Decimal("4.56"))
        update_expression = "SET attr_value = :val1"
        expression_attribute_values = {":val1": Decimal("4.56")}

        # Perform the update
        self.dynamodb_base._table.update_item(
            Key={"id": "123", "sort_key": "abc"},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
        )

        # Verify that the item was updated
        table = self.dynamodb.Table(self.table_name)
        response = table.get_item(Key={"id": "123", "sort_key": "abc"})
        self.assertEqual(response["Item"]["attr_value"], Decimal("4.56"))

    def test_update_existing_item(self):
        """Test updating an existing item in the DynamoDB table."""
        # Add an item to the table
        item = {"id": "123", "sort_key": "1", "value": Decimal("10.1")}
        self.dynamodb_base.add(item)

        # Update the item
        key = {"id": "123", "sort_key": "1"}
        update_expression = "SET #value = :val"
        expression_attribute_values = {":val": Decimal("20.2")}
        expression_attribute_names = {"#value": "value"}
        response_key = self.dynamodb_base._table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
        )

        # Verify the update was successful
        table = self.dynamodb.Table(self.table_name)
        response = table.get_item(Key=key)
        self.assertEqual(response_key["ResponseMetadata"]["HTTPStatusCode"], 200)
        self.assertEqual(response["Item"]["value"], Decimal("20.2"))

    def test_update_non_existing_item(self):
        """Test updating a non-existing item in the DynamoDB table."""
        # Update a non-existing item
        key = {"id": "456", "sort_key": "1"}
        update_expression = "SET #value = :val"
        expression_attribute_values = {":val": Decimal("30.3")}
        expression_attribute_names = {"#value": "value"}
        response_key = self.dynamodb_base._table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
        )

        # Verify the item was added to the table with the correct values
        table = self.dynamodb.Table(self.table_name)
        response = table.get_item(Key=key)
        self.assertEqual(response_key["ResponseMetadata"]["HTTPStatusCode"], 200)
        self.assertEqual(response["Item"]["value"], Decimal("30.3"))

    def test_update_float_to_decimal_conversion(self):
        """Test updating an item by converting float to Decimal."""
        key = {"id": "123", "sort_key": "1"}

        # Use Decimal instead of float for the update
        update_expression = "SET #value = :value"
        expression_attribute_values = {":value": Decimal("20.2")}
        expression_attribute_names = {"#value": "value"}

        self.dynamodb_base._table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
        )

        # Retrieve and verify the updated item
        table = self.dynamodb.Table(self.table_name)
        response = table.get_item(Key=key)
        expected_item = {"id": "123", "sort_key": "1", "value": Decimal("20.2")}
        self.assertEqual(response["Item"], expected_item)

    def test_update_reserved_keyword(self):
        """Test updating an item using a reserved keyword."""
        # Add an item to the table
        item = {"id": "101", "sort_key": "1", "value": Decimal("10.0")}
        self.dynamodb_base.add(item)

        # Update the item using a reserved keyword
        key = {"id": "101", "sort_key": "1"}
        update_expression = "SET #value = :val"
        expression_attribute_names = {"#value": "value"}
        expression_attribute_values = {":val": Decimal("25.0")}
        try:
            self.dynamodb_base._table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
            )
        except ClientError as e:
            self.fail(f"Update operation failed with error: {e}")

        # Verify the update was successful
        table = self.dynamodb.Table(self.table_name)
        response = table.get_item(Key=key)
        self.assertEqual(response["Item"]["value"], Decimal("25.0"))

    def test_update_invalid_expression(self):
        """Test updating an item with an invalid update expression."""
        # Add an item to the table
        item = {"id": "102", "sort_key": "1", "value": Decimal("15.0")}
        self.dynamodb_base.add(item)

        # Attempt to update the item with an invalid expression
        key = {"id": "102", "sort_key": "1"}
        update_expression = "INVALID_EXPRESSION"
        expression_attribute_values = {":val": Decimal("20.0")}

        with self.assertRaises(ClientError):
            self.dynamodb_base.update(
                key, update_expression, expression_attribute_values
            )

    def test_update_missing_key(self):
        """Test updating an item with a missing key."""
        # Attempt to update an item with a missing key
        key = {"id": "103"}
        update_expression = "SET #value = :val"
        expression_attribute_values = {":val": Decimal("25.0")}

        with self.assertRaises(ClientError):
            self.dynamodb_base.update(
                key, update_expression, expression_attribute_values
            )

    def test_get_by_partition_key(self):
        """Test retrieving items by partition key."""
        item1 = {"id": "123", "sort_key": "a", "value": Decimal("1.23")}
        item2 = {"id": "123", "sort_key": "b", "value": Decimal("2.34")}
        item3 = {"id": "456", "sort_key": "c", "value": Decimal("3.45")}

        self.dynamodb_base.add(item1)
        self.dynamodb_base.add(item2)
        self.dynamodb_base.add(item3)

        result = self.dynamodb_base.get_by_partition_key(pk_name="id", pk_value="123")
        self.assertEqual(result, [item1, item2])

    def test_get_all_with_default_limit(self):
        """Test retrieving all items with the default limit."""
        # Adding sample items
        items = [
            {"id": f"{i}", "sort_key": "1", "value": Decimal(f"{i}.23")}
            for i in range(3)
        ]
        self.dynamodb_base.write_batch(items)

        # Call get_all with default limit (100)
        result = self.dynamodb_base.get_all()
        self.assertTrue(len(result) <= 100)
        self.assertEqual(result, items)

    def test_get_all_with_custom_limit(self):
        """Test retrieving items with a custom limit."""
        # Adding sample items
        items = [
            {"id": f"{i}", "sort_key": "1", "value": Decimal(f"{i}.23")}
            for i in range(5)
        ]
        self.dynamodb_base.write_batch(items)

        # Call get_all with a limit of 2
        result = self.dynamodb_base.get_all(limit=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result, items[:2])

    def test_get_all_with_zero_limit(self):
        """Test retrieving items with a limit of zero."""
        # Adding sample items
        items = [
            {"id": f"{i}", "sort_key": "1", "value": Decimal(f"{i}.23")}
            for i in range(3)
        ]
        self.dynamodb_base.write_batch(items)

        # Call get_all with a limit of 0
        result = self.dynamodb_base.get_all(limit=0)
        self.assertEqual(result, [])

    def test_get_all_with_large_limit(self):
        """Test retrieving items with a limit greater than available items."""
        # Adding sample items
        items = [
            {"id": f"{i}", "sort_key": "1", "value": Decimal(f"{i}.23")}
            for i in range(3)
        ]
        self.dynamodb_base.write_batch(items)

        # Call get_all with a large limit (10)
        result = self.dynamodb_base.get_all(limit=10)
        self.assertEqual(len(result), len(items))
        self.assertEqual(result, items)

    def test_get_all_no_items(self):
        """Test retrieving items when there are no items in the table."""
        result = self.dynamodb_base.get_all()
        self.assertEqual(result, [])

    def test_get_all_handles_scan_error(self):
        """Test handling of an error during the scan operation."""
        # Mock scan to raise an exception
        self.dynamodb_base._table.scan = lambda *args, **kwargs: (_ for _ in ()).throw(
            Exception("DynamoDB scan error")
        )

        with self.assertRaises(Exception, msg="DynamoDB scan error"):
            self.dynamodb_base.get_all()

    def test_delete_item(self):
        """Test deleting an item from the DynamoDB table."""
        item = {"id": "123", "sort_key": "abc", "value": Decimal("1.23")}
        self.dynamodb_base.add(item)

        # Delete the item from DynamoDB
        # self.dynamodb_base._del_by_keys(
        #    primary_key_name="id", primary_key_value="123", sort_key="abc"
        # )
        self.dynamodb_base._del_by_keys("id", "123", "sort_key", "abc")

        # Attempt to get the deleted item
        table = self.dynamodb.Table(self.table_name)
        response = table.get_item(Key={"id": "123", "sort_key": "abc"})

        # Assert that the item is not found (i.e., it was deleted)
        self.assertNotIn("Item", response)

    def test_batch_write_items(self):
        """Test batch writing multiple items to the DynamoDB table."""
        items = [
            {"id": "1", "sort_key": "abc", "value": Decimal("10.1")},
            {"id": "2", "sort_key": "abc", "value": Decimal("20.2")},
            {"id": "3", "sort_key": "abc", "value": Decimal("30.3")},
        ]

        # Write the items in batch
        self.dynamodb_base.write_batch(items)

        # Fetch each item from the table and compare with the expected values
        table = self.dynamodb.Table(self.table_name)
        for item in items:
            response = table.get_item(
                Key={"id": item["id"], "sort_key": item["sort_key"]}
            )
            self.assertEqual(response["Item"], item)

    def test_convert_float_to_decimal(self):
        """Test that the float values are properly converted to Decimal."""
        item = {"id": "123", "float_value": 2.718, "nested": {"float_value": 3.14159}}
        converted_item = self.dynamodb_base._DynamoDBBase__convert_to_decimal(item)

        self.assertEqual(converted_item["float_value"], Decimal("2.718"))
        self.assertEqual(converted_item["nested"]["float_value"], Decimal("3.14159"))

    def test_convert_to_decimal_from_object(self):
        """Test converting an object with attributes to dictionary
        for Decimal conversion."""

        class SampleObject:
            def __init__(self):
                self.attr1 = 1.23
                self.attr2 = 4.56

        sample_object = SampleObject()
        result = self.dynamodb_base._DynamoDBBase__convert_to_decimal(sample_object)

        # Expected result should have float attributes converted to Decimal
        expected_result = {"attr1": Decimal("1.23"), "attr2": Decimal("4.56")}
        self.assertEqual(result, expected_result)

    def test_convert_to_decimal_float_input(self):
        """Test converting a single float value to Decimal."""
        float_value = 12.34567
        result = self.dynamodb_base._DynamoDBBase__convert_to_decimal(float_value)

        # The float value should be rounded and converted to Decimal
        expected_result = Decimal("12.34567")
        self.assertEqual(result, expected_result)

    def test_convert_to_decimal_from_list(self):
        """Test converting a list containing floats to a list with Decimals."""

        item = {"key1": [1.23, 4.56, {"nested_key": 7.89}]}
        result = self.dynamodb_base._DynamoDBBase__convert_to_decimal(item)

        # Expected result should have float values inside list converted to Decimal
        expected_result = {
            "key1": [Decimal("1.23"), Decimal("4.56"), {"nested_key": Decimal("7.89")}]
        }
        self.assertEqual(result, expected_result)

    def test_convert_to_decimal_nested_list(self):
        """Test converting nested lists containing floats to Decimals."""

        item = {"key1": [[1.23, 4.56], {"nested_key": [7.89, 10.11]}]}
        result = self.dynamodb_base._DynamoDBBase__convert_to_decimal(item)

        # Expected result should have float values inside nested lists
        # converted to Decimal
        expected_result = {
            "key1": [
                [Decimal("1.23"), Decimal("4.56")],
                {"nested_key": [Decimal("7.89"), Decimal("10.11")]},
            ]
        }
        self.assertEqual(result, expected_result)

    def test_convert_to_decimal_object_with_float(self):
        """Test converting an object with __dict__ attribute containing
        floats to Decimals."""
        obj = TestObject(123, 45.67)
        converted = self.dynamodb_base._DynamoDBBase__convert_to_decimal(obj)

        expected = {"attr1": 123, "attr2": Decimal("45.67")}
        self.assertEqual(converted, expected)

    def test_convert_to_decimal_mixed_nested_structures(self):
        """Test converting a complex nested structure with dictionaries,
        lists, and floats."""
        nested_item = {
            "key1": [
                {"nested_key1": 1.23, "nested_key2": {"inner_key": 4.56}},
                7.89,
                {"nested_key3": [{"deep_key": 10.11}, 12.34]},
            ],
            "key2": 45.67,
        }

        converted = self.dynamodb_base._DynamoDBBase__convert_to_decimal(nested_item)

        expected = {
            "key1": [
                {
                    "nested_key1": Decimal("1.23"),
                    "nested_key2": {"inner_key": Decimal("4.56")},
                },
                Decimal("7.89"),
                {"nested_key3": [{"deep_key": Decimal("10.11")}, Decimal("12.34")]},
            ],
            "key2": Decimal("45.67"),
        }
        self.assertEqual(converted, expected)

    def test_convert_to_decimal_object_in_nested_dict(self):
        """Test converting a nested structure with an object inside a dictionary."""
        nested_obj = {
            "key1": TestObject(100, 200.55),
            "key2": 300.75,
            "key3": [1.1, 2.2, {"deep_key": TestObject(300, 400.99)}],
        }

        converted = self.dynamodb_base._DynamoDBBase__convert_to_decimal(nested_obj)

        expected = {
            "key1": {"attr1": 100, "attr2": Decimal("200.55")},
            "key2": Decimal("300.75"),
            "key3": [
                Decimal("1.1"),
                Decimal("2.2"),
                {"deep_key": {"attr1": 300, "attr2": Decimal("400.99")}},
            ],
        }
        self.assertEqual(converted, expected)
