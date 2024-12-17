#!/usr/bin/env python3

import aws_cdk as cdk

from infrastructure_py.chap3_stack import Chapter3Stack


app = cdk.App()
Chapter3Stack(app, "Chapter3Stack")

app.synth()
