#!/usr/bin/env python3

import os
import aws_cdk as cdk
from infrastructure_py.chap4_stack import Chapter4Stack


app = cdk.App()
Chapter4Stack(
    app,
    "Chapter4Stack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

app.synth()
