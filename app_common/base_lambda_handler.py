"""
This module contains the base class for Lambda handlers.
"""

import base64
import json
import os
import traceback
from abc import ABC, abstractmethod

import boto3
from app_common.app_utils import do_log


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

    def _on_error(self, e):
        """
        Handles errors that occurred during a lambda function invocation. The
        parameter ``e`` is usually an exception instance with information on
        what caused the error.
        """
        # TODO: #13 implement a better error handling mechanism
        # For now, just print the exception and send an email. This could be
        # extended to log to an external system.
        error_message = f"BaseLambdaHandler::OnError():: Error occurred:\n{e}"
        traceback_info = traceback.format_exc()
        print(error_message)
        print(traceback_info)
        # lambda_name = "not set"
        # if "AWS_LAMBDA_FUNCTION_NAME" in os.environ:
        #     # this prevents errors when for some reason
        #     # the environment variable is not set by AWS
        #     lambda_name = str(os.environ["AWS_LAMBDA_FUNCTION_NAME"])

        # try send email to admin
        # try:
        #     # self.event, self.context, self.body was setted in __init__ and __call__ methods
        #     email_util.send_email(
        #         "Error in Lambda - " + lambda_name,
        #         "<b>Error msg:</b><br>"
        #         + error_message
        #         + "<br><br><b>Traceback Info:</b><br>"
        #         + traceback_info
        #         + "<br><br><b>Event:</b><br>"
        #         + str(self.event)
        #         + "<br><br><b>Context:</b><br>"
        #         + str(self.context)
        #         + "<br><br><b>Body:</b><br>"
        #         + str(self.body),
        #     )
        # except Exception as email_error:  # pylint: disable=broad-except
        #     # using a generic exception here because we don't want to fail
        #     print("Error sending email", email_error)

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

        print("Running before_handle()...")

    def _after_handle(self):
        """
        Performs tasks that should be run after the main lambda function
        processing in handle(). This method is invoked by ``_do_the_job()`` in
        this class. The default implementation does nothing, and is meant to be
        overridden by subclasses.
        """

        print("Running after_handle()...")

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
            if len(self.event["Records"]) > 0 and "body" in self.event["Records"][0]:
                raw_body = self.event["Records"][0]["body"]

        self.body = raw_body

        if not raw_body:
            return None

        if isinstance(self.body, dict):
            return self.body
        # else: try to parse as json

        try:
            self.body = json.loads(raw_body)
        except Exception as e:
            print("** error parsing body as json", e)
            # Use raw body if not JSON
            return raw_body

        return self.body

    def _log_basic_info(self):
        """
        Logs basic information about the lambda invocation, such as the
        `event`, `context` and `body` parameters received from AWS.
        """
        do_log(self.event, title="*** Event")
        do_log(self.context, title="*** Context")
        do_log(self.body, title="*** Body")

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

        print("** Finishing the lambda execution")

        if isinstance(job_return, dict) and "statusCode" in job_return:
            # If the return is a response object, return it
            return job_return
        # else: return a 200 OK response
        return self.response(message=job_return)

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

        # this method is called by the __call__ method
        try:
            if not self._security_check():
                # if the security check fails, do nothing
                return
            # else: it is ok to proceed
            self._before_handle()
            print("** before_handle() is done.")
            job_return = None
            job_return = self._handle()
            print("** handle() is done.")
            self._after_handle()
            print("** after_handle() is done.")
        except Exception as e:
            self._on_error(e)
            print("** on_error() is done.")

        self._account_execution_costs()
        return job_return

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
    def send_message_to_sqs(queue_url, message_body, message_group_id="same", verbose=True) -> dict:
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
            message_body = json.dumps(message_body)

        if verbose:
            do_log(f"** send_message_to_sqs: queue_url{queue_url}\nmessage_body{message_body}\nmessage_group_id{message_group_id}")
        # Initialize the SQS client
        sqs_client = boto3.client("sqs")

        # Send the message
        response = sqs_client.send_message(QueueUrl=queue_url, 
                                           MessageBody=message_body, 
                                           MessageGroupId=message_group_id # required for FIFO queues
                                           )

        if verbose:
            do_log(f"** send_message_to_sqs: response{response}")

        return response

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
        if isinstance(payload, dict):
            payload = json.dumps(payload)

        # Set invocation type based on async_invoke
        invocation_type = "Event" if async_invoke else "RequestResponse"

        print(
            "** Invoking Lambda: function_name",
            function_name,
            "\ninvocation_type",
            invocation_type,
            "\npayload",
            payload,
        )

        # Invoke the Lambda function
        response = lambda_client.invoke(
            FunctionName=function_name, InvocationType=invocation_type, Payload=payload
        )

        # If synchronous invocation, read and return the Lambda function response payload
        if not async_invoke:
            return json.loads(response["Payload"].read())
        else:
            return response

    @staticmethod
    def response(status_code: int=200, 
                 headers={'Content-Type': 'application/json'},
                 message:str="OK", 
                 body=None) -> dict:
        """
        Returns a response object that can be returned by a Lambda handler.
        """
        # TODO: #14 Review the implementation of this method. Is it necessary message and body?
        return {
        'statusCode': status_code,
        'headers': headers,
        'message': message,
        'body': body
        }

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
