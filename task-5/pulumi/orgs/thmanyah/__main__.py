import pulumi

import __setup__

# Load the pulumi global config
config = pulumi.Config("global")
domain = config.get("domain")

# Initial Configs
__setup__.configure_ssh_keys()
__setup__.configure_base_image()

# This is the main resources for the infrastructure
## Networks
networks_config = pulumi.Config("networks")

tiers = networks_config.get_object("tiers")
if tiers:
    __setup__.create_networks(tiers)

# Servers
servers_config = pulumi.Config("servers")

## Router
router_servers = servers_config.get_object("router_servers")
if router_servers:
    __setup__.create_servers(router_servers, domain)

## Public Tier
lb_servers = servers_config.get_object("lb_servers")
if lb_servers:
    __setup__.create_servers(lb_servers, domain)

## Application Tier
app_servers = servers_config.get_object("app_servers")
if app_servers:
    __setup__.create_servers(app_servers, domain)

## Database Tier
postgres_servers = servers_config.get_object("postgres_servers")
if postgres_servers:
    __setup__.create_servers(postgres_servers, domain)

# Outputs
pulumi.export("networks", __setup__.networks_output())
pulumi.export("servers", __setup__.servers_output())
