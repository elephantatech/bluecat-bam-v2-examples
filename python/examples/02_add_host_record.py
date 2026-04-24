"""
Episode 1 (v2): Add a host record (A + PTR) and a CNAME alias.

Original v1 equivalent: Episodes/Episode1/2-addHost-REST.py
  - v1 built URLs manually with string concatenation
  - v1 used getEntityByName to walk: Config -> View -> Zone
  - v2 uses resource-based paths: /views/{id}/zones, /zones/{id}/resourceRecords
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bam_client import BAMClient

BAM_URL = os.environ.get("BAM_URL", "https://bam.lab.corp")
BAM_USER = os.environ.get("BAM_USER", "admin")
BAM_PASS = os.environ.get("BAM_PASS", "admin")

# What we want to create
HOSTNAME = "FINRPT02"
IP_ADDRESS = "192.168.0.16"
ALIAS = "reporting2"
CONFIG_NAME = "main"
VIEW_NAME = "default"
ZONE_NAME = "lab.corp"

with BAMClient(BAM_URL, BAM_USER, BAM_PASS, verify_ssl=False) as bam:
    # 1. Find configuration
    config = bam.find_configuration(CONFIG_NAME)
    print(f"Config: [{config['id']}] {config['name']}")

    # 2. Find view
    view = bam.find_view(config["id"], VIEW_NAME)
    print(f"View: [{view['id']}] {view['name']}")

    # 3. Find zone (or list zones to find it)
    zones = bam.get_zones(view["id"])
    zone = next(
        (z for z in zones.get("data", []) if z["name"] == ZONE_NAME),
        None,
    )
    if not zone:
        print(f"Zone '{ZONE_NAME}' not found. Available zones:")
        for z in zones.get("data", []):
            print(f"  {z['name']}")
        sys.exit(1)
    print(f"Zone: [{zone['id']}] {zone['name']}")

    # 4. Create host record (A + PTR)
    host = bam.create_host_record(zone["id"], HOSTNAME, IP_ADDRESS, reverse=True)
    print(f"\nHost record created: {host}")

    # 5. Create CNAME alias
    linked = f"{HOSTNAME}.{ZONE_NAME}"
    alias = bam.create_alias_record(zone["id"], ALIAS, linked)
    print(f"Alias record created: {alias}")
