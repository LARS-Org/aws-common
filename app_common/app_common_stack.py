"""
This module contains a common stack that ensures all Lambda functions
in the stack automatically have permission to publish to the ErrorHandlingTopic.
The stack also creates an SSM parameter to store the ErrorHandlingTopic ARN.
This can be used as a base class for other utility features to be added to a stack.
"""

import boto3
import jsii
from aws_cdk import Aspects, Duration, IAspect, RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_events as events
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_sns as sns
from aws_cdk import aws_ssm as ssm
from constructs import Construct, IConstruct

from app_common.app_utils import _do_log


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
        self.error_handling_topic_arn = self._get_or_create_sns_topic_arn(
            self._get_error_topic_name()
        )

        # Store the SNS topic ARN in SSM Parameter Store
        # So, each specialized stack is going to have its own parameter
        # retrieving the ARN of the ErrorHandlingTopic
        self._ensure_ssm_parameter(
            "ErrorHandlingTopic-ARN",
            self.error_handling_topic_arn,
        )

        # Apply the aspect to grant publish permissions to all Lambda functions
        Aspects.of(self).add(GrantPublishToSnsAspect(self.error_handling_topic_arn))

    def _ensure_ssm_parameter(
        self, parameter_name: str, value: str, custom_path: str = None, **kwargs
    ) -> None:
        """
        Creates an SSM parameter during the deployment process.

        :param parameter_name: The name of the SSM parameter.
        :param value: The value to set for the parameter.
        :param custom_path: Optional custom path for the parameter.
                            Defaults to the stack name if not provided.
        """
        # Use the custom path or default to the stack name
        custom_path = custom_path or self.stack_name

        if custom_path.startswith("/"):
            # Remove the leading slash
            custom_path = custom_path[1:]

        if parameter_name.startswith("/"):
            # Remove the leading slash
            parameter_name = parameter_name[1:]

        # Construct the full parameter name
        full_parameter_name = f"/{custom_path}/{parameter_name}"

        # Create the SSM parameter
        ssm.StringParameter(
            self,
            f"{parameter_name.replace('/', '_')}_Parameter",  # Unique ID
            parameter_name=full_parameter_name,
            string_value=value,
            **kwargs,
        )

        self.do_log(title="SSM Parameter Created/Updated", obj=full_parameter_name)

    @staticmethod
    def _get_or_create_sns_topic_arn(topic_name: str, ensure_creation=True) -> str:
        """
        Retrieves the ARN of an SNS topic by name, creating the topic
        if it does not exist.
        Automatically escalates permissions if required.

        :param topic_name: The name of the SNS topic.
        :param ensure_creation: If False, raises an error if the topic doesn't exist.
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
        if ensure_creation:
            AppCommonStack.do_log(obj=f"Ensuring SNS topic '{topic_name}' exists...")
            create_response = sns_client.create_topic(Name=topic_name)
            AppCommonStack.do_log(
                obj=(
                    f"Successfully ensured topic '{topic_name}'."
                    f" ARN: {create_response['TopicArn']}"
                )
            )
            return create_response["TopicArn"]
        else:
            # If automatic creation is disabled, assume the topic exists
            AppCommonStack.do_log(
                obj=(
                    f"Checking if topic '{topic_name}' " "exists without creating it..."
                )
            )
            return topic_arn

    @staticmethod
    def _get_sns_topic_arn(topic_name: str) -> str:
        """
        Retrieves the ARN of an SNS topic based on its name.

        :param topic_name: The name of the SNS topic.
        :return: The ARN of the SNS topic.
        :raises ValueError: If the topic is not found.
        """
        return AppCommonStack._get_or_create_sns_topic_arn(
            topic_name, ensure_creation=False
        )

    def _get_or_create_sns_topic(self, topic_name: str) -> sns.Topic:
        """
        Retrieves an SNS topic by name, creating the topic if it does not exist.
        """
        return sns.Topic.from_topic_arn(
            self,
            f"{self.stack_name}-{topic_name}",  # Unique ID for the topic
            self._get_or_create_sns_topic_arn(topic_name),
        )

    def _get_or_create_sns_topic_with_sms_param(
        self, topic_name: str, sufix="-ARN"
    ) -> sns.Topic:
        """
        Retrieves an SNS topic by name, creating the topic if it does not exist.
        The ARN of the topic is stored in SSM Parameter Store.
        """
        sns_topic = self._get_or_create_sns_topic(topic_name)
        param_name = f"{topic_name}{sufix}"
        self._ensure_ssm_parameter(param_name, sns_topic.topic_arn)
        return sns_topic

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
        return self._get_or_create_sns_topic_arn(self._get_error_topic_name())

    def _get_error_topic(self) -> sns.Topic:
        """
        Retrieves the SNS topic to which error notifications are sent.
        """
        return self._get_or_create_sns_topic_with_sms_param(
            self._get_error_topic_name()
        )

    def _grant_ssm_parameter_access(
        self, lambda_function: _lambda.Function, param_full_path: str
    ):
        """
        Grants permission to a Lambda function to read an SSM parameter.

        :param lambda_function: The Lambda function to grant access.
        :param parameter_full_path: The full path of the SSM parameter.
        """
        if param_full_path.startswith("/"):
            # Remove the leading "/" if present
            param_full_path = param_full_path[1:]

        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[
                    (
                        f"arn:aws:ssm:{self.region}:{self.account}"
                        f":parameter/{param_full_path}"
                    )
                ],
            )
        )

    def _grant_send_email_permissions(
        self, lambda_function: _lambda.Function, resources=None
    ):
        """
        Grants permission to a Lambda function to send emails using Amazon SES.

        :param lambda_function: The Lambda function to grant access.
        """
        if resources is None:
            # If no resources are provided, grant permission to
            # send emails to any address
            resources = ["*"]

        lambda_function.add_to_role_policy(
            statement=iam.PolicyStatement(
                actions=["ses:SendEmail"],
                resources=resources,
            )
        )

    def _create_lambda(
        self,
        name: str,
        handler: str,
        environment: dict = None,
        duration_seconds: int = 30,
        from_asset: str = "lambdas",
        runtime=_lambda.Runtime.PYTHON_3_11,
        **kwargs,
    ) -> _lambda.Function:
        """
        Utility method to create a Lambda function with the specified configuration.
        """
        lambda_obj = _lambda.Function(
            self,
            name,
            function_name=f"{self.stack_name}-{name}",
            runtime=runtime,
            handler=handler,
            code=_lambda.Code.from_asset(from_asset),
            environment=environment,
            timeout=Duration.seconds(duration_seconds),
            **kwargs,
        )

        self.do_log(f"Created Lambda function {name}")

        return lambda_obj

    @staticmethod
    def do_log(obj, title: str = None):
        """
        Utility method to log an object.
        """
        _do_log(obj=obj, title=title)

    def _create_dynamodb_table(
        self,
        table_name: str,
        pk_name: str,
        pk_type: dynamodb.AttributeType,
        sk_name: str = None,
        sk_type: dynamodb.AttributeType = None,
        removal_policy: RemovalPolicy = RemovalPolicy.RETAIN,
        **kwargs,
    ) -> dynamodb.Table:
        """
        Creates a DynamoDB table with the specified parameters.
        """
        new_table = dynamodb.Table(
            self,
            table_name,
            partition_key=dynamodb.Attribute(name=pk_name, type=pk_type),
            sort_key=(
                dynamodb.Attribute(name=sk_name, type=sk_type)
                if sk_name and sk_type
                else None
            ),
            table_name=table_name,
            removal_policy=removal_policy,
            **kwargs,
        )

        self.do_log(f"Created DynamoDB table {table_name}")

        return new_table

    def _get_event_bus_name(self) -> str:
        """ "
        Returns the name of the FlowOrchestrator EventBridge event bus.
        That can be overridden in subclasses to use a different bus.
        """
        return "FlowOrchestratorEventBus"

    def _get_or_create_event_bus(self):
        """
        Returns the EventBridge event bus for the FlowOrchestrator.
        If the bus does not exist, it will be created.
        """
        # Name of the EventBus
        event_bus_name = self._get_event_bus_name()

        # Check if the EventBus already exists
        try:
            event_bus = events.EventBus.from_event_bus_name(
                self, event_bus_name, event_bus_name
            )
        except Exception as e:
            # If it doesn't exist, create a new one
            self.do_log(
                title="Error when trying to get the EventBus. Creating a new one.",
                obj=str(e),
            )
            event_bus = events.EventBus(
                self, event_bus_name, event_bus_name=event_bus_name
            )

        self.do_log(f"EventBus loaded successfully: {event_bus.event_bus_name}")

        # Register the EventBus name in SSM Parameter Store
        self._ensure_ssm_parameter(
            parameter_name="EventBusName", value=event_bus_name, custom_path="global"
        )

        return event_bus
