"""
BlueCat Address Manager v2 API Client

A simple, modern Python client for the BAM RESTful v2 API.
This replaces the v1 REST/SOAP patterns from the original
bluecatlabs/making-apis-work-for-you examples.

NOTE: Endpoint paths and request bodies were verified against the
BAM v2 API documentation (25.1.0). Some endpoints may differ
between BAM versions (9.5, 9.6, 25.1). If a call returns 404
or 400, check your BAM's Swagger UI at https://<BAM_IP>/api/docs
for the exact paths and schemas your version supports.

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


def _escape_filter_value(value: str) -> str:
    """Escape single quotes in BAM v2 filter values."""
    return value.replace("'", "''")


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
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        """End the API session via PATCH (v2 documented approach)."""
        if self.token:
            try:
                self.session.patch(
                    f"{self.api_url}/sessions/current",
                    json={"state": "LOGGED_OUT"},
                )
            except Exception:
                pass
            finally:
                self.token = None

    def close(self):
        """Close the underlying HTTP session."""
        self.logout()
        self.session.close()

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, *args):
        self.close()

    # --- Low-level HTTP helpers ---

    def get(self, path: str, params: dict | None = None):
        resp = self.session.get(f"{self.api_url}{path}", params=params)
        resp.raise_for_status()
        return resp.json() if resp.content else None

    def get_all(self, path: str, params: dict | None = None) -> list:
        """Fetch all pages of a collection endpoint."""
        params = dict(params or {})
        results = []
        offset = 0
        limit = 100
        while True:
            params["offset"] = offset
            params["limit"] = limit
            resp = self.get(path, params=params)
            items = resp.get("data", []) if resp else []
            results.extend(items)
            if len(items) < limit:
                break
            offset += limit
        return results

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
        """Find a configuration by name. Raises ValueError if not found."""
        escaped = _escape_filter_value(name)
        result = self.get("/configurations", params={"filter": f"name:eq('{escaped}')"})
        items = result.get("data", [])
        if not items:
            raise ValueError(f"Configuration '{name}' not found")
        return items[0]

    # --- Views ---

    def get_views(self, config_id: int):
        """List views in a configuration."""
        return self.get(f"/configurations/{config_id}/views")

    def find_view(self, config_id: int, name: str):
        """Find a view by name. Raises ValueError if not found."""
        escaped = _escape_filter_value(name)
        result = self.get(
            f"/configurations/{config_id}/views",
            params={"filter": f"name:eq('{escaped}')"},
        )
        items = result.get("data", [])
        if not items:
            raise ValueError(f"View '{name}' not found in configuration {config_id}")
        return items[0]

    # --- Zones ---

    def get_zones(self, view_id: int):
        """List zones under a view."""
        return self.get(f"/views/{view_id}/zones")

    def create_zone(self, view_id: int, absolute_name: str, zone_type: str = "Zone"):
        """Create a DNS zone. Use absoluteName for dotted names (e.g., 'office.example.com')."""
        return self.post(
            f"/views/{view_id}/zones",
            data={
                "type": zone_type,
                "absoluteName": absolute_name,
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
        data: dict = {"type": "IPv4Block", "range": cidr}
        if name:
            data["name"] = name
        return self.post(f"/configurations/{config_id}/blocks", data=data)

    # --- Networks ---

    def get_networks(self, block_id: int):
        """List IPv4 networks in a block."""
        return self.get(f"/blocks/{block_id}/networks")

    def create_network(self, block_id: int, cidr: str, name: str | None = None):
        """Create an IPv4 network."""
        data: dict = {"type": "IPv4Network", "range": cidr}
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
        data: dict = {
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
        """Get and assign the next available IP in a network.

        NOTE: The v2 API may use GET for discovery and POST for assignment
        depending on your BAM version. Check /api/docs on your instance.
        """
        data: dict = {"action": action}
        if mac:
            data["macAddress"] = mac
        if name:
            data["name"] = name
        return self.post(f"/networks/{network_id}/nextAvailableAddress", data=data)

    # --- DHCP Ranges ---

    def create_dhcp_range(self, network_id: int, start: str, end: str):
        """Create a DHCP range (pool) in a network.

        NOTE: Some BAM versions use /ranges instead of /dhcpRanges, and
        expect {range: "offset,size"} or {fromAddress, toAddress} instead
        of {start, end}. Check /api/docs on your instance.
        """
        return self.post(
            f"/networks/{network_id}/ranges",
            data={
                "type": "DHCP4Range",
                "start": start,
                "end": end,
            },
        )

    # --- Deployment Options ---

    def add_dns_option(self, zone_id: int, option_name: str, value: str):
        """Add a DNS deployment option to a zone."""
        return self.post(
            f"/zones/{zone_id}/deploymentOptions",
            data={
                "type": "DNSDeploymentOption",
                "name": option_name,
                "value": value,
            },
        )

    def add_dhcp_option(self, network_id: int, option_name: str, value: str):
        """Add a DHCP client deployment option to a network."""
        return self.post(
            f"/networks/{network_id}/deploymentOptions",
            data={
                "type": "DHCPClientDeploymentOption",
                "name": option_name,
                "value": value,
            },
        )

    # --- Servers ---

    def get_servers(self, config_id: int):
        """List servers in a configuration."""
        return self.get(f"/configurations/{config_id}/servers")

    def deploy_server(self, server_id: int, services: list[str] | None = None):
        """Deploy configuration to a server.

        NOTE: Some BAM versions use /deployments instead of /deploy.
        Check /api/docs on your instance.
        """
        return self.post(
            f"/servers/{server_id}/deployments",
            data={
                "services": services or ["DNS", "DHCP"],
            },
        )

    def get_deployment_status(self, server_id: int):
        """Check deployment status."""
        return self.get(f"/servers/{server_id}/deploymentStatus")

    # --- Search ---

    def search(self, keyword: str, object_types: str | None = None, limit: int = 100):
        """Search by filtering on a collection endpoint.

        The v2 API has no /search endpoint. This searches configurations
        using the filter parameter. For more targeted searches, use
        get() with filters on specific collection endpoints like
        /zones, /resourceRecords, /networks, etc.
        """
        params: dict = {
            "filter": f"name:contains('{_escape_filter_value(keyword)}')",
            "limit": limit,
        }
        if object_types:
            params["type"] = object_types
        return self.get("/configurations", params=params)
