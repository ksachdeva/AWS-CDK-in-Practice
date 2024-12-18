from pathlib import Path
from constructs import Construct
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from aws_cdk import aws_secretsmanager as sm
from .custom.resource_initializer import (
    ResourceInitializerProps,
    ResourceInitializer,
)  # noqa
from aws_cdk.aws_logs import RetentionDays
from aws_cdk.aws_lambda import DockerImageCode

from aws_cdk import Duration, CfnOutput


class RDS(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: ec2.Vpc,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        instance_id = "my-sql-instance"
        credentials_secret_name = f"chapter-4/rds/{instance_id}"

        self.credentials = rds.DatabaseSecret(
            self,
            "MySQLCredentials",
            username="admin",
            secret_name=credentials_secret_name,
        )

        self.instance = rds.DatabaseInstance(
            self,
            "MySQL",
            engine=rds.DatabaseInstanceEngine.mysql(
                version=rds.MysqlEngineVersion.VER_8_0_39
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3,
                ec2.InstanceSize.SMALL,
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                one_per_az=True,
            ),
            database_name="todolist",
            credentials=rds.Credentials.from_secret(self.credentials),
            instance_identifier=instance_id,
            port=3306,
            publicly_accessible=False,
        )

        docker_image_dir = Path(__file__).parent / "init"

        initializer = ResourceInitializer(
            self,
            "MySQLInitializer",
            props=ResourceInitializerProps(
                credentials_secret_name=credentials_secret_name,
                function_log_retention=RetentionDays.FIVE_MONTHS,
                function_code=DockerImageCode.from_image_asset(
                    str(docker_image_dir)
                ),  # noqa
                function_timeout=Duration.minutes(2),
                function_security_groups=[],
                vpc=vpc,
                subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                function_memory_size=512,
            ),
        )

        initializer.custom_resource.node.add_dependency(self.instance)

        self.credentials.grant_read(initializer.fn)

        self.instance.connections.allow_from(initializer.fn, ec2.Port.tcp(3306))

        CfnOutput(
            self,
            "RdsInitFnResponse",
            value=initializer.response,
        )
