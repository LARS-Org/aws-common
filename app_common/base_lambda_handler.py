"""
This module contains the base class for Lambda handlers.
"""

import base64
import json
import os
import traceback
from abc import ABC, abstractmethod
from functools import lru_cache

try:
    import boto3
except ImportError as exc:
    raise RuntimeError(
        "boto3 is not available; ensure it is provided by the runtime environment."
    ) from exc

from app_common import app_utils


class BaseLambdaHandler(ABC):
    """
    BaseLambdaHandler is a class that can be used as a base for Lambda
    handlers. It provides a few useful features such as exception handling and
    execution hooks. At the very least, subclasses must override the
    ``handle()`` method in order to service lambda function invocations.

    This class relies on some core attributes:

    - ``context``: this is the ``context`` parameter received from AWS when a
        lambda function is invoked, and has to do AWS infrastructure;
    - ``event``: this is the ``event`` parameter received from AWS when a
        lambda function is invoked, and contains data about the fact or
        situation that generated the invocation (for example, a message sent
        by a user in Telegram). This attribute can be handled as a dictionary;
    - ``body``: this is extracted from the ``event`` parameter and contains
        the main information about the fact or situation that generated the
        invocation (for example, the text of a message sent by a user in
        Telegram, as well as information about the user itself). This attribute
        can be handled as a dictionary.
    """

    def __init__(self):
        """
        Initializes the core class attributes ``context``, ``event`` and
        ``body`` with ``None``.
        """
        self.event = None
        self.context = None
        self.body = None
        self.headers = None
        self.job_return = None

    @staticmethod
    def extract_error_details(exception: Exception) -> dict:
        """
        Extracts error details from the exception.
        """
        # Extract the stack trace
        stack_trace = "".join(traceback.format_tb(exception.__traceback__))
        # Extract the error message
        error_message = str(exception)
        # Extract the error type
        error_type = exception.__class__.__name__

        # Traverse to the deepest frame in the traceback
        tb = exception.__traceback__
        deepest_frame = None
        while tb:
            deepest_frame = tb.tb_frame
            tb = tb.tb_next

        if deepest_frame:
            # Extract details from the deepest frame
            component = deepest_frame.f_globals.get("__name__", "unknown")
            location = deepest_frame.f_code.co_name
            line_number = deepest_frame.f_lineno
        else:
            # Fallback if no frame is found
            component = "unknown"
            location = "unknown"
            line_number = "unknown"

        return {
            "stack_trace": stack_trace,
            "error_message": error_message,
            "error_type": error_type,
            "component": component,
            "location": location,
            "line_number": line_number,
        }

    def _on_error(self, error_details: dict):
        """
        Handles errors that occur during lambda execution by logging the error details.

        This method is called when an exception occurs during lambda processing.
        It receives a dictionary containing details about the error and logs them
        using the do_log method.

        It can be overridden for a custom behaviour.
        """
        # Publish the exception on the custom event bus
        try:
            # Just print the exception.
            self.do_log(title="Exception Found", obj=error_details)
            self.publish_to_custom_event_bus(
                message=error_details,
                detail_type="NewExceptionRaised",
                source="BaseLambdaHandler",
            )
        except Exception as e:
            self.do_log(
                title="Error while publishing to custom event bus",
                obj={"exception": str(e)},
            )

    def _security_check(self) -> bool:
        """
        Performs a security check to verify that the current lambda function
        invocation is valid from a security standpoint. Must return ``True``
        in case the lambda function invocation is considered valid, and
        ``False`` otherwise. This method is invoked by ``_do_the_job()`` in
        this class. The default implementation simply returns ``True``, and is
        meant to be overridden by subclasses.
        """

        return True  # default implementation

    def _before_handle(self):
        """
        Performs tasks that should be run before the main lambda function
        processing in handle(). This method is invoked by ``_do_the_job()``
        in this class. The default implementation does nothing, and is meant
        to be overridden by subclasses.
        """

        self.do_log("Running before_handle()...")

    def _after_handle(self):
        """
        Performs tasks that should be run after the main lambda function
        processing in handle(). This method is invoked by ``_do_the_job()`` in
        this class. The default implementation does nothing, and is meant to be
        overridden by subclasses.
        """

        self.do_log("Running after_handle()...")

    @abstractmethod
    def _handle(self):
        """
        The main method that handles the lambda function invocation. This
        method is invoked by ``_do_the_job()`` in this class. The default
        implementation simply raises an exception, and is meant to be
        overridden by subclasses.
        """

    def _load_body_from_event(self):
        """
        Attempts to extract the body from the `event` parameter received from
        AWS upon invocation of the Lambda function. Special logic is necessary
        because the event body can be in different places depending on the
        event type. After extracting the event body, this method stores the
        resulting information in the `body` attribute and returns it to the
        caller. This method only attempts the extraction when the `body`
        attribute contains `None`; in case the `body` attribute already
        contains information obtained from a previous invocation, the attribute
        is returned immediately.
        """

        if self.event is None:
            return None

        if self.body is not None:
            return self.body

        raw_body = self.event

        if "body" in self.event:
            raw_body = self.event["body"]
            if self.event.get("isBase64Encoded", False):
                # Decode the body if it is Base64-encoded
                raw_body = base64.b64decode(self.event["body"])
        elif "Records" in self.event:
            if len(self.event["Records"]) > 0:
                if "body" in self.event["Records"][0]:
                    raw_body = self.event["Records"][0]["body"]
                elif (
                    "Sns" in self.event["Records"][0]
                    and "Message" in self.event["Records"][0]["Sns"]
                ):
                    raw_body = self.event["Records"][0]["Sns"]["Message"]

        self.body = raw_body

        if not raw_body:
            return None

        if isinstance(self.body, dict):
            return self.body
        # else: try to parse as json

        try:
            self.body = json.loads(raw_body)
        except (json.JSONDecodeError, TypeError, ValueError):
            self.do_log(title="** Error parsing body as json", obj=raw_body)
            # Use raw body if not JSON
            return raw_body

        return self.body

    def _log_basic_info(self):
        """
        Logs basic information about the lambda invocation, such as the
        `event`, `context` and `body` parameters received from AWS.
        """
        self.do_log(self.event, title="*** Event", deep_limit=1)
        self.do_log(self.context, title="*** Context", deep_limit=1)
        self.do_log(self.body, title="*** Body", deep_limit=5)

    def __call__(self, event, context):
        """
        Performs all the tasks required to service a lambda function
        invocation, as follows:

        - Initializes the ``event`` and ``context`` class attributes with the
          parameters received from AWS;
        - Initializes the ``body`` class attribute by extracting the relevant
          information from the ``event`` parameter;
        - Invokes ``_do_the_job()`` to perform the actual processing required
          to service the lambda invocation. Please see the documentation on
          that method to learn more about execution hooks;
        - Returns a ``"200 OK"`` HTTP response. This is the case even when some
          error occurs, as returning anything other than ``"200"`` may cause AWS
          to try invoking the lambda function again with the same parameters.
        """

        # initialize the class attributes
        self.event = event
        self.context = context
        self.body = self._load_body_from_event()
        self.headers = event["headers"] if "headers" in event else {}

        # log basic information about the lambda invocation
        self._log_basic_info()

        # Call the _do_the_job method synchronously
        job_return = None
        job_return = self._do_the_job()

        self.do_log("** Finishing the lambda execution")

        if isinstance(job_return, dict) and "statusCode" in job_return:
            # If the return is a response object, return it
            return job_return
        # else: return a 200 OK response
        return self.response(message=job_return)

    def _get_sns_topic_listeners(self) -> list:
        """
        Returns a list of SNS topics to which the lambda function should
        publish messages. This method is invoked by the ``__call__()`` method
        in this class. The default implementation returns an empty list, and is
        meant to be overridden by subclasses.
        """
        # Returning a empty list in the default implementation.
        # Override this method to return a list of SNS topics, if needed.
        return []

    def _get_custom_event_bus_name(self):
        """
        Returns the name of the custom EventBridge event bus.
        """
        return self.get_env_var("CUSTOM_EVENT_BUS_NAME")

    def publish_to_event_bus(
        self,
        event_bus_name: str,
        message: dict,
        detail_type: str,
        source: str = None,
    ):
        """
        Publish a message to an Amazon EventBridge event bus.

        Args:
            event_bus_name (str): The name of the custom EventBridge event bus
                                  to publish to.
            message (dict): The message payload to publish. If dict, will be converted
                            to JSON string.
            detail_type (str): The detail-type field that will be attached to the event.
            source (str, optional): The source field that will be attached to the event.
                                    Defaults to class name if not provided.

        Returns:
            dict: Response from EventBridge PutEvents API containing fields like
                 'Entries' and 'FailedEntryCount'.

        Raises:
            RuntimeError: If any events fail to publish (FailedEntryCount > 0).
        """
        eventbridge_client = boto3.client("events")

        if not source:
            # source equal the current class name
            source = self.__class__.__name__

        if isinstance(message, dict):
            message = self.json_dumps(message)

        event = {
            "Source": source,
            "DetailType": detail_type,
            "Detail": message,
            "EventBusName": event_bus_name,
        }

        response = eventbridge_client.put_events(Entries=[event])

        if response["FailedEntryCount"] > 0:
            raise RuntimeError(f"Failed to publish event: {response['Entries']}")

        self.do_log(
            title=f"Event published to EventBridge Bus {event_bus_name}", obj=response
        )
        # remove the Detail field from the event to avoid logging it again
        event.pop("Detail")
        self.do_log(event)

        return response

    def publish_to_custom_event_bus(
        self, message: dict, detail_type: str, source: str = None
    ):
        """
        Publishes a message to the custom event bus.
        """
        self.publish_to_event_bus(
            event_bus_name=self._get_custom_event_bus_name(),
            message=message,
            detail_type=detail_type,
            source=source,
        )

    def _do_the_job(self):
        """
        Performs the actual processing required to service a lambda function
        invocation. This method is invoked by the ``__call__()`` method. It
        invokes ``security_check()`` and returns immediately in case that
        method returns ``False`` (for example, when a Telegram bot on our side
        is being contacted by another bot, or when there is a DDoS attack in
        progress). If ``security_check()`` returns ``True``, however, this
        method invokes the below methods:

        - ``before_handle()``
        - ``handle()``
        - ``after_handle()``
        - ``account_execution_costs()``

        If an exception occurs in either ``before_handle()``, ``handle()`` or
        ``after_handle()``, the resulting exception instance is passed to the
        ``on_error()`` method. Finally, this method invokes
        ``account_execution_costs()`` even when an invocation to the previously
        mentioned methods fails.
        """
        self.job_return = None
        # this method is called by the __call__ method
        try:
            if not self._security_check():
                # if the security check fails, do nothing
                return
            # else: it is ok to proceed
            self._before_handle()
            self.do_log("** before_handle() is done.")
            self.job_return = self._handle()
            self.do_log("** handle() is done.")
            self._after_handle()
            self.do_log("** after_handle() is done.")
        except Exception as e:
            # an exception occurred during the processing of the lambda
            # set the job_return to the error message
            self.job_return = {
                "error": str(e),
                "class_name": self.__class__.__name__,
                "payload": self.body,
                # AWS LambdaContext info
                "lambda_context": {
                    "aws_request_id": self.context.aws_request_id,
                    "log_group_name": self.context.log_group_name,
                    "log_stream_name": self.context.log_stream_name,
                    "function_name": self.context.function_name,
                    "function_version": self.context.function_version,
                    "invoked_function_arn": self.context.invoked_function_arn,
                    "memory_limit_in_mb": self.context.memory_limit_in_mb,
                    "remaining_time_in_millis": (
                        self.context.get_remaining_time_in_millis()
                    ),
                },
            }
            # Add more details
            self.job_return.update(self.extract_error_details(e))

            # call the on_error method
            self._on_error(self.job_return)

        self._account_execution_costs()
        return self.job_return

    def _account_execution_costs(self):
        """
        Performs accounting of execution costs for a lambda function
        invocation. This method is invoked by ``_do_the_job()`` in this class
        at the end of the lambda execution. The default implementation does
        nothing, and is meant to be overridden by subclasses.
        """
        return  # do nothing while this feature is not implemented

    @staticmethod
    def _get_temp_dir_path():
        """
        Returns the path to the temporary directory used by this lambda
        handler. The returned path ends with a directory separator.
        """

        return "/tmp/"

    @staticmethod
    def upload_to_bucket(
        bucket_name, local_file_path, bucket_obj_name, remove_local_file=True
    ):
        """
        Uploads the contents of a local file to an object inside an AWS S3
        bucket, optionally removing the local file after the upload.
        """

        bucket = boto3.resource("s3").Bucket(bucket_name)
        bucket.upload_file(local_file_path, bucket_obj_name)
        if remove_local_file:
            os.remove(local_file_path)

    @staticmethod
    def download_object_from_bucket(bucket_name, bucket_obj_name, local_file_path):
        """
        Given the identification of an object inside an AWS S3 bucket,
        downloads its contents to a local file.
        """

        bucket = boto3.resource("s3").Bucket(bucket_name)
        bucket.download_file(bucket_obj_name, local_file_path)

    @staticmethod
    def send_message_to_sqs(
        queue_url, message_body, message_group_id="same", verbose=True
    ) -> dict:
        """
        Send a message to an SQS queue.

        Parameters:
        - queue_url (str): The URL of the SQS queue.
        - message_body (str): The message body you want to send.
        - message_group_id (str, optional): The message group ID to use for
            FIFO queues. Default is "same".

        Returns:
        - dict: Response from the `send_message` SQS API call.
        """
        if message_body is None:
            return None
        if not isinstance(message_body, str):
            message_body = BaseLambdaHandler.json_dumps(message_body, indent=None)

        if verbose:
            BaseLambdaHandler.do_log(
                f"** send_message_to_sqs: queue_url {queue_url}\n"
                f"message_body {message_body}\n"
                f"message_group_id {message_group_id}"
            )

        # Initialize the SQS client
        sqs_client = boto3.client("sqs")

        # Send the message
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body,
            MessageGroupId=message_group_id,  # required for FIFO queues
        )

        if verbose:
            BaseLambdaHandler.do_log(f"** send_message_to_sqs: response{response}")

        return response

    @staticmethod
    def publish_to_sns(topic_arn: str, message, subject=None, verbose=True):
        """
        Send a message to an SNS topic.

        Parameters:
        - topic_arn (str): The ARN of the SNS topic.
        - message (str): The message body you want to send.
        - subject (str, optional): The subject of the message. Default is None.
        """
        sns_client = boto3.client("sns")
        _return = None
        if not isinstance(message, str):
            # If the message is not a string, convert it to JSON
            message = BaseLambdaHandler.json_dumps(message, indent=None)

        if subject:
            _return = sns_client.publish(
                TopicArn=topic_arn, Message=message, Subject=subject
            )
        else:
            _return = sns_client.publish(TopicArn=topic_arn, Message=message)

        if verbose:
            BaseLambdaHandler.do_log(
                obj=message, title=f"Message published to SNS topic: {topic_arn}"
            )

        return _return

    @staticmethod
    def do_log(obj, title=None, line_len_limit: int = 100, deep_limit: int = 3):
        """
        Wrapper function to call the do_log() function from the app_utils module.
        """
        app_utils._do_log(
            obj, title=title, line_len_limit=line_len_limit, deep_limit=deep_limit
        )

    @staticmethod
    def invoke_lambda(function_name, payload=None, async_invoke=False):
        """
        Invoke an AWS Lambda function.

        Parameters:
        - function_name (str): Name or ARN of the Lambda function to invoke.
        - payload (dict or str, optional): Data payload to send to the Lambda
          function.
        - async_invoke (bool, optional): If True, invoke the Lambda function
          asynchronously. Default is False (synchronous).

        Returns:
        - dict or str: If synchronous, returns the response payload. If
          asynchronous, returns the invocation response.
        """
        if not function_name:
            return None

        # Initialize the Lambda client
        lambda_client = boto3.client("lambda")

        # Ensure payload is a JSON string
        if isinstance(payload, dict) or (
            payload is not None and not isinstance(payload, str)
        ):
            payload = BaseLambdaHandler.json_dumps(payload, indent=None)

        # Set invocation type based on async_invoke
        invocation_type = "Event" if async_invoke else "RequestResponse"

        BaseLambdaHandler.do_log(
            title=(
                f"** Invoking Lambda: {function_name} "
                f"- Invocation_type: {invocation_type}"
            ),
            obj=payload,
        )

        # Invoke the Lambda function
        response = lambda_client.invoke(
            FunctionName=function_name, InvocationType=invocation_type, Payload=payload
        )

        # If synchronous invocation, read and return the Lambda function
        # response payload
        if not async_invoke:
            return json.loads(response["Payload"].read())
        else:
            return response

    @staticmethod
    def response(
        status_code=200,
        headers=None,
        body=None,
        message=None,
    ):
        """
        Returns a response object that can be returned by a Lambda handler.
        """
        if headers is None:
            headers = {"Content-Type": "application/json"}

        dict_response = {
            "statusCode": status_code,
            "headers": headers,
            "body": json.dumps(body, cls=app_utils.DecimalEncoder) if body else None,
        }

        # Add a message to the response if provided and body is empty
        # This is useful to avoid problems with API Gateway
        if not body and message:
            dict_response["message"] = message

        return dict_response

    @staticmethod
    def body_or_none(event: dict):
        """
        Returns the body of the event or None if it is not present.
        """
        if event and "body" in event:
            return event["body"]
        return None

    @staticmethod
    def get_env_var(name: str, default_value: str = None):
        """
        Returns the value of an environment variable or a default value if the
        variable is not set.
        """
        return os.environ.get(name, default_value)

    @staticmethod
    @lru_cache(maxsize=None)
    def get_ssm_parameter_cached(
        parameter_name: str, with_decryption: bool = False
    ) -> str:
        """
        Retrieves the value of an SSM parameter with caching using lru_cache.

        :param parameter_name: The name of the SSM parameter.
        :param with_decryption: Whether to decrypt the parameter if it's encrypted.
        :return: The value of the SSM parameter.
        :raises Exception: If the parameter cannot be retrieved.
        """
        try:
            # Fetch the parameter from SSM
            ssm_client = BaseLambdaHandler._get_ssm_client()
            response = ssm_client.get_parameter(
                Name=parameter_name,
                WithDecryption=with_decryption,
            )
            return response["Parameter"]["Value"]
        except Exception as e:
            print(f"Error retrieving SSM parameter '{parameter_name}': {e}")
            raise ValueError(f"Failed to retrieve parameter: {parameter_name}") from e

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_ses_client():
        """
        Retrieves the SES client.
        Uses lru_cache to cache the client instance, avoiding multiple connections.
        """
        return boto3.client("ses")

    def send_email_notification(
        self, from_email: str, to_email: str, subject: str, body: str
    ):
        """
        Sends an email notification using Amazon SES.
        """
        # Retrieve the SES client
        ses_client = self._get_ses_client()

        self.do_log(f"Sending email From: {from_email}, To: {to_email}")

        # Send the email
        response = ses_client.send_email(
            Source=from_email,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body}},
            },
        )

        # Log the response
        self.do_log(f"Email sent. Message ID: {response['MessageId']}")

        return response

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_ssm_client():
        """
        Retrieves the SSM client.
        Uses lru_cache to cache the client instance, avoiding multiple connections.
        """
        return boto3.client("ssm")

    @staticmethod
    def json_dumps(data, indent=4, cls=app_utils.DecimalEncoder) -> str:
        """
        Utility method to serialize data to JSON, including Decimal values.
        """
        return app_utils.json_dumps(data, indent=indent, cls=cls)

    def _get_path_parameter(self, parameter_name: str) -> str:
        """
        Extracts the path parameter with the given name from the event dictionary.
        """
        return self.event["pathParameters"][parameter_name]
