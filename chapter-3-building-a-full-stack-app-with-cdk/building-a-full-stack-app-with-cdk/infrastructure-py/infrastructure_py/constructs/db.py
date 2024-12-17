from aws_cdk import RemovalPolicy, aws_dynamodb as dynamodb
from constructs import Construct


class DynamoDB(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        # create the dynamodb table
        self.main_table = dynamodb.Table(
            self,
            "MainTable",
            table_name="main_table",
            partition_key=dynamodb.Attribute(
                name="partition_key",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="sort_key",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
