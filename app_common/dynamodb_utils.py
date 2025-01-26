"""
This module contains the DynamoDBBase class that handles common operations
for DynamoDB tables.
"""

from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

# A global resource used to interact with DynamoDB.
# Whereas it can be used as is, you may want to replace or mock this resource for
# development and testing purposes. In such scenarios, consider the following
# alternatives:
#
# 1. You can replace this resource via the ``replace_dynamodb_resource()`` method,
#    e.g.:
#    ```
#    new_dynamodb = boto3.resource("dynamodb", endpoint_url="http://localhost:8000")
#    replace_dynamodb_resource(new_dynamodb)
#    ```
#
# 2. You can mock this resource via the ``moto`` library to mock AWS services by
#    annotating the relevant methods with ``@mock_aws``. See:
#      https://pypi.org/project/moto/
#      http://docs.getmoto.org/en/latest/docs/getting_started.html
dynamodb = boto3.resource("dynamodb")


def replace_dynamodb_resource(new_dynamodb_resource):
    """
    Replaces the global ``dynamodb`` resource with the given resource.
    This is meant to be used mainly for testing purposes, e.g., to use a DynamoDB
    Local instance instead of the default one provided by the AWS environment:

    ```
    new_dynamodb = boto3.resource("dynamodb", endpoint_url="http://localhost:8000")
    replace_dynamodb_resource(new_dynamodb)
    ```
    """
    global dynamodb
    dynamodb = new_dynamodb_resource


def create_table_resource(
    table_name: str,
    partition_key_name: str,
    partition_key_attribute_type: str,
    sort_key_name: str,
    sort_key_attribute_type: str,
    global_secondary_index_name: str,
    global_secondary_index_partition_key_name: str,
    global_secondary_index_projection_type: str = "ALL",
    table_read_capacity_units: int = 1,
    table_write_capacity_units: int = 1,
    global_secondary_index_read_capacity_units: int = 1,
    global_secondary_index_write_capacity_units: int = 1,
    **kwargs,
):
    """
    Creates and returns a DynamoDB table resource via ``dynamodb.create_table()`` with
    the given parameters.
    This method is meant to be used mainly for testing purposes and is kept
    deliberately simple. If you need more complex logic -- say, for example,
    additional columns in ``AttributeDefinitions`` or multiple Global Secondary Indexes
    --, consider invoking ``dynamodb.create_table()`` directly.
    """

    # Handles the simpler case where there is no Global Secondary Index
    if not global_secondary_index_name:
        return dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": partition_key_name, "KeyType": "HASH"},
                {"AttributeName": sort_key_name, "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {
                    "AttributeName": partition_key_name,
                    "AttributeType": partition_key_attribute_type,
                },
                {
                    "AttributeName": sort_key_name,
                    "AttributeType": sort_key_attribute_type,
                },
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": table_read_capacity_units,
                "WriteCapacityUnits": table_write_capacity_units,
            },
            **kwargs,
        )

    # Handles the more complex case where there is a Global Secondary Index
    return dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": partition_key_name, "KeyType": "HASH"},
            {"AttributeName": sort_key_name, "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {
                "AttributeName": partition_key_name,
                "AttributeType": partition_key_attribute_type,
            },
            {"AttributeName": sort_key_name, "AttributeType": sort_key_attribute_type},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": global_secondary_index_name,
                "KeySchema": [
                    {
                        "AttributeName": global_secondary_index_partition_key_name,
                        "KeyType": "HASH",
                    },
                ],
                "Projection": {
                    "ProjectionType": global_secondary_index_projection_type,
                },
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": global_secondary_index_read_capacity_units,
                    "WriteCapacityUnits": global_secondary_index_write_capacity_units,
                },
            },
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": table_read_capacity_units,
            "WriteCapacityUnits": table_write_capacity_units,
        },
        **kwargs,
    )


class DynamoDBBase:
    """Handles common operations for DynamoDB tables."""

    def __init__(self, table_name):
        self._table_name = table_name
        self._table = dynamodb.Table(table_name)

    def recreate_table_resource(self):
        """
        Recreates the ``Table`` resource of this instance through the global
        ``dynamodb`` resource. This is meant to be used mainly for testing purposes,
        e.g., after replacing the global ``dynamodb`` resource to point to a DynamoDB
        Local instance instead of the default one provided by the AWS environment.
        """
        self._table = dynamodb.Table(self._table_name)

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
