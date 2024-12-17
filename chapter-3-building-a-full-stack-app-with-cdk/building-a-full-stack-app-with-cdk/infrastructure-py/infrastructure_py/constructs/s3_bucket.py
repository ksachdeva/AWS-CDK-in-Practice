import uuid
from pathlib import Path

from aws_cdk import CfnOutput, RemovalPolicy
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3_deployment
from constructs import Construct


class S3Bucket(Construct):
    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)

        web_bucket = s3.Bucket(
            self,
            "WebBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            access_control=s3.BucketAccessControl.BUCKET_OWNER_FULL_CONTROL,
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,
            public_read_access=True,
            website_index_document="index.html",
            website_error_document="index.html",
            bucket_name=f"chapter-3-web-bucket-{uuid.uuid4()}",
        )

        build_path = Path(__file__).parent.parent.parent.parent / "web" / "build"

        print(build_path)

        web_bucket_deploy = s3_deployment.BucketDeployment(
            self,
            "WebBucketDeployment",
            sources=[s3_deployment.Source.asset(str(build_path))],
            destination_bucket=web_bucket,
        )

        CfnOutput(
            self,
            "FrontendURL",
            value=web_bucket.bucket_website_url,
            description="Web Bucket URL",
        )
