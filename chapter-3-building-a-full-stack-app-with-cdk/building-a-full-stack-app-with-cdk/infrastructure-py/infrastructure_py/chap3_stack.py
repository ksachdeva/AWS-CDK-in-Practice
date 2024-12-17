from aws_cdk import Stack
from constructs import Construct

from .constructs.s3_bucket import S3Bucket
from .constructs.db import DynamoDB
from .constructs.ecs import ECS


class Chapter3Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        db = DynamoDB(self, "DynamoDB")
        s3 = S3Bucket(self, "S3")

        ecs = ECS(self, "ECS", db.main_table)
