"""
Office Template Provisioner

This example shows how to provision an entire office location from a YAML
template. It creates networks, DHCP scopes, DNS zones, host records, and
DHCP reservations for all hardware devices.

This is the "templating" workflow -- define your office once in YAML,
then run this to provision everything in BAM.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import yaml

from bam_client import BAMClient

BAM_URL = os.environ.get("BAM_URL", "https://bam.lab.corp")
BAM_USER = os.environ.get("BAM_USER", "admin")
BAM_PASS = os.environ.get("BAM_PASS")

TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), "office-template.yaml")


def provision_office(bam: BAMClient, template: dict, dry_run: bool = True):
    """Provision an office from a YAML template."""
    site = template["site"]
    network = template["network"]

    print(f"{'[DRY RUN] ' if dry_run else ''}Provisioning: {site['name']} ({site['code']})")
    print(f"  Domain: {network['domain']}")
    print(f"  Supernet: {network['supernet']}")

    actions = []

    # Step 1: Find or verify config/view exist
    config_name = network.get("bam_config", "main")
    view_name = network.get("bam_view", "default")
    print(f"\n1. Using config='{config_name}', view='{view_name}'")

    if not dry_run:
        config = bam.find_configuration(config_name)
        view = bam.find_view(config["id"], view_name)
    else:
        config = {"id": 0, "name": config_name}
        view = {"id": 0, "name": view_name}

    # Step 2: Create IP block for the office supernet
    print(f"\n2. Create IP block: {network['supernet']}")
    actions.append(
        {"action": "create_block", "cidr": network["supernet"], "name": f"{site['code']}-supernet"}
    )
    if not dry_run:
        block = bam.create_block(config["id"], network["supernet"], name=f"{site['code']}-supernet")
    else:
        block = {"id": 0}

    # Step 3: Create networks for each VLAN
    print("\n3. Create networks:")
    networks_created = {}
    for vlan in template["vlans"]:
        vlan_name = f"{site['code']}-vlan{vlan['id']}-{vlan['name']}"
        print(f"  VLAN {vlan['id']:>3} | {vlan['subnet']:<18} | {vlan_name}")
        actions.append({"action": "create_network", "cidr": vlan["subnet"], "name": vlan_name})
        if not dry_run:
            net = bam.create_network(block["id"], vlan["subnet"], name=vlan_name)
            networks_created[vlan["id"]] = net

    # Step 4: Create DNS forward zone
    print(f"\n4. Create DNS zone: {network['domain']}")
    actions.append({"action": "create_zone", "name": network["domain"]})
    zone = bam.create_zone(view["id"], network["domain"]) if not dry_run else {"id": 0}

    # Step 5: Create DHCP ranges for dynamic VLANs
    print("\n5. Create DHCP ranges:")
    for vlan in template["vlans"]:
        dhcp = vlan.get("dhcp", {})
        if dhcp.get("type") == "dynamic" and dhcp.get("range_start"):
            print(
                f"  VLAN {vlan['id']:>3} | {dhcp['range_start']} - {dhcp['range_end']} "
                f"| lease={dhcp.get('lease_time', '8h')}"
            )
            actions.append(
                {
                    "action": "create_dhcp_range",
                    "vlan": vlan["id"],
                    "start": dhcp["range_start"],
                    "end": dhcp["range_end"],
                }
            )
            if not dry_run:
                net = networks_created[vlan["id"]]
                bam.create_dhcp_range(net["id"], dhcp["range_start"], dhcp["range_end"])

    # Step 6: Create DHCP reservations + DNS records for hardware
    print("\n6. Hardware provisioning:")
    for device_type, devices in template.get("hardware", {}).items():
        for device in devices:
            mac = device.get("mac")
            ip = device.get("ip")
            name = device["name"]

            if mac and ip:
                print(f"  {device_type:<15} | {name:<20} | {ip:<15} | {mac}")
                actions.append(
                    {
                        "action": "reserve_and_register",
                        "name": name,
                        "ip": ip,
                        "mac": mac,
                        "type": device_type,
                    }
                )
                if not dry_run:
                    vlan_id = device.get("vlan")
                    if vlan_id and vlan_id in networks_created:
                        net = networks_created[vlan_id]
                        bam.assign_ip(
                            net["id"], ip, mac=mac, name=name, action="MAKE_DHCP_RESERVED"
                        )
                    bam.create_host_record(zone["id"], name, ip, reverse=True)
            elif ip:
                print(f"  {device_type:<15} | {name:<20} | {ip:<15} | (static)")
                actions.append({"action": "dns_only", "name": name, "ip": ip})
                if not dry_run:
                    bam.create_host_record(zone["id"], name, ip, reverse=True)

    # Step 7: WiFi summary
    print("\n7. WiFi SSIDs (configure on wireless controller):")
    for vlan in template["vlans"]:
        wifi = vlan.get("wifi")
        if wifi:
            portal = " + captive portal" if wifi.get("captive_portal") else ""
            print(f"  VLAN {vlan['id']:>3} | SSID: {wifi['ssid']:<20} | {wifi['security']}{portal}")

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Total actions: {len(actions)}")
    return actions


def main():
    if not os.path.exists(TEMPLATE_FILE):
        print(f"Template not found: {TEMPLATE_FILE}")
        print("Copy office-template.yaml to the examples directory.")
        sys.exit(1)

    with open(TEMPLATE_FILE) as f:
        template = yaml.safe_load(f)

    # Dry run by default -- set DRY_RUN=false to execute
    dry_run = os.environ.get("DRY_RUN", "true").lower() != "false"

    if dry_run:
        # Dry run doesn't need BAM connection
        provision_office(None, template, dry_run=True)
    else:
        if not BAM_PASS:
            print("Set BAM_PASS environment variable for live mode.")
            sys.exit(1)
        with BAMClient(BAM_URL, BAM_USER, BAM_PASS, verify_ssl=False) as bam:
            provision_office(bam, template, dry_run=False)


if __name__ == "__main__":
    main()
