from pathlib import Path

from constructs import Construct
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2

from aws_cdk import Duration, CfnOutput, RemovalPolicy
from aws_cdk.aws_logs import LogGroup, RetentionDays
from aws_cdk.aws_certificatemanager import Certificate
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as route53_targets

from dataclasses import dataclass


@dataclass
class ECSProps:
    vpc: ec2.Vpc
    rds_host_name: str
    certificate: Certificate
    hosted_zone: route53.IHostedZone
    backend_subdomain_name: str
    domain_name: str


class ECS(Construct):

    def __init__(self, scope: Construct, id: str, props: ECSProps) -> None:
        super().__init__(scope, id)

        log_group = LogGroup(
            self,
            "LogGroup-chapter-4",
            retention=RetentionDays.ONE_DAY,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ECS Cluster
        self.cluster = ecs.Cluster(self, "Cluster", vpc=props.vpc)

        self.cluster.add_capacity(
            "DefaultAutoScalingGroup",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T2,
                ec2.InstanceSize.MICRO,
            ),
        )

        # ECS Task Definition
        self.task_definition = ecs.Ec2TaskDefinition(self, "TaskDefinition")

        server_dir = Path(__file__).parent.parent.parent.parent / "server"

        print(server_dir)

        # ECS Container Definition
        container = self.task_definition.add_container(
            "Express",
            image=ecs.ContainerImage.from_asset(str(server_dir)),
            memory_limit_mib=256,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="chapter4",
                log_group=log_group,
            ),
            environment={
                "RDS_HOST": props.rds_host_name,
            },
        )

        container.add_port_mappings(
            ecs.PortMapping(
                container_port=80,
                protocol=ecs.Protocol.TCP,
            ),
        )

        # ECS Service
        service = ecs.Ec2Service(
            self,
            "Service",
            cluster=self.cluster,
            task_definition=self.task_definition,
        )

        load_balancer = elbv2.ApplicationLoadBalancer(
            self,
            "LB",
            vpc=props.vpc,
            internet_facing=True,
            load_balancer_name="chapter4-lb",
        )

        listener = load_balancer.add_listener(
            "PublicListener",
            port=443,
            open=True,
            certificates=[props.certificate],  # noqa
        )

        listener.add_targets(
            "ECS",
            port=80,
            targets=[
                service.load_balancer_target(
                    container_name="Express",
                    container_port=80,
                )
            ],
            health_check=elbv2.HealthCheck(
                path="/healthcheck",
                timeout=Duration.seconds(5),
                interval=Duration.seconds(60),
                unhealthy_threshold_count=5,
                healthy_threshold_count=5,
            ),
        )

        route53.ARecord(
            self,
            "BackendAliasRecord",
            zone=props.hosted_zone,
            target=route53.RecordTarget.from_alias(
                route53_targets.LoadBalancerTarget(load_balancer)
            ),
            record_name=f"{props.backend_subdomain_name}.{props.domain_name}",
        )

        CfnOutput(
            self,
            "BackendURL",
            value=load_balancer.load_balancer_dns_name,
            description="Load Balancer DNS",
        )
