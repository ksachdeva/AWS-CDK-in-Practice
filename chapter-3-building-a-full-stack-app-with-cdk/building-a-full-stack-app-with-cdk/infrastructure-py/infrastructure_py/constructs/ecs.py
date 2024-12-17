from pathlib import Path

from constructs import Construct
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2

from aws_cdk import Duration, CfnOutput
from aws_cdk import aws_dynamodb as dynamodb


class ECS(Construct):

    def __init__(self, scope: Construct, id: str, table: dynamodb.Table) -> None:
        super().__init__(scope, id)

        # VPC
        vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
        )

        # ECS Cluster
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        cluster.add_capacity(
            "DefaultAutoScalingGroup",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T2,
                ec2.InstanceSize.MICRO,
            ),
        )

        # ECS Task Definition
        task_definition = ecs.FargateTaskDefinition(self, "TaskDefinition")

        server_dir = Path(__file__).parent.parent.parent.parent / "server"

        print(server_dir)

        # ECS Container Definition
        container = task_definition.add_container(
            "Express",
            image=ecs.ContainerImage.from_asset(str(server_dir)),
            memory_limit_mib=256,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="chapter3",
            ),
        )

        container.add_port_mappings(
            ecs.PortMapping(
                container_port=80,
                protocol=ecs.Protocol.TCP,
            ),
        )

        # ECS Service
        service = ecs.FargateService(
            self,
            "Service",
            cluster=cluster,
            task_definition=task_definition,
        )

        load_balancer = elbv2.ApplicationLoadBalancer(
            self,
            "LB",
            vpc=vpc,
            internet_facing=True,
        )

        listener = load_balancer.add_listener(
            "PublicListener",
            port=80,
            open=True,
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
            ),
        )

        table.grant_read_write_data(service.task_definition.task_role)

        CfnOutput(
            self,
            "BackendURL",
            value=load_balancer.load_balancer_dns_name,
            description="Load Balancer DNS",
        )
