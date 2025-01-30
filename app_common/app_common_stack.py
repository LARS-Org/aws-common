"""
This module contains a common stack that ensures all Lambda functions
in the stack automatically have permission to publish to the ErrorHandlingTopic.
The stack also creates an SSM parameter to store the ErrorHandlingTopic ARN.
This can be used as a base class for other utility features to be added to a stack.
"""

import jsii
from aws_cdk import Aspects, Duration, IAspect, RemovalPolicy, Stack
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_events as events
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as logs
from aws_cdk import aws_sns as sns
from aws_cdk import aws_ssm as ssm
from constructs import Construct, IConstruct

from app_common.app_utils import _do_log


@jsii.implements(IAspect)
class GrantPublishToCustomEventBusAspect:
    """
    Aspect that automatically grants permissions for all Lambda functions
    in the stack to publish to a specific EventBridge event bus.
    """

    def __init__(self, custom_event_bus_name: str) -> None:
        self.custom_event_bus_name = custom_event_bus_name

    def visit(self, node: IConstruct) -> None:
        """
        Visit each node in the construct tree and attach
        the necessary permissions.
        """
        if isinstance(node, _lambda.Function):
            _do_log(
                obj=f"Granting publish permissions to Lambda: {node.function_name} "
                f"to publish messages on the {self.custom_event_bus_name} event bus"
            )
            node.add_to_role_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["events:PutEvents"],
                    resources=[
                        f"arn:aws:events:{Stack.of(node).region}"
                        f":{Stack.of(node).account}"
                        f":event-bus/{self.custom_event_bus_name}"
                    ],
                )
            )
            # Add the custom event bus name as a environment variable
            node.add_environment("CUSTOM_EVENT_BUS_NAME", self.custom_event_bus_name)


class AppCommonStack(Stack):
    """
    A common stack that ensures all Lambda functions in the stack automatically
    have permission to publish to the ErrorHandlingTopic.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if self._get_custom_event_bus_name():
            Aspects.of(self).add(
                GrantPublishToCustomEventBusAspect(self._get_custom_event_bus_name())
            )

    def _get_default_param_custom_path(self):
        """
        Returns the default custom path for SSM parameters.

        :return: The default custom path for SSM parameters.
        """
        if self.stack_name is None:
            raise ValueError("Stack name is not set.")
        return self.stack_name

    def _create_ssm_parameter(
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
        custom_path = custom_path or self._get_default_param_custom_path()

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

    def _create_sns_topic(
        self,
        topic_name,
        # TODO: #46 Study the use of FIFO SNS with a SQS as intermediary
        # to allow lambda subscriptions
        fifo=False,
        message_retention_period_in_days=7,  # just in case of fifo topics
        allow_event_bus_publish_on=True,
        **kwargs,
    ):
        topic = None

        if fifo:
            # create a FIFO SNS topic
            topic_name = f"{topic_name}.fifo"
            topic = sns.Topic(
                self,
                id=topic_name,
                topic_name=topic_name,
                display_name=topic_name,
                fifo=True,
                content_based_deduplication=True,
                message_retention_period_in_days=message_retention_period_in_days,
                **kwargs,
            )
        else:
            topic = sns.Topic(
                self,
                id=topic_name,
                topic_name=topic_name,
                display_name=topic_name,
                **kwargs,
            )

        if allow_event_bus_publish_on:
            # Add a resource policy allowing only EventBridge event buses
            # in the same account to publish messages
            topic.add_to_resource_policy(
                iam.PolicyStatement(
                    sid=f"AllowEventBridgePublishOn-{topic_name}",
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ServicePrincipal("events.amazonaws.com")],
                    actions=["sns:Publish"],
                    resources=[topic.topic_arn],
                )
            )

        self._create_ssm_parameter(
            topic_name + "-Arn", topic.topic_arn, self._get_default_param_custom_path()
        )

        self.do_log(title="SNS Topic Created", obj=f"{topic_name}\n{topic.topic_arn}")

        return topic

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
        log_retention=logs.RetentionDays.THREE_MONTHS,
        **kwargs,
    ) -> _lambda.Function:
        """
        Utility method to create a Lambda function with the specified configuration.
        Ensures the Lambda's log group retention policy is set
        according with the log_retention parameter.
        """
        # Create the Lambda function
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

        # Update log group retention according to the log_retention parameter
        logs.LogRetention(
            self,
            f"{name}LogRetention",
            log_group_name=f"/aws/lambda/{lambda_obj.function_name}",
            retention=log_retention,
        )

        self.do_log(
            f"Created Lambda function {name} with a "
            f"{log_retention} log retention policy."
        )

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

    def _get_custom_event_bus_name(self) -> str:
        """
        Returns the name of the FlowOrchestrator EventBridge event bus.
        That can be overridden in subclasses to use a different bus.
        """
        return "FlowOrchestratorEventBus"

    def _create_custom_event_bus(self):
        """
        Creates an EventBridge event bus with the specified name.
        """
        custom_event_bus_name = self._get_custom_event_bus_name()

        if not custom_event_bus_name:
            return None
        # else:
        self.do_log(f"Creating EventBus: {custom_event_bus_name}")
        # Create the EventBus
        custom_event_bus = events.EventBus(
            self,
            custom_event_bus_name,
            event_bus_name=custom_event_bus_name,
        )

        self.do_log(f"EventBus: {custom_event_bus_name} created")

        return custom_event_bus

    def _import_sns_topic(self, topic_name: str) -> sns.ITopic:
        """Imports an existing SNS topic by name."""
        topic_arn = f"arn:aws:sns:{self.region}:{self.account}:{topic_name}"
        return sns.Topic.from_topic_arn(self, topic_name, topic_arn)

    def _create_request_authorizer(
        self,
        authorizer_id: str,
        lambda_function: _lambda.Function,
        header_names: list[str] | None,
        context_values: list[str] | None,
        query_strings: list[str] | None,
        stage_variables: list[str] | None,
        human_friendly_authorizer_name: str | None,
        results_cache_ttl: None | int = 0,  # 0 = disables authorization caching
        **kwargs,
    ) -> apigw.RequestAuthorizer:
        """
        Creates an API Gateway Lambda authorizer where the full context of a request
        (e.g., headers, query string parameters, stage variables) can be used for
        request authorization. This is the preferred way to create API Gateway
        authorizers.
        """

        identity_sources = []

        if header_names:
            identity_sources.extend(
                [apigw.IdentitySource.header(x) for x in header_names]
            )
        if context_values:
            identity_sources.append(
                [apigw.IdentitySource.context(x) for x in context_values]
            )
        if query_strings:
            identity_sources.append(
                [apigw.IdentitySource.query_string(x) for x in query_strings]
            )
        if stage_variables:
            identity_sources.append(
                [apigw.IdentitySource.stage_variable(x) for x in stage_variables]
            )

        authorizer = apigw.RequestAuthorizer(
            self,
            authorizer_id,
            handler=lambda_function,
            identity_sources=identity_sources,
            authorizer_name=human_friendly_authorizer_name,
            results_cache_ttl=results_cache_ttl,
            **kwargs,
        )

        self.do_log(f"Created RequestAuthorizer {authorizer_id}")

        return authorizer

    def _create_token_authorizer(
        self,
        authorizer_id: str,
        lambda_function: _lambda.Function,
        identity_source: str | None,
        human_friendly_authorizer_name: str | None,
        results_cache_ttl: None | int = 0,  # 0 = disables authorization caching
        **kwargs,
    ) -> apigw.TokenAuthorizer:
        """
        Creates an API Gateway Lambda authorizer where only a single header containing
        an authorization token is used for request authorization.
        """

        authorizer = apigw.TokenAuthorizer(
            self,
            authorizer_id,
            handler=lambda_function,
            identity_source=identity_source,
            authorizer_name=human_friendly_authorizer_name,
            results_cache_ttl=results_cache_ttl,
            **kwargs,
        )

        self.do_log(f"Created TokenAuthorizer {authorizer_id}")

        return authorizer
