"""
Episode 6/7 (v2): List servers and deploy configuration.

Original v1 equivalents:
  - Episodes/Episode6/2-getServers-REST.py (pipe-delimited property parsing)
  - Episodes/Episode7/2-fulldeploy-REST.py (deploy + poll status)

In v2, properties are returned as proper JSON fields -- no more parsing
pipe-delimited strings like "name=bdds1|connected=true|..."
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bam_client import BAMClient

BAM_URL = os.environ.get("BAM_URL", "https://bam.lab.corp")
BAM_USER = os.environ.get("BAM_USER", "admin")
BAM_PASS = os.environ.get("BAM_PASS", "admin")

CONFIG_NAME = "main"
DEPLOY_SERVER = os.environ.get("DEPLOY_SERVER", "")  # set to server name to deploy

with BAMClient(BAM_URL, BAM_USER, BAM_PASS, verify_ssl=False) as bam:
    config = bam.find_configuration(CONFIG_NAME)

    # List all servers
    print("=== Servers ===")
    servers = bam.get_servers(config["id"])
    for server in servers.get("data", []):
        # v2 returns clean JSON -- no pipe-delimited parsing needed!
        print(f"  [{server['id']}] {server['name']}")
        for key, val in server.items():
            if key not in ("id", "name", "type", "_links"):
                print(f"    {key}: {val}")

    # Optional: deploy to a specific server
    if DEPLOY_SERVER:
        target = next(
            (s for s in servers.get("data", []) if s["name"] == DEPLOY_SERVER),
            None,
        )
        if not target:
            print(f"\nServer '{DEPLOY_SERVER}' not found")
            sys.exit(1)

        print(f"\nDeploying to {target['name']}...")
        bam.deploy_server(target["id"], services="DNS,DHCP")

        # Poll deployment status
        for _ in range(60):
            status = bam.get_deployment_status(target["id"])
            print(f"  Status: {status}")
            if status.get("status") in ("COMPLETED", "FAILED"):
                break
            time.sleep(2)
