"""
This module contains a common stack that ensures all Lambda functions
in the stack automatically have permission to publish to the ErrorHandlingTopic.
The stack also creates an SSM parameter to store the ErrorHandlingTopic ARN.
This can be used as a base class for other utility features to be added to a stack.
"""

import boto3
import jsii
from app_utils import _do_log
from aws_cdk import Aspects, IAspect, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_ssm as ssm
from constructs import Construct, IConstruct


@jsii.implements(IAspect)
class GrantPublishToSnsAspect:
    """
    Aspect that automatically grants permissions for all Lambda functions
    in the stack to publish to a specific SNS topic.
    """

    def __init__(self, error_handling_topic_arn: str) -> None:
        self.error_handling_topic_arn = error_handling_topic_arn

    def visit(self, node: IConstruct) -> None:
        """
        Visit each node in the construct tree and attach
        the necessary permissions.
        """
        if isinstance(node, _lambda.Function):
            _do_log(obj=f"Granting publish permissions to Lambda: {node.function_name}")
            node.add_to_role_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["sns:Publish"],
                    resources=[self.error_handling_topic_arn],
                )
            )
            # Add the topic ARN to the lambda environment variables
            node.add_environment("ERROR_TOPIC_ARN", self.error_handling_topic_arn)


class AppCommonStack(Stack):
    """
    A common stack that ensures all Lambda functions in the stack automatically
    have permission to publish to the ErrorHandlingTopic.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create an SNS topic for error handling
        self.error_handling_topic_arn = self.get_or_create_sns_topic_arn(
            self._get_error_topic_name()
        )

        # Store the SNS topic ARN in SSM Parameter Store
        self._ensure_ssm_parameter(
            "error_handling_topic_arn",
            self.error_handling_topic_arn,
            custom_path="app_common",
        )

        # Apply the aspect to grant publish permissions to all Lambda functions
        Aspects.of(self).add(GrantPublishToSnsAspect(self.error_handling_topic_arn))

    def _ensure_ssm_parameter(
        self, parameter_name: str, value: str, custom_path=None
    ) -> None:
        """
        Ensures that an SSM parameter exists with the specified name and value.
        If the parameter already exists with a different value, it logs a warning.
        If the parameter does not exist, it creates the parameter.

        :param parameter_name: The name of the SSM parameter.
        :param value: The value to set for the parameter if it doesn't exist.
        """
        if not custom_path:
            # use the stack name as the path
            custom_path = self.stack_name

        # update the parameter name with the custom path
        full_parameter_name = f"/{custom_path}/{parameter_name}"

        try:
            # Check if the parameter already exists
            existing_value = ssm.StringParameter.value_from_lookup(
                self, full_parameter_name
            )
            _do_log(
                obj=(
                    f"Found existing SSM parameter: "
                    f"{full_parameter_name} "
                    f"with value: {existing_value}"
                )
            )

            # Check if the existing value matches the desired value
            if existing_value != value:
                _do_log(
                    obj=(
                        f"SSM parameter '{full_parameter_name}' exists with"
                        f" a different value: {existing_value}.\n"
                        f"Expected: {value}. Please update it manually if needed."
                    )
                )
        except Exception as e:
            _do_log(
                obj=(
                    f"SSM parameter '{full_parameter_name}' not found."
                    f"\nCreating it. Error: {e}"
                )
            )
            # Create the parameter if it doesn't exist
            ssm.StringParameter(
                self,
                f"{parameter_name.replace('/', '_')}_Parameter",
                parameter_name=full_parameter_name,
                string_value=value,
            )

    @staticmethod
    def get_or_create_sns_topic_arn(topic_name: str, automatic_creation=True) -> str:
        """
        Retrieves the ARN of an SNS topic by name, creating the topic
        if it does not exist.
        Automatically escalates permissions if required.

        :param topic_name: The name of the SNS topic.
        :param automatic_creation: If False, raises an error if the topic doesn't exist.
        :return: The ARN of the SNS topic.
        """

        sns_client = boto3.client("sns")
        sts_client = boto3.client("sts")

        # Get account details to construct the ARN
        account_id = sts_client.get_caller_identity()["Account"]
        region = sns_client.meta.region_name

        # Construct the topic ARN
        topic_arn = f"arn:aws:sns:{region}:{account_id}:{topic_name}"

        # Try to create the topic directly (idempotent operation)
        if automatic_creation:
            _do_log(obj=f"Ensuring SNS topic '{topic_name}' exists...")
            create_response = sns_client.create_topic(Name=topic_name)
            _do_log(
                obj=(
                    f"Successfully ensured topic '{topic_name}'."
                    f" ARN: {create_response['TopicArn']}"
                )
            )
            return create_response["TopicArn"]
        else:
            # If automatic creation is disabled, assume the topic exists
            _do_log(
                obj=(
                    f"Checking if topic '{topic_name}' " "exists without creating it..."
                )
            )
            return topic_arn

    @staticmethod
    def get_sns_topic_arn(topic_name: str) -> str:
        """
        Retrieves the ARN of an SNS topic based on its name.

        :param topic_name: The name of the SNS topic.
        :return: The ARN of the SNS topic.
        :raises ValueError: If the topic is not found.
        """
        return AppCommonStack.get_or_create_sns_topic_arn(
            topic_name, automatic_creation=False
        )

    def _get_error_topic_name(self) -> str:
        """
        The name of the SNS topic to which error notifications are sent.
        This can be overridden in subclasses to provide a custom error topic name.
        """
        return "ErrorNotificationsTopic"

    def _get_error_topic_arn(self) -> str:
        """
        Retrieves the ARN of the SNS topic to which error notifications are sent.
        This method is used internally by the base class to send error notifications.
        If the topic does not exist, it is created automatically.
        """
        return self.get_or_create_sns_topic_arn(self._get_error_topic_name())
