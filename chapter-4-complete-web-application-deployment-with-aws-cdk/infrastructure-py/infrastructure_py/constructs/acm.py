from constructs import Construct
from aws_cdk import aws_certificatemanager as cm
from aws_cdk import aws_route53 as route53


class ACM(Construct):

    def __init__(
        self,
        scope: Construct,
        id: str,
        domain_name: str,
        hosted_zone: route53.IHostedZone,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.certificate = cm.Certificate(
            self,
            "Certificate",
            domain_name=domain_name,
            validation=cm.CertificateValidation.from_dns(hosted_zone),
            subject_alternative_names=[f"*.{domain_name}"],
        )
