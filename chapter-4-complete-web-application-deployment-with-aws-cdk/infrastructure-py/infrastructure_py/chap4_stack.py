import json
from pathlib import Path
from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from constructs import Construct

from .constructs.route_53 import Route53
from .constructs.acm import ACM
from .constructs.s3_bucket import S3Bucket
from .constructs.rds import RDS
from .constructs.ecs import ECS, ECSProps


class Chapter4Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        config_path = Path(__file__).parent.parent.parent.joinpath("config.json")

        config_json = config_path.read_text()
        domain_name = json.loads(config_json)["domain_name"]
        frontend_subdomain_name = json.loads(config_json)["frontend_subdomain"]
        backend_subdomain_name = json.loads(config_json)["backend_subdomain"]

        print(f"Domain Name: {domain_name}")

        r53 = Route53(self, "Route53", domain_name=domain_name)
        acm = ACM(
            self,
            "ACM",
            domain_name=domain_name,
            hosted_zone=r53.hosted_zone,
        )

        vpc = ec2.Vpc(
            self,
            "VPC",
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name="ingress",
                    subnet_type=ec2.SubnetType.PUBLIC,
                ),
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name="compute",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                ),
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name="rds",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                ),
            ],
        )

        s3_bucket = S3Bucket(
            self,
            "S3Bucket",
            domain_name=domain_name,
            frontend_subdomain_name=frontend_subdomain_name,
            certificate=acm.certificate,
            hosted_zone=r53.hosted_zone,
        )

        rds = RDS(
            self,
            "RDS",
            vpc=vpc,
        )

        ecs = ECS(
            self,
            "ECS",
            props=ECSProps(
                vpc=vpc,
                rds_host_name=rds.instance.instance_endpoint.hostname,
                certificate=acm.certificate,
                hosted_zone=r53.hosted_zone,
                backend_subdomain_name=backend_subdomain_name,
                domain_name=domain_name,
            ),
        )

        rds.instance.connections.allow_from(ecs.cluster, ec2.Port.tcp(3306))

        ecs.task_definition.task_role.add_to_principal_policy(
            statement=iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[rds.credentials.secret_arn],
            )
        )

        # ecs.node.add_dependency(rds)
