import json
import hashlib
from constructs import Construct
from aws_cdk import aws_ec2 as ec2
from aws_cdk import custom_resources as cr
from aws_cdk import Duration, Stack
from aws_cdk import aws_lambda as _lambda
from aws_cdk.aws_logs import RetentionDays
from aws_cdk import aws_iam as iam

from dataclasses import dataclass


@dataclass
class ResourceInitializerProps:
    vpc: ec2.Vpc
    credentials_secret_name: str
    function_code: _lambda.DockerImageCode
    function_log_retention: RetentionDays
    function_security_groups: list[ec2.ISecurityGroup]
    function_timeout: Duration
    function_memory_size: int
    subnet_type: ec2.SubnetType


class ResourceInitializer(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        props: ResourceInitializerProps,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        stack = Stack.of(self)

        function_security_group = ec2.SecurityGroup(
            self,
            "FunctionSecurityGroup",
            vpc=props.vpc,
            allow_all_outbound=True,
            security_group_name=f"{id}-function-security-group",
        )

        self.fn = _lambda.DockerImageFunction(
            self,
            "ResourceInitializerFunction",
            code=props.function_code,
            # allow_all_outbound=True,
            function_name=f"{id}-ReInit{stack.stack_name}",
            log_retention=props.function_log_retention,
            memory_size=props.function_memory_size,
            security_groups=[function_security_group]
            + props.function_security_groups,  # noqa
            timeout=props.function_timeout,
            vpc=props.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=props.subnet_type,
            ),
        )

        payload: str = json.dumps(
            {
                "params": {
                    "config": {"credentials_secret_name": props.credentials_secret_name}
                }
            }
        )

        payload_hash_prefix = hashlib.md5(payload.encode()).hexdigest()[:6]

        sdk_call = cr.AwsSdkCall(
            action="invoke",
            service="Lambda",
            parameters={
                "FunctionName": self.fn.function_name,
                "Payload": payload,
            },  # noqa
            physical_resource_id=cr.PhysicalResourceId.of(
                f"{id}-AwsSdkCall-{self.fn.current_version.version + payload_hash_prefix}"  # noqa
            ),
        )

        cr_fn_role = iam.Role(
            self,
            "AwsCustomResourceRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        cr_fn_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[self.fn.function_arn],
            )
        )

        self.custom_resource = cr.AwsCustomResource(
            self,
            "AwsCustomResource",
            on_update=sdk_call,
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
            role=cr_fn_role,
            timeout=Duration.minutes(10),
        )

        self.response = self.custom_resource.get_response_field("Payload")
