"""
BlueCat Address Manager v2 API Client

A simple, modern Python client for the BAM RESTful v2 API.
This replaces the v1 REST/SOAP patterns from the original
bluecatlabs/making-apis-work-for-you examples.

Usage:
    from bam_client import BAMClient

    with BAMClient("https://bam.example.com", "admin", "password") as bam:
        info = bam.get_system_info()
        print(info)

Requirements:
    pip install requests
"""

import requests
import urllib3

# Suppress InsecureRequestWarning when verify=False is used in lab environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BAMClient:
    """Simple client for BlueCat Address Manager RESTful v2 API."""

    def __init__(self, url: str, username: str, password: str, verify_ssl: bool = True):
        self.base_url = url.rstrip("/")
        self.api_url = f"{self.base_url}/api/v2"
        self.username = username
        self.password = password
        self.verify = verify_ssl
        self.token = None
        self.session = requests.Session()
        self.session.verify = self.verify

    # --- Session management ---

    def login(self):
        """Authenticate and obtain API token."""
        resp = self.session.post(
            f"{self.api_url}/sessions",
            json={"username": self.username, "password": self.password},
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data["apiToken"]
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
        )
        return data

    def logout(self):
        """End the API session."""
        if self.token:
            self.session.delete(f"{self.api_url}/sessions")
            self.token = None

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, *args):
        self.logout()

    # --- Low-level HTTP helpers ---

    def get(self, path: str, params: dict | None = None):
        resp = self.session.get(f"{self.api_url}{path}", params=params)
        resp.raise_for_status()
        return resp.json() if resp.content else None

    def post(self, path: str, data: dict | None = None):
        resp = self.session.post(f"{self.api_url}{path}", json=data)
        resp.raise_for_status()
        return resp.json() if resp.content else None

    def put(self, path: str, data: dict | None = None):
        resp = self.session.put(f"{self.api_url}{path}", json=data)
        resp.raise_for_status()
        return resp.json() if resp.content else None

    def patch(self, path: str, data: dict | None = None):
        resp = self.session.patch(f"{self.api_url}{path}", json=data)
        resp.raise_for_status()
        return resp.json() if resp.content else None

    def delete(self, path: str):
        resp = self.session.delete(f"{self.api_url}{path}")
        resp.raise_for_status()

    # --- System ---

    def get_system_info(self):
        """Get BAM system information."""
        return self.get("/systemInfo")

    # --- Configurations ---

    def get_configurations(self):
        """List all configurations."""
        return self.get("/configurations")

    def get_configuration(self, config_id: int):
        return self.get(f"/configurations/{config_id}")

    def find_configuration(self, name: str):
        """Find a configuration by name."""
        result = self.get("/configurations", params={"filter": f"name:eq('{name}')"})
        items = result.get("data", [])
        return items[0] if items else None

    # --- Views ---

    def get_views(self, config_id: int):
        """List views in a configuration."""
        return self.get(f"/configurations/{config_id}/views")

    def find_view(self, config_id: int, name: str):
        result = self.get(
            f"/configurations/{config_id}/views",
            params={"filter": f"name:eq('{name}')"},
        )
        items = result.get("data", [])
        return items[0] if items else None

    # --- Zones ---

    def get_zones(self, view_id: int):
        """List zones under a view."""
        return self.get(f"/views/{view_id}/zones")

    def create_zone(self, view_id: int, name: str, zone_type: str = "Zone"):
        """Create a DNS zone."""
        return self.post(
            f"/views/{view_id}/zones",
            data={
                "type": zone_type,
                "name": name,
            },
        )

    # --- Resource Records ---

    def create_host_record(self, zone_id: int, name: str, ip: str, reverse: bool = True):
        """Create an A record (host record) with optional PTR."""
        return self.post(
            f"/zones/{zone_id}/resourceRecords",
            data={
                "type": "HostRecord",
                "name": name,
                "addresses": [{"address": ip}],
                "reverseRecord": reverse,
            },
        )

    def create_alias_record(self, zone_id: int, name: str, linked_record: str):
        """Create a CNAME record."""
        return self.post(
            f"/zones/{zone_id}/resourceRecords",
            data={
                "type": "AliasRecord",
                "name": name,
                "linkedRecord": linked_record,
            },
        )

    def get_resource_records(self, zone_id: int):
        """List records in a zone."""
        return self.get(f"/zones/{zone_id}/resourceRecords")

    def delete_resource_record(self, record_id: int):
        """Delete a resource record by ID."""
        self.delete(f"/resourceRecords/{record_id}")

    # --- IP Blocks ---

    def get_blocks(self, config_id: int):
        """List IPv4 blocks in a configuration."""
        return self.get(f"/configurations/{config_id}/blocks")

    def create_block(self, config_id: int, cidr: str, name: str | None = None):
        """Create an IPv4 block."""
        data = {"range": cidr}
        if name:
            data["name"] = name
        return self.post(f"/configurations/{config_id}/blocks", data=data)

    # --- Networks ---

    def get_networks(self, block_id: int):
        """List IPv4 networks in a block."""
        return self.get(f"/blocks/{block_id}/networks")

    def create_network(self, block_id: int, cidr: str, name: str | None = None):
        """Create an IPv4 network."""
        data = {"range": cidr}
        if name:
            data["name"] = name
        return self.post(f"/blocks/{block_id}/networks", data=data)

    # --- IP Addresses ---

    def get_addresses(self, network_id: int):
        """List IP addresses in a network."""
        return self.get(f"/networks/{network_id}/addresses")

    def assign_ip(
        self,
        network_id: int,
        address: str,
        mac: str | None = None,
        name: str | None = None,
        action: str = "MAKE_STATIC",
    ):
        """Assign an IP address."""
        data = {
            "address": address,
            "action": action,
        }
        if mac:
            data["macAddress"] = mac
        if name:
            data["name"] = name
        return self.post(f"/networks/{network_id}/addresses", data=data)

    def assign_next_available_ip(
        self,
        network_id: int,
        mac: str | None = None,
        name: str | None = None,
        action: str = "MAKE_DHCP_RESERVED",
    ):
        """Assign the next available IP in a network."""
        data = {"action": action}
        if mac:
            data["macAddress"] = mac
        if name:
            data["name"] = name
        return self.post(f"/networks/{network_id}/nextAvailableAddress", data=data)

    # --- DHCP Ranges ---

    def create_dhcp_range(self, network_id: int, start: str, end: str):
        """Create a DHCP range (pool) in a network."""
        return self.post(
            f"/networks/{network_id}/dhcpRanges",
            data={
                "start": start,
                "end": end,
            },
        )

    # --- Deployment Options ---

    def add_dns_option(self, entity_id: int, option_name: str, value: str):
        """Add a DNS deployment option."""
        return self.post(
            "/deploymentOptions",
            data={
                "type": "DNSDeploymentOption",
                "parentId": entity_id,
                "name": option_name,
                "value": value,
            },
        )

    def add_dhcp_option(self, entity_id: int, option_name: str, value: str):
        """Add a DHCP client deployment option."""
        return self.post(
            "/deploymentOptions",
            data={
                "type": "DHCPClientDeploymentOption",
                "parentId": entity_id,
                "name": option_name,
                "value": value,
            },
        )

    # --- Servers ---

    def get_servers(self, config_id: int):
        """List servers in a configuration."""
        return self.get(f"/configurations/{config_id}/servers")

    def deploy_server(self, server_id: int, services: str = "DNS,DHCP"):
        """Deploy configuration to a server."""
        return self.post(
            f"/servers/{server_id}/deploy",
            data={
                "services": services,
            },
        )

    def get_deployment_status(self, server_id: int):
        """Check deployment status."""
        return self.get(f"/servers/{server_id}/deploymentStatus")

    # --- Search ---

    def search(self, keyword: str, object_types: str | None = None, limit: int = 100):
        """Search across BAM objects."""
        params = {"filter": f"keyword:contains('{keyword}')", "limit": limit}
        if object_types:
            params["type"] = object_types
        return self.get("/search", params=params)
