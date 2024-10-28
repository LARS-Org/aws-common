import decimal
import json
import os

import boto3
import pytest
from moto import mock_aws

from app_common.base_lambda_handler import BaseLambdaHandler


@pytest.fixture(scope="class")
def setup_s3():
    """Fixture to mock S3 and create a bucket."""
    with mock_aws():
        s3 = boto3.resource("s3")
        bucket_name = "test-bucket"
        s3.create_bucket(Bucket=bucket_name)
        yield bucket_name, s3


@pytest.fixture(scope="class")
def setup_sqs():
    """Fixture to mock SQS and create a FIFO queue with
    ContentBasedDeduplication enabled."""
    with mock_aws():
        sqs = boto3.resource("sqs")
        queue = sqs.create_queue(
            QueueName="test-queue.fifo",
            Attributes={
                "FifoQueue": "true",
                "ContentBasedDeduplication": "true",
            },
        )
        yield queue.url, sqs


@pytest.fixture(scope="class")
def setup_sns():
    """Fixture to mock SNS and create a topic."""
    with mock_aws():
        sns = boto3.client("sns")
        topic_arn = sns.create_topic(Name="test-topic")["TopicArn"]
        yield topic_arn, sns


@pytest.fixture(scope="function")
def mock_event():
    """Fixture to create a mock Lambda event."""
    return {
        "body": json.dumps({"key": "value"}),
        "headers": {"Authorization": "Bearer token"},
    }


@pytest.fixture(scope="function")
def mock_context():
    """Fixture to create a mock Lambda context."""
    return {}  # Mock context


class TestBaseLambdaHandler:
    """Class for BaseLambdaHandler integration tests."""

    def test_lambda_invocation(self, mock_event, mock_context):
        """Test the entire Lambda invocation process."""

        class TestLambdaHandler(BaseLambdaHandler):
            def _handle(self):
                return {"statusCode": 200, "body": "Success"}

        handler = TestLambdaHandler()

        response = handler(mock_event, mock_context)

        assert response["statusCode"] == 200
        assert response["body"] == "Success"

    def test_upload_to_bucket(self, setup_s3):
        """Test S3 file upload and removal."""
        bucket_name, s3 = setup_s3
        local_file_path = "/tmp/test_file.txt"

        # Create a temporary file to upload
        with open(local_file_path, "w") as f:
            f.write("Sample data")

        BaseLambdaHandler.upload_to_bucket(
            bucket_name=bucket_name,
            local_file_path=local_file_path,
            bucket_obj_name="test_file.txt",
            remove_local_file=True,
        )

        # Assert file is uploaded in S3
        bucket = s3.Bucket(bucket_name)
        objs = list(bucket.objects.all())
        assert len(objs) == 1
        assert objs[0].key == "test_file.txt"

        # Assert local file is removed
        assert not os.path.exists(local_file_path)

    def test_send_message_to_sqs(self, setup_sqs):
        """Test sending a message to SQS with ContentBasedDeduplication enabled."""
        queue_url, sqs = setup_sqs
        message_body = {"amount": decimal.Decimal("10.50")}

        # Call the send_message_to_sqs method
        response = BaseLambdaHandler.send_message_to_sqs(
            queue_url=queue_url,
            message_body=message_body,
            message_group_id="test_group",  # Required for FIFO queues
            verbose=True,
        )

        assert response is not None
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

        # Retrieve the message and verify its contents
        messages = sqs.Queue(queue_url).receive_messages()
        assert len(messages) == 1
        assert json.loads(messages[0].body)["amount"] == "10.50"

    def test_publish_to_sns(self, setup_sns):
        """Test publishing a message to SNS."""
        topic_arn, sns = setup_sns
        message = {"content": "Test message"}

        response = BaseLambdaHandler.publish_to_sns(
            topic_arn=topic_arn, message=message, subject="Test Subject"
        )

        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_get_env_var(self):
        """Test retrieving environment variables."""
        os.environ["TEST_VAR"] = "test_value"

        result = BaseLambdaHandler.get_env_var("TEST_VAR")
        assert result == "test_value"

        # Test default value
        result = BaseLambdaHandler.get_env_var("NON_EXISTENT_VAR", "default")
        assert result == "default"

    def test_security_check(self, mock_event, mock_context):
        """Test that the security check prevents processing when it returns False."""

        class TestLambdaHandler(BaseLambdaHandler):
            def _security_check(self):
                return False  # Simulate security failure

            def _handle(self):
                raise AssertionError(
                    "This should not be called when security check fails"
                )

        handler = TestLambdaHandler()
        response = handler(mock_event, mock_context)

        assert "message" not in response
        assert response["statusCode"] == 200
