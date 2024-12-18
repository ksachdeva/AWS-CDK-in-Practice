from constructs import Construct
from aws_cdk import aws_route53 as route53


class Route53(Construct):

    def __init__(
        self,
        scope: Construct,
        id: str,
        domain_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.hosted_zone = route53.HostedZone.from_lookup(
            self,
            "HostedZone",
            domain_name=domain_name,
        )
