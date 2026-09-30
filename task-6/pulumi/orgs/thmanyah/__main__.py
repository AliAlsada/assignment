import pulumi

import __setup__

# Load the pulumi global config
config = pulumi.Config("global")
env = config.get("env")

# This is the main resources for the infrastructure
## Storage
bucket = __setup__.create_bucket(env)

## Access
role = __setup__.create_role(env, bucket)

## Input
input = __setup__.create_input(env)

## Channel
channel = __setup__.create_channel(env, input, role, bucket)

# Outputs
pulumi.export("bucket", bucket.bucket)
pulumi.export("input_id", input.id)
pulumi.export("channel_id", channel.channel_id)
