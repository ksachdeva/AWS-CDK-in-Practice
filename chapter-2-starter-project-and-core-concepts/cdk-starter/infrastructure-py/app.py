#!/usr/bin/env python3

import aws_cdk as cdk
from infrastructure_py.web_stack import WebStack

app = cdk.App()
WebStack(app, "cip-chap2")

app.synth()
