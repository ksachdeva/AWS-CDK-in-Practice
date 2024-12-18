import uuid
from pathlib import Path

from aws_cdk import CfnOutput, RemovalPolicy
from aws_cdk import aws_certificatemanager as cm
from aws_cdk import aws_cloudfront as cf
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as route53_targets
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3_deployment
from constructs import Construct


class S3Bucket(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        domain_name: str,
        frontend_subdomain_name: str,
        certificate: cm.Certificate,
        hosted_zone: route53.IHostedZone,
    ) -> None:
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
            bucket_name=f"chapter-4-web-bucket-{uuid.uuid4()}",
        )

        build_path = Path(__file__).parent.parent.parent.parent / "web" / "build"

        print(build_path)

        web_bucket_deploy = s3_deployment.BucketDeployment(
            self,
            "WebBucketDeployment",
            sources=[s3_deployment.Source.asset(str(build_path))],
            destination_bucket=web_bucket,
        )

        # create the cloudfront distribution
        # oai = cf.OriginAccessIdentity(self, "chap4-fe-oai")
        # oai.apply_removal_policy(RemovalPolicy.DESTROY)

        # # grant above identity read access to the bucket
        # web_bucket.grant_read(oai)

        # cf_distribution = cf.CloudFrontWebDistribution(
        #     self,
        #     "chap4-fe-distribution",
        #     origin_configs=[
        #         cf.SourceConfiguration(
        #             s3_origin_source=cf.S3OriginConfig(
        #                 s3_bucket_source=web_bucket,
        #                 origin_access_identity=oai,
        #             ),
        #             behaviors=[cf.Behavior(is_default_behavior=True)],
        #         )
        #     ],
        # )

        distribution = cf.Distribution(
            self,
            "chap4-fe-distribution",
            certificate=certificate,
            domain_names=[f"{frontend_subdomain_name}.{domain_name}"],
            default_root_object="index.html",
            default_behavior=cf.BehaviorOptions(
                origin=origins.S3Origin(web_bucket),
                viewer_protocol_policy=cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,  # noqa
            ),
        )

        route53.ARecord(
            self,
            "FrontendAliasRecord",
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(
                route53_targets.CloudFrontTarget(distribution)
            ),
            record_name=f"{frontend_subdomain_name}.{domain_name}",
        )

        CfnOutput(
            self,
            "FrontendURL",
            value=web_bucket.bucket_website_url,
            description="The bucket wesbite URL",
        )
