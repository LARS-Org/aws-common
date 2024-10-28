"""
This module contains the DynamoDBBase class that handles common operations
for DynamoDB tables.
"""

from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")


class DynamoDBBase:
    """Handles common operations for DynamoDB tables."""

    def __init__(self, table_name):
        self._table = dynamodb.Table(table_name)

    def __convert_to_decimal(self, item):
        """
        Convert all float values in the given dictionary or list to Decimals
        compatible with DynamoDB.

        DynamoDB requires numerical values to be expressed as Decimals instead
        of floats, as it does not support the float data type directly. This
        function ensures that all floating-point numbers are converted to
        Decimal, which is the correct numerical type for DynamoDB.

        Args:
            item (dict, list, float or object): The dictionary, list, float, or object
            containing the data to be converted and inserted into DynamoDB.

        Returns:
            dict, list, Decimal, or original value: A new dictionary or list with all
            float values converted to Decimals, suitable for DynamoDB storage, or the
            original value.
        """
        if isinstance(item, dict):
            # Recursively convert all dictionary values
            return {k: self.__convert_to_decimal(v) for k, v in item.items()}
        elif isinstance(item, list):
            # Recursively convert all items in the list
            return [self.__convert_to_decimal(i) for i in item]
        elif isinstance(item, float):
            # Convert floats to Decimals
            return Decimal(str(round(item, 10)))
        elif hasattr(item, "__dict__"):
            # If item has a __dict__ attribute, treat it like a dictionary
            return {k: self.__convert_to_decimal(v) for k, v in item.__dict__.items()}
        else:
            # If the item is not a dict, list, or float, return it as-is
            return item

    def add(self, item):
        """Adds an item to the DynamoDB table."""
        self._table.put_item(Item=self.__convert_to_decimal(item))
        return item

    def update(self, key, update_expression, expression_attribute_values):
        """Updates an item in the DynamoDB table.
        The UpdateItem operation updates an existing item,
        or adds a new item to the table if it does not already exist.
        """
        self._table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=self.__convert_to_decimal(
                expression_attribute_values
            ),
        )
        return key

    def get_all(self, limit=100) -> list:
        """
        Retrieves all objects from the DynamoDB table, considering the limit.
        """
        if limit == 0:
            return []  # Return an empty list if limit is zero

        return self._table.scan(Limit=limit)["Items"]

    def _get_by_keys(
        self,
        primary_key_name,
        primary_key_value,
        sort_key_name=None,
        sort_key_value=None,
        index_name=None,
        scan_index_forward=True,
        limit=None,
    ):
        """
        Retrieves items by primary key and optional sort key.

        - Use query instead of scan for better performance when only primary
          key is provided.
        - Ensure that your table's key design and indexes support your query patterns
          for efficiency.
        """
        # Start with the primary key condition
        key_condition = Key(primary_key_name).eq(primary_key_value)

        # If a sort key is provided, add it to the condition
        if sort_key_name and sort_key_value:
            key_condition &= Key(sort_key_name).eq(sort_key_value)

        # Prepare the query parameters
        query_params = {
            "KeyConditionExpression": key_condition,
            "ScanIndexForward": scan_index_forward,
        }

        # Conditionally add IndexName if it's provided
        if index_name is not None:
            query_params["IndexName"] = index_name

        # Conditionally add Limit if it's provided
        if limit is not None:
            query_params["Limit"] = limit

        # Perform the query with the constructed parameters
        response = self._table.query(**query_params)

        return response["Items"]

    def get_by_partition_key(self, pk_name, pk_value):
        """
        Retrieves items by partition key.

        Args: pk_name (str): The name of the partition key.
                pk_value (str): The value of the partition key.
        Returns: list: A list of items matching the given partition key.
        """
        return self._get_by_keys(primary_key_name=pk_name, primary_key_value=pk_value)

    def _get_last_items_by_key(self, key_name, key_value, k, scan_index_forward=False):
        """
        Get the last items by a key.
        """
        response = self._table.query(
            KeyConditionExpression=Key(key_name).eq(key_value),
            ScanIndexForward=scan_index_forward,
            Limit=k,
        )

        return response["Items"][:k] if response["Items"] else []

    def _get_batch_writer(self):
        """
        Utilitary method to get the batch writer.
        """
        return self._table.batch_writer()

    def write_batch(self, items):
        """
        Utilitary method to batch write items.
        """
        with self._get_batch_writer() as batch:
            for item in items:
                batch.put_item(Item=self.__convert_to_decimal(item))

    def _del_by_keys(
        self, primary_key_name, primary_key_value, sort_key_name, sort_key_value
    ):
        """
        Deletes an item from the DynamoDB table by primary key and sort key.
        """
        self._table.delete_item(
            Key={primary_key_name: primary_key_value, sort_key_name: sort_key_value}
        )
