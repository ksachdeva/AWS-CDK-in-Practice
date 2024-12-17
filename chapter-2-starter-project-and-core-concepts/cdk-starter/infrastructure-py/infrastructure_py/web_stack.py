from aws_cdk import Stack
from constructs import Construct

from infrastructure_py.constructs.s3_bucket import S3Bucket


class WebStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = S3Bucket(self, "MyRemovableBucket", environment="dev")
