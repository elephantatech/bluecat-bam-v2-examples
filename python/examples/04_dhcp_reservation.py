"""
Episode 2 (v2): Assign a DHCP reservation with next available IP.

Original v1 equivalent: Episodes/Episode2/2-assignDHCPReservation-REST.py
  - v1 used assignNextAvailableIP4Address with pipe-delimited properties
  - v1 required manually walking Config -> Network -> View for hostInfo
  - v2 uses POST /networks/{id}/nextAvailableAddress with JSON body
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bam_client import BAMClient

BAM_URL = os.environ.get("BAM_URL", "https://bam.lab.corp")
BAM_USER = os.environ.get("BAM_USER", "admin")
BAM_PASS = os.environ.get("BAM_PASS", "admin")

# Device to reserve
MAC_ADDRESS = "BB:CC:DD:AA:AA:AA"
HOSTNAME = "appsrv23"
CONFIG_NAME = "main"
NETWORK_CIDR = "192.168.3.0/24"

with BAMClient(BAM_URL, BAM_USER, BAM_PASS, verify_ssl=False) as bam:
    # 1. Find config
    config = bam.find_configuration(CONFIG_NAME)
    print(f"Config: {config['name']}")

    # 2. Find the network
    blocks = bam.get_blocks(config["id"])
    # Walk blocks to find the network containing our CIDR
    network = None
    for block in blocks.get("data", []):
        networks = bam.get_networks(block["id"])
        for net in networks.get("data", []):
            if net.get("range") == NETWORK_CIDR:
                network = net
                break
        if network:
            break

    if not network:
        print(f"Network {NETWORK_CIDR} not found")
        sys.exit(1)
    print(f"Network: [{network['id']}] {network.get('range')}")

    # 3. Assign next available IP as DHCP reserved
    result = bam.assign_next_available_ip(
        network["id"],
        mac=MAC_ADDRESS,
        name=HOSTNAME,
        action="MAKE_DHCP_RESERVED",
    )
    print("\nReservation created:")
    print(f"  Host: {HOSTNAME}")
    print(f"  MAC:  {MAC_ADDRESS}")
    print(f"  IP:   {result}")
