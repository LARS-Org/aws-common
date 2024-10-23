import base64
import json
import os
import traceback
from unittest.mock import MagicMock, patch

import pytest

from app_common.base_lambda_handler import BaseLambdaHandler


# Create a concrete subclasses for testing purposes
class DefaultLambdaHandler(BaseLambdaHandler):
    def _handle(self):
        # Simple implementation for testing
        return "Default handle executed"


class TestLambdaHandler(BaseLambdaHandler):
    def _handle(self):
        # Simple implementation for testing
        return "Test handle executed"

    def _security_check(self) -> bool:
        # Overridden implementation for testing purposes
        return False

    def _before_handle(self):
        # Simple overridden implementation for testing
        print("Overridden before_handle() executed")

    def _after_handle(self):
        # Simple overridden implementation for testing
        print("Overridden after_handle() executed")

    def _do_the_job(self):
        # Simple implementation for testing
        return "Job done"

    def _account_execution_costs(self):
        # Overridden implementation for testing accounting of execution costs
        print("Accounting execution costs...")


class SecurityFailingTestLambdaHandler(TestLambdaHandler):
    def _security_check(self) -> bool:
        print("Security check called in SecurityFailingTestLambdaHandler.")
        return False


class TestBaseLambdaHandler:
    def setup_method(self):
        """
        Set up a new instance of TestLambdaHandler before each test.
        """
        self.handler = TestLambdaHandler()

    def test_initialization(self):
        """
        Test that the TestLambdaHandler initializes with None for event, context,
        body, and headers.
        """
        assert self.handler.event is None
        assert self.handler.context is None
        assert self.handler.body is None
        assert self.handler.headers is None

    @patch("builtins.print")
    def test_on_error(self, mock_print):
        """
        Test that the _on_error method correctly handles exceptions and prints
        the error and traceback.
        """
        error_message = "Test Exception"

        try:
            raise Exception(error_message)
        except Exception as e:
            traceback_info = (
                traceback.format_exc()
            )  # Capture the traceback within the except block
            self.handler._on_error(e, traceback_info)

        # Check that the error message is printed
        mock_print.assert_any_call(
            f"BaseLambdaHandler::OnError():: Error occurred:\n{error_message}"
        )

        # Check if the debug statements are showing correct values
        mock_print.assert_any_call(traceback_info)

    def test_handle(self):
        """
        Test that the _handle method in the TestLambdaHandler works as expected.
        """
        result = self.handler._handle()
        assert result == "Test handle executed"

    def test_security_check_default(self):
        """
        Test that the default _security_check method returns True.
        """
        base_handler = DefaultLambdaHandler()
        assert base_handler._security_check() is True

    def test_security_check_overridden(self):
        """
        Test that the overridden _security_check method in TestLambdaHandler
        returns False.
        """
        assert self.handler._security_check() is False

    @patch("builtins.print")
    def test_before_handle_default(self, mock_print):
        """
        Test that the default _before_handle method prints the expected message.
        """
        base_handler = DefaultLambdaHandler()
        base_handler._before_handle()

        # Check that the default message is printed
        mock_print.assert_any_call("Running before_handle()...")

    @patch("builtins.print")
    def test_before_handle_overridden(self, mock_print):
        """
        Test that the overridden _before_handle method in TestLambdaHandler
        prints the overridden message.
        """
        self.handler._before_handle()

        # Check that the overridden message is printed
        mock_print.assert_any_call("Overridden before_handle() executed")

    @patch("builtins.print")
    def test_after_handle_default(self, mock_print):
        """
        Test that the default _after_handle method prints the expected message.
        """
        base_handler = DefaultLambdaHandler()
        base_handler._after_handle()

        # Check that the default message is printed
        mock_print.assert_any_call("Running after_handle()...")

    @patch("builtins.print")
    def test_after_handle_overridden(self, mock_print):
        """
        Test that the overridden _after_handle method in TestLambdaHandler
        prints the overridden message.
        """
        self.handler._after_handle()

        # Check that the overridden message is printed
        mock_print.assert_any_call("Overridden after_handle() executed")

    def test_handle_not_implemented(self):
        """
        Test that the abstract _handle method raises NotImplementedError
        when not overridden.
        """

        class IncompleteHandler(BaseLambdaHandler):
            pass

        with pytest.raises(
            TypeError,
            match=(
                "Can't instantiate abstract class IncompleteHandler"
                " with abstract method _handle"
            ),
        ):
            incomplete_handler = IncompleteHandler()
            incomplete_handler._handle()

    def test_load_body_from_event_none_event(self):
        """
        Test that _load_body_from_event returns None when event is None.
        """
        self.handler.event = None
        result = self.handler._load_body_from_event()
        assert result is None

    def test_load_body_from_event_existing_body(self):
        """
        Test that _load_body_from_event returns existing body if body is not None.
        """
        self.handler.event = {"test": "value"}
        self.handler.body = {"existing": "body"}
        result = self.handler._load_body_from_event()
        assert result == {"existing": "body"}

    def test_load_body_from_event_plain_body(self):
        """
        Test that _load_body_from_event extracts plain body from event.
        """
        self.handler.event = {"body": "test body"}
        result = self.handler._load_body_from_event()
        assert result == "test body"

    def test_load_body_from_event_base64_encoded_body(self):
        """
        Test that _load_body_from_event correctly decodes a Base64-encoded body.
        """
        encoded_body = base64.b64encode(b"test body").decode("utf-8")
        self.handler.event = {"body": encoded_body, "isBase64Encoded": True}
        result = self.handler._load_body_from_event()
        assert result == b"test body"

    def test_load_body_from_event_sqs_record(self):
        """
        Test that _load_body_from_event extracts body from SQS record.
        """
        self.handler.event = {"Records": [{"body": "sqs message body"}]}
        result = self.handler._load_body_from_event()
        assert result == "sqs message body"

    def test_load_body_from_event_sns_record(self):
        """
        Test that _load_body_from_event extracts message from SNS record.
        """
        self.handler.event = {"Records": [{"Sns": {"Message": "sns message body"}}]}
        result = self.handler._load_body_from_event()
        assert result == "sns message body"

    @patch("builtins.print")
    def test_load_body_from_event_invalid_json(self, mock_print):
        """
        Test that _load_body_from_event handles non-JSON body gracefully.
        """
        self.handler.event = {"body": "not a json"}
        result = self.handler._load_body_from_event()
        assert result == "not a json"
        mock_print.assert_any_call(
            "** error parsing body as json", mock_print.call_args[0][1]
        )

    def test_load_body_from_event_valid_json(self):
        """
        Test that _load_body_from_event parses a valid JSON body correctly.
        """
        self.handler.event = {"body": json.dumps({"key": "value"})}
        result = self.handler._load_body_from_event()
        assert result == {"key": "value"}

    def test_load_body_from_event_empty_body(self):
        """
        Test that _load_body_from_event returns None when the body is empty.
        """
        self.handler.event = {"body": ""}
        result = self.handler._load_body_from_event()
        assert result is None

    def test_load_body_from_event_empty_sqs_record(self):
        """
        Test that _load_body_from_event returns None when the SQS record body is empty.
        """
        self.handler.event = {"Records": [{"body": ""}]}
        result = self.handler._load_body_from_event()
        assert result is None

    def test_load_body_from_event_empty_sns_message(self):
        """
        Test that _load_body_from_event returns None when the SNS message is empty.
        """
        self.handler.event = {"Records": [{"Sns": {"Message": ""}}]}
        result = self.handler._load_body_from_event()
        assert result is None

    def test_load_body_from_event_none_raw_body(self):
        """
        Test that _load_body_from_event returns None when raw_body is None.
        """
        self.handler.event = {"body": None}
        result = self.handler._load_body_from_event()
        assert result is None

    def test_load_body_from_event_plain_dict_body(self):
        """
        Test that _load_body_from_event returns the body when it is a dictionary.
        """
        self.handler.event = {"body": {"key": "value"}}
        result = self.handler._load_body_from_event()
        assert result == {"key": "value"}
        assert isinstance(result, dict)

    def test_load_body_from_event_parsed_json_dict(self):
        """
        Test that _load_body_from_event returns the parsed body when it is a valid
        JSON string that results in a dictionary.
        """
        json_body = json.dumps({"key": "value"})
        self.handler.event = {"body": json_body}
        result = self.handler._load_body_from_event()
        assert result == {"key": "value"}
        assert isinstance(result, dict)

    def test_load_body_from_event_sqs_record_as_dict(self):
        """
        Test that _load_body_from_event returns the body as a dictionary from
        SQS records.
        """
        self.handler.event = {"Records": [{"body": '{"key": "value"}'}]}
        result = self.handler._load_body_from_event()
        assert result == {"key": "value"}
        assert isinstance(result, dict)

    def test_load_body_from_event_sns_message_as_dict(self):
        """
        Test that _load_body_from_event returns the body as a dictionary from
        SNS message.
        """
        self.handler.event = {"Records": [{"Sns": {"Message": '{"key": "value"}'}}]}
        result = self.handler._load_body_from_event()
        assert result == {"key": "value"}
        assert isinstance(result, dict)

    @patch("app_common.base_lambda_handler.do_log")
    def test_log_basic_info(self, mock_do_log):
        """
        Test that _log_basic_info calls do_log with event, context, and body.
        """
        self.handler.event = {"key": "event_value"}
        self.handler.context = {"key": "context_value"}
        self.handler.body = {"key": "body_value"}

        self.handler._log_basic_info()

        # Verify that do_log was called with the correct parameters
        mock_do_log.assert_any_call(self.handler.event, title="*** Event")
        mock_do_log.assert_any_call(self.handler.context, title="*** Context")
        mock_do_log.assert_any_call(self.handler.body, title="*** Body")

    @patch("app_common.base_lambda_handler.do_log")
    @patch("builtins.print")
    def test_call_method(self, mock_print, mock_do_log):
        """
        Test that the __call__ method sets attributes, calls logging methods,
        and returns 200 OK response.
        """
        # Mock the event and context
        event = {"body": '{"key": "value"}', "headers": {"header_key": "header_value"}}
        context = {"context_key": "context_value"}

        # Call the handler
        response = self.handler(event, context)

        # Check that the event, context, body, and headers are set correctly
        assert self.handler.event == event
        assert self.handler.context == context
        assert self.handler.body == {"key": "value"}
        assert self.handler.headers == {"header_key": "header_value"}

        # Verify that basic info was logged
        mock_do_log.assert_any_call(self.handler.event, title="*** Event")
        mock_do_log.assert_any_call(self.handler.context, title="*** Context")
        mock_do_log.assert_any_call(self.handler.body, title="*** Body")

        # Verify that _do_the_job was called
        assert response == self.handler.response(message="Job done")

        # Verify that the finishing print statement is called
        mock_print.assert_any_call("** Finishing the lambda execution")

    @patch("app_common.base_lambda_handler.do_log")
    @patch("builtins.print")
    def test_call_method_with_custom_response(self, mock_print, mock_do_log):
        """
        Test that the __call__ method returns a custom response if _do_the_job
        returns a response object.
        """
        # Mock the event and context
        event = {"body": '{"key": "value"}', "headers": {"header_key": "header_value"}}
        context = {"context_key": "context_value"}

        # Mock the _do_the_job to return a response object
        self.handler._do_the_job = MagicMock(
            return_value={"statusCode": 200, "body": "Custom response"}
        )

        # Call the handler
        response = self.handler(event, context)

        # Verify that the custom response is returned
        assert response == {"statusCode": 200, "body": "Custom response"}

        # Verify that the finishing print statement is called
        mock_print.assert_any_call("** Finishing the lambda execution")

    def test_do_the_job_success_flow(self):
        """Test the entire flow of _do_the_job when all methods execute successfully."""
        result = self.handler._do_the_job()

        # Assert that the final return value is from `_handle()`
        assert result == "Job done"

    @patch("builtins.print")
    def test_account_execution_costs_default(self, mock_print):
        """
        Test that the default _account_execution_costs method does nothing.
        """
        base_handler = DefaultLambdaHandler()
        base_handler._account_execution_costs()

        # Ensure no print statement or action is performed
        mock_print.assert_not_called()

    @patch("builtins.print")
    def test_account_execution_costs_overridden(self, mock_print):
        """
        Test that the overridden _account_execution_costs method in TestLambdaHandler
        prints the expected message.
        """
        self.handler._account_execution_costs()

        # Verify that the overridden message is printed
        mock_print.assert_any_call("Accounting execution costs...")

    def test_get_temp_dir_path(self):
        """
        Test that _get_temp_dir_path returns the expected path.
        """
        assert self.handler._get_temp_dir_path() == "/tmp/"

    @patch("boto3.resource")
    @patch("os.remove")
    def test_upload_to_bucket(self, mock_os_remove, mock_boto3_resource):
        """
        Test that upload_to_bucket uploads the file and optionally removes
        the local file.
        """
        bucket_mock = MagicMock()
        mock_boto3_resource.return_value.Bucket.return_value = bucket_mock

        bucket_name = "test-bucket"
        local_file_path = "test.txt"
        bucket_obj_name = "test/test.txt"

        # Test with remove_local_file=True
        self.handler.upload_to_bucket(
            bucket_name, local_file_path, bucket_obj_name, remove_local_file=True
        )
        bucket_mock.upload_file.assert_called_once_with(
            local_file_path, bucket_obj_name
        )
        mock_os_remove.assert_called_once_with(local_file_path)

        # Test with remove_local_file=False
        mock_os_remove.reset_mock()
        self.handler.upload_to_bucket(
            bucket_name, local_file_path, bucket_obj_name, remove_local_file=False
        )
        mock_os_remove.assert_not_called()

    @patch("boto3.resource")
    def test_download_object_from_bucket(self, mock_boto3_resource):
        """
        Test that download_object_from_bucket downloads the file from S3 to the
        specified local path.
        """
        bucket_mock = MagicMock()
        mock_boto3_resource.return_value.Bucket.return_value = bucket_mock

        bucket_name = "test-bucket"
        bucket_obj_name = "test/test.txt"
        local_file_path = "test.txt"

        self.handler.download_object_from_bucket(
            bucket_name, bucket_obj_name, local_file_path
        )
        bucket_mock.download_file.assert_called_once_with(
            bucket_obj_name, local_file_path
        )

    @patch("boto3.client")
    @patch("app_common.base_lambda_handler.do_log")
    def test_send_message_to_sqs(self, mock_do_log, mock_boto3_client):
        """
        Test that send_message_to_sqs sends a message to the SQS queue and
        logs the operation.
        """
        sqs_client_mock = MagicMock()
        mock_boto3_client.return_value = sqs_client_mock
        sqs_client_mock.send_message.return_value = {"MessageId": "12345"}

        queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"
        message_body = "Test message"
        message_group_id = "group1"

        # Call the method
        response = self.handler.send_message_to_sqs(
            queue_url, message_body, message_group_id, verbose=True
        )

        # Check that the message was sent
        sqs_client_mock.send_message.assert_called_once_with(
            QueueUrl=queue_url,
            MessageBody=message_body,
            MessageGroupId=message_group_id,
        )

        # Verify that logging occurred
        mock_do_log.assert_any_call(
            f"** send_message_to_sqs: queue_url {queue_url}\n"
            f"message_body {message_body}\nmessage_group_id {message_group_id}"
        )
        mock_do_log.assert_any_call(f"** send_message_to_sqs: response{response}")

        # Check the response
        assert response == {"MessageId": "12345"}

    @patch("boto3.client")
    @patch("app_common.base_lambda_handler.do_log")
    def test_send_message_to_sqs_non_string_body(self, mock_do_log, mock_boto3_client):
        """
        Test that send_message_to_sqs correctly handles non-string message bodies
        by converting them to JSON.
        """
        sqs_client_mock = MagicMock()
        mock_boto3_client.return_value = sqs_client_mock
        sqs_client_mock.send_message.return_value = {"MessageId": "12345"}

        queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"
        message_body = {"key": "value"}
        message_group_id = "group1"

        # Call the method
        response = self.handler.send_message_to_sqs(
            queue_url, message_body, message_group_id, verbose=True
        )

        # Check that the message was sent
        sqs_client_mock.send_message.assert_called_once_with(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body),
            MessageGroupId=message_group_id,
        )

        # Verify that logging occurred
        mock_do_log.assert_any_call(
            f"** send_message_to_sqs: queue_url {queue_url}\n"
            f"message_body {json.dumps(message_body)}\n"
            f"message_group_id {message_group_id}"
        )
        mock_do_log.assert_any_call(f"** send_message_to_sqs: response{response}")

        # Check the response
        assert response == {"MessageId": "12345"}

    @patch("boto3.client")
    @patch("app_common.base_lambda_handler.do_log")
    def test_publish_to_sns(self, mock_do_log, mock_boto3_client):
        """
        Test that publish_to_sns sends a message to the SNS topic and logs
        the operation.
        """
        sns_client_mock = MagicMock()
        mock_boto3_client.return_value = sns_client_mock
        sns_client_mock.publish.return_value = {"MessageId": "12345"}

        topic_arn = "arn:aws:sns:us-east-1:123456789012:test-topic"
        message = "Test message"
        subject = "Test subject"

        # Call the method
        response = self.handler.publish_to_sns(
            topic_arn, message, subject, verbose=True
        )

        # Check that the message was published
        sns_client_mock.publish.assert_called_once_with(
            TopicArn=topic_arn,
            Message=message,
            Subject=subject,
        )

        # Verify that logging occurred
        mock_do_log.assert_any_call(f"Message published to SNS topic: {topic_arn}")
        mock_do_log.assert_any_call(message, title="Message")

        # Check the response
        assert response == {"MessageId": "12345"}

    @patch("boto3.client")
    @patch("app_common.base_lambda_handler.do_log")
    def test_publish_to_sns_non_string_message(self, mock_do_log, mock_boto3_client):
        """
        Test that publish_to_sns correctly handles non-string message bodies
        by converting them to JSON.
        """
        sns_client_mock = MagicMock()
        mock_boto3_client.return_value = sns_client_mock
        sns_client_mock.publish.return_value = {"MessageId": "12345"}

        topic_arn = "arn:aws:sns:us-east-1:123456789012:test-topic"
        message = {"key": "value"}
        subject = "Test subject"

        # Call the method
        response = self.handler.publish_to_sns(
            topic_arn, message, subject, verbose=True
        )

        # Check that the message was published
        sns_client_mock.publish.assert_called_once_with(
            TopicArn=topic_arn,
            Message=json.dumps(message),
            Subject=subject,
        )

        # Verify that logging occurred
        mock_do_log.assert_any_call(f"Message published to SNS topic: {topic_arn}")
        mock_do_log.assert_any_call(json.dumps(message), title="Message")

        # Check the response
        assert response == {"MessageId": "12345"}

    @patch("app_common.base_lambda_handler.do_log")
    def test_do_log_wrapper(self, mock_do_log):
        """
        Test that the do_log wrapper method correctly calls the do_log function
        from app_utils.
        """
        obj = {"key": "value"}
        title = "Test Title"
        log_limit = 1000

        # Call the method
        self.handler.do_log(obj, title=title, log_limit=log_limit)

        # Verify that the do_log function was called with the correct arguments
        mock_do_log.assert_called_once_with(obj, title=title, log_limit=log_limit)

    @patch("boto3.client")
    @patch("builtins.print")
    def test_invoke_lambda_async(self, mock_print, mock_boto3_client):
        """
        Test that invoke_lambda correctly invokes a Lambda function asynchronously
        and logs the operation.
        """
        lambda_client_mock = MagicMock()
        mock_boto3_client.return_value = lambda_client_mock
        lambda_client_mock.invoke.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 202}
        }

        function_name = "test_lambda_function"
        payload = {"key": "value"}

        # Call the method asynchronously
        response = self.handler.invoke_lambda(function_name, payload, async_invoke=True)

        # Check that the Lambda function was invoked with the "Event"
        # invocation type for async calls
        lambda_client_mock.invoke.assert_called_once_with(
            FunctionName=function_name,
            InvocationType="Event",
            Payload=json.dumps(payload),
        )

        # Verify that logging occurred
        mock_print.assert_any_call(
            "** Invoking Lambda: function_name",
            function_name,
            "\ninvocation_type",
            "Event",
            "\npayload",
            json.dumps(payload),
        )

        # Check the response
        assert response == {"ResponseMetadata": {"HTTPStatusCode": 202}}

    @patch("boto3.client")
    def test_invoke_lambda_empty_function_name(self, mock_boto3_client):
        """
        Test that invoke_lambda returns None if function_name is empty or None.
        """
        function_name = ""
        payload = {"key": "value"}

        # Call the method with an empty function name
        response = self.handler.invoke_lambda(function_name, payload)

        # Ensure that the client was not invoked
        mock_boto3_client.assert_not_called()

        # Ensure response is None
        assert response is None

        # Test with None as the function_name
        response = self.handler.invoke_lambda(None, payload)
        assert response is None
        mock_boto3_client.assert_not_called()

    @patch("boto3.client")
    @patch("builtins.print")
    def test_invoke_lambda_non_dict_payload(self, mock_print, mock_boto3_client):
        """
        Test that invoke_lambda correctly handles non-dictionary
        payloads by converting them to JSON.
        """
        lambda_client_mock = MagicMock()
        mock_boto3_client.return_value = lambda_client_mock
        lambda_client_mock.invoke.return_value = {
            "Payload": MagicMock(
                read=MagicMock(return_value=json.dumps({"result": "success"}))
            )
        }

        function_name = "test_lambda_function"
        payload = ["item1", "item2"]

        # Call the method
        response = self.handler.invoke_lambda(function_name, payload)

        # Check that the payload was converted to JSON
        lambda_client_mock.invoke.assert_called_once_with(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )

        # Verify that logging occurred
        mock_print.assert_any_call(
            "** Invoking Lambda: function_name",
            function_name,
            "\ninvocation_type",
            "RequestResponse",
            "\npayload",
            json.dumps(payload),
        )

        # Check the response
        assert response == {"result": "success"}

    @patch("boto3.client")
    @patch("builtins.print")
    def test_invoke_lambda_no_payload(self, mock_print, mock_boto3_client):
        """
        Test that invoke_lambda correctly handles invocation without a payload.
        """
        lambda_client_mock = MagicMock()
        mock_boto3_client.return_value = lambda_client_mock
        lambda_client_mock.invoke.return_value = {
            "Payload": MagicMock(
                read=MagicMock(return_value=json.dumps({"result": "success"}))
            )
        }

        function_name = "test_lambda_function"

        # Call the method without a payload
        response = self.handler.invoke_lambda(function_name, async_invoke=False)

        # Check that the Lambda function was invoked with no payload
        lambda_client_mock.invoke.assert_called_once_with(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=None,
        )

        # Verify that logging occurred
        mock_print.assert_any_call(
            "** Invoking Lambda: function_name",
            function_name,
            "\ninvocation_type",
            "RequestResponse",
            "\npayload",
            None,
        )

        # Check the response
        assert response == {"result": "success"}

    def test_response(self):
        """
        Test the response method to verify the returned response object is correct.
        """
        response = self.handler.response(
            status_code=201,
            headers={"Content-Type": "application/json"},
            message="Created",
            body={"key": "value"},
        )
        expected_response = {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "message": "Created",
            "body": {"key": "value"},
        }
        assert response == expected_response

    def test_response_default(self):
        """
        Test the response method with default parameters.
        """
        response = self.handler.response()
        expected_response = {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "message": "OK",
            "body": None,
        }
        assert response == expected_response

    def test_body_or_none_with_body(self):
        """
        Test the body_or_none method when the event contains a body.
        """
        event = {"body": "test_body"}
        assert self.handler.body_or_none(event) == "test_body"

    def test_body_or_none_without_body(self):
        """
        Test the body_or_none method when the event does not contain a body.
        """
        event = {}
        assert self.handler.body_or_none(event) is None

    @patch.dict(os.environ, {"TEST_ENV_VAR": "test_value"})
    def test_get_env_var_existing(self):
        """
        Test get_env_var method when the environment variable is set.
        """
        assert self.handler.get_env_var("TEST_ENV_VAR") == "test_value"

    def test_get_env_var_default(self):
        """
        Test get_env_var method when the environment variable is not set,
        using a default value.
        """
        assert (
            self.handler.get_env_var("NON_EXISTENT_VAR", "default_value")
            == "default_value"
        )

    def test_get_env_var_none(self):
        """
        Test get_env_var method when the environment variable is not set,
        without a default value.
        """
        assert self.handler.get_env_var("NON_EXISTENT_VAR") is None