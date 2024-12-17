from constructs import Construct
from aws_cdk import RemovalPolicy
from aws_cdk import aws_s3 as s3


class S3Bucket(Construct):
    def __init__(self, scope: Construct, id: str, *, environment: str) -> None:
        super().__init__(scope, id)

        s3.Bucket(
            self,
            f"Bucket-S3-{environment}",
            removal_policy=RemovalPolicy.DESTROY,
        )
