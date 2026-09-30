import ipaddress
import os

import pulumi
import pulumi_libvirt as libvirt
import yaml

config = pulumi.Config("global")
image_config = pulumi.Config("image")

# The provider attaches disk files as raw, the servers use qcow2 disks
DISK_FORMAT_XSLT = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output omit-xml-declaration="yes" indent="yes"/>
  <xsl:template match="node()|@*">
    <xsl:copy>
      <xsl:apply-templates select="node()|@*"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="/domain/devices/disk[@device='disk']/driver/@type">
    <xsl:attribute name="type">qcow2</xsl:attribute>
  </xsl:template>
</xsl:stylesheet>
"""

ssh_keys = []
base_image = {}
networks = {}
servers_networks = {}


def configure_ssh_keys():
    admin_users = config.get_object("admin_users")
    for user in admin_users:
        email = user["email"]
        key = user.get("pubkey")
        if not key and user.get("pubkey_file"):
            with open(os.path.expanduser(user["pubkey_file"])) as pubkey_file:
                key = pubkey_file.read().strip()
        if not email or not key:
            raise ValueError(
                "Both email and pubkey must be provided for all admin users."
            )
        ssh_keys.append(key)


def configure_base_image():
    _volume = libvirt.Volume(
        "thmanyah-base-image",
        name="thmanyah-base-image.qcow2",
        pool=image_config.get("pool"),
        source=image_config.get("source"),
        format="qcow2",
    )
    base_image["volume"] = _volume


def create_networks(tiers):
    for tier in tiers:
        tier_name = tier["name"]
        network_name = "thmanyah-" + tier_name

        # NAT gives the servers outbound access only, there is no route between the networks
        _network = libvirt.Network(
            network_name,
            name=network_name,
            mode="nat",
            addresses=[tier["cidr"]],
            dhcp=libvirt.NetworkDhcpArgs(enabled=False),
            dns=libvirt.NetworkDnsArgs(enabled=True),
            autostart=True,
        )
        networks[tier_name] = {"network": _network, "cidr": tier["cidr"]}


def create_servers(servers, domain):
    for server in servers:
        server_name = server["name"] + domain
        interfaces = _interfaces(server)

        _cloudinit = libvirt.CloudInitDisk(
            server_name + "-cloudinit",
            name=server_name + "-cloudinit.iso",
            pool=image_config.get("pool"),
            user_data=_user_data(server, domain),
            network_config=_network_config(interfaces),
        )

        _volume = libvirt.Volume(
            server_name,
            name=server_name + ".qcow2",
            pool=image_config.get("pool"),
            base_volume_id=base_image["volume"].id,
            size=server["disk"] * 1024**3,
            format="qcow2",
        )

        libvirt.Domain(
            server_name,
            name=server_name,
            vcpu=server["cpu"],
            memory=server["memory"],
            cpu=libvirt.DomainCpuArgs(mode="host-passthrough"),
            cloudinit=_cloudinit.id,
            autostart=True,
            # The disk is attached by path, AppArmor blocks the base image of a pool volume
            disks=[libvirt.DomainDiskArgs(file=_volume.id)],
            xml=libvirt.DomainXmlArgs(xslt=DISK_FORMAT_XSLT),
            network_interfaces=[
                libvirt.DomainNetworkInterfaceArgs(
                    network_id=networks[interface["tier"]]["network"].id,
                    mac=interface["mac"],
                )
                for interface in interfaces
            ],
            consoles=[
                libvirt.DomainConsoleArgs(
                    type="pty", target_type="serial", target_port="0"
                )
            ],
            # The provider reads the disk back as a volume and reports a change on every run
            opts=pulumi.ResourceOptions(ignore_changes=["disks"]),
        )

        servers_networks[server["name"]] = {
            interface["tier"]: interface["ip"] for interface in interfaces
        }


def networks_output():
    return {name: network["cidr"] for name, network in networks.items()}


def servers_output():
    return servers_networks


def _interfaces(server):
    interfaces = []
    for index, network in enumerate(server["networks"]):
        address = ipaddress.ip_address(network["ip"])
        cidr = ipaddress.ip_network(networks[network["tier"]]["cidr"])
        if address not in cidr:
            raise ValueError(f"{network['ip']} is not part of the {network['tier']} network.")

        octets = address.packed
        interfaces.append(
            {
                "name": f"eth{index}",
                "tier": network["tier"],
                "ip": network["ip"],
                "prefix": cidr.prefixlen,
                "gateway": str(cidr.network_address + 1),
                "routes": network.get("routes", []),
                # The MAC address is derived from the IP to keep it stable
                "mac": "52:54:00:%02x:%02x:%02x" % (octets[1], octets[2], octets[3]),
            }
        )
    return interfaces


def _user_data(server, domain):
    # The keys are added to the default user of the image, Ansible manages the users
    user_data = {
        "hostname": server["name"],
        "fqdn": server["name"] + domain,
        "ssh_authorized_keys": ssh_keys,
    }
    return "#cloud-config\n" + yaml.safe_dump(user_data, sort_keys=False)


def _network_config(interfaces):
    ethernets = {}
    for index, interface in enumerate(interfaces):
        ethernets[interface["name"]] = {
            "match": {"macaddress": interface["mac"]},
            "set-name": interface["name"],
            "addresses": [f"{interface['ip']}/{interface['prefix']}"],
        }
        routes = list(interface["routes"])
        # Only the first interface has a default route and DNS
        if index == 0:
            routes.insert(0, {"to": "default", "via": interface["gateway"]})
            ethernets[interface["name"]]["nameservers"] = {
                "addresses": [interface["gateway"]]
            }
        if routes:
            ethernets[interface["name"]]["routes"] = routes
    return yaml.safe_dump({"version": 2, "ethernets": ethernets}, sort_keys=False)
