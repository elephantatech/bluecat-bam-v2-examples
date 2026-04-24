# BlueCat BAM v2 API Examples

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Modern examples for the [BlueCat Address Manager](https://bluecatnetworks.com/) RESTful v2 API, covering DNS, DHCP, and IPAM automation. Includes an office location template provisioner.

This project is a v2 API rewrite of the official [bluecatlabs/making-apis-work-for-you](https://github.com/bluecatlabs/making-apis-work-for-you) examples, which use the deprecated v1 REST and SOAP APIs.

> Blog post: [Migrating from BlueCat BAM v1 to v2 REST API](https://techmystery.blogspot.com/)

## BlueCat documentation

- [BAM RESTful v2 API Guide (25.1.0)](https://docs.bluecatnetworks.com/r/Address-Manager-RESTful-v2-API-Guide/Introduction/25.1.0)
- [BAM Legacy v1 API Guide (9.5.0)](https://docs.bluecatnetworks.com/r/en-US/Address-Manager-Legacy-v1-API-Guide/9.5.0)
- [v1 to v2 Migration Guide](https://docs.bluecatnetworks.com/r/Address-Manager-RESTful-v2-API-Guide/v1-REST-API-to-RESTful-v2-API-migration-guide/9.5.0)
- [BlueCat Python Library (bluecat-libraries)](https://docs.bluecatnetworks.com/r/BlueCat-Python-Library-Guide/BlueCat-Library-Address-Manager-REST-v2-API-client-reference/23.1)
- Every BAM instance ships with Swagger UI at `https://<your-bam>/api/docs` and OpenAPI spec at `https://<your-bam>/api/openapi.json`

## What changed from v1 to v2

| v1 (deprecated) | v2 (current) |
|---|---|
| `GET /Services/REST/v1/login?username=...&password=...` | `POST /api/v2/sessions` with JSON body |
| Token parsed from string: `"Session Token-> BAMAuthToken: ..."` | Proper JSON response with `apiToken` field |
| RPC-style: `POST /v1/addHostRecord?viewId=...&absoluteName=...` | REST-style: `POST /api/v2/zones/{id}/resourceRecords` |
| Properties as pipe-delimited strings: `"name=x\|connected=true\|"` | Clean JSON objects with named fields |
| `getEntityByName` to walk hierarchy manually | Resource paths: `/configurations/{id}/views/{id}/zones` |
| `assignNextAvailableIP4Address` with `hostInfo` string encoding | `POST /networks/{id}/nextAvailableAddress` with JSON |
| No spec | OpenAPI 3.0 spec at `/api/openapi.json` |
| No interactive docs | Swagger UI at `/api/docs` |

## Project structure

```
bluecat-office-provisioner/
  python/                    # Python examples (uv + ruff)
    bam_client.py            # BAM v2 API client
    examples/
      01_connect_and_sysinfo.py   # Connect, get sys info
      02_add_host_record.py       # Add A record + CNAME
      03_bulk_add_from_csv.py     # Bulk add from CSV
      04_dhcp_reservation.py      # DHCP reservation
      05_search.py                # Search objects
      06_servers_and_deploy.py    # List servers, deploy config
      07_office_template.py       # Office template provisioner
      office-template.yaml        # Sample office definition

  nodejs/                    # TypeScript examples (Bun)
    bam-client.ts            # BAM v2 API client
    examples/
      01-connect.ts               # Connect, list configs
      02-add-host.ts              # Add A record + CNAME
      03-dhcp-reservation.ts      # DHCP reservation
      04-office-template.ts       # Office template provisioner
      office-template.yaml        # Sample office definition

  research/                  # API research notes
    01-bluecat-api-overview.md    # v2 API endpoints, auth, data model
    02-opensource-ecosystem.md    # Existing libraries and SDKs
    03-office-network-design.md  # Network design best practices
    04-architecture-decision.md  # Architecture decisions
```

## Prerequisites

- **Python**: [uv](https://docs.astral.sh/uv/) (package manager)
- **Node.js**: [Bun](https://bun.sh/) (runtime)
- **BlueCat BAM**: Address Manager 9.5+ with RESTful v2 API enabled

## Python setup

```bash
cd python
uv sync

# Run an example
uv run python examples/01_connect_and_sysinfo.py

# Run the office template provisioner (dry run)
uv run python examples/07_office_template.py

# Lint and format
uv run ruff check .
uv run ruff format .
```

### Environment variables

```bash
export BAM_URL="https://bam.example.com"
export BAM_USER="admin"
export BAM_PASS="your-password"
```

## Bun (Node.js) setup

```bash
cd nodejs
bun install

# Run an example
bun examples/01-connect.ts

# Run the office template provisioner (dry run)
bun examples/04-office-template.ts
```

### Environment variables

Same as Python: `BAM_URL`, `BAM_USER`, `BAM_PASS`.

## BAM v2 API client

Both Python and Bun clients follow the same pattern:

```python
# Python
from bam_client import BAMClient

with BAMClient("https://bam.example.com", "admin", "password") as bam:
    config = bam.find_configuration("main")
    view = bam.find_view(config["id"], "default")
    zones = bam.get_zones(view["id"])
    bam.create_host_record(zone_id, "myhost", "10.0.0.50")
```

```typescript
// Bun / TypeScript
import { BAMClient } from "./bam-client";

const bam = new BAMClient("https://bam.example.com", "admin", "password");
await bam.login();

const config = await bam.findConfiguration("main");
const view = await bam.findView(config!.id, "default");
const zones = await bam.getZones(view!.id);
await bam.createHostRecord(zoneId, "myhost", "10.0.0.50");

await bam.logout();
```

### Client methods

| Method | Description |
|---|---|
| `login()` / `logout()` | Session management |
| `find_configuration(name)` | Find config by name |
| `find_view(config_id, name)` | Find DNS view by name |
| `get_zones(view_id)` | List zones in a view |
| `create_zone(view_id, name)` | Create a DNS zone |
| `create_host_record(zone_id, name, ip)` | Create A + PTR record |
| `create_alias_record(zone_id, name, target)` | Create CNAME |
| `get_blocks(config_id)` | List IP blocks |
| `create_block(config_id, cidr, name)` | Create IP block |
| `create_network(block_id, cidr, name)` | Create network/subnet |
| `assign_ip(network_id, address, mac, name)` | Assign static IP |
| `assign_next_available_ip(network_id, ...)` | Next available IP with DHCP reservation |
| `create_dhcp_range(network_id, start, end)` | Create DHCP pool |
| `get_servers(config_id)` | List BDDS servers |
| `deploy_server(server_id, services)` | Deploy config to server |
| `search(keyword, type)` | Search BAM objects |

## Office template provisioner

The template provisioner reads a YAML file that defines an entire office network and provisions it in BAM. This covers:

1. **IP block** (supernet for the office)
2. **Networks** per VLAN (Corp-Data, Corp-Voice, Corp-WiFi, Guest-WiFi, Mgmt, IoT)
3. **DNS zone** (forward zone for the office)
4. **DHCP ranges** for dynamic VLANs
5. **DHCP reservations** for hardware with known MAC addresses
6. **DNS records** (A + PTR) for all infrastructure devices
7. **WiFi SSIDs** summary for controller configuration

### Template format

```yaml
site:
  code: "chi1"
  name: "Chicago Office 1"

network:
  supernet: "10.40.0.0/20"
  domain: "chi1.corp.example.com"
  dns_servers: ["10.0.0.10", "10.0.0.11"]

vlans:
  - id: 10
    name: "Corp-Data"
    subnet: "10.40.0.0/23"
    gateway: "10.40.0.1"
    dhcp:
      type: "dynamic"
      range_start: "10.40.0.100"
      range_end: "10.40.1.254"
      lease_time: "8h"
    ddns: true

  - id: 40
    name: "Guest-WiFi"
    subnet: "10.40.8.0/23"
    gateway: "10.40.8.1"
    dhcp:
      type: "dynamic"
      range_start: "10.40.8.10"
      range_end: "10.40.9.254"
      lease_time: "2h"
    ddns: false
    wifi:
      ssid: "Guest-CHI1"
      security: "WPA3-Personal"
      captive_portal: true

hardware:
  switches:
    - { name: "sw-core01", mac: "AA:BB:CC:01:01:01", ip: "10.40.10.129", vlan: 60 }
  wireless_aps:
    - { name: "ap-1f-01", mac: "AA:BB:CC:02:01:01", ip: "10.40.10.140", vlan: 60 }
  printers:
    - { name: "pr-1f-01", mac: "AA:BB:CC:03:01:01", ip: "10.40.0.20", vlan: 10 }
  firewall:
    - { name: "fw01", ip: "10.40.10.254" }  # Static, no DHCP
```

### Running the provisioner

```bash
# Dry run (default) -- shows what would be created, no BAM connection needed
uv run python examples/07_office_template.py
bun examples/04-office-template.ts

# Live run -- connects to BAM and creates everything
DRY_RUN=false BAM_URL=https://bam.example.com uv run python examples/07_office_template.py
```

### Sample dry run output

```
[DRY RUN] Provisioning: Chicago Office 1 (chi1)
  Domain: chi1.corp.example.com
  Supernet: 10.40.0.0/20

1. Create IP block: 10.40.0.0/20

2. Create networks:
  VLAN  10 | 10.40.0.0/23       | chi1-vlan10-Corp-Data
  VLAN  20 | 10.40.2.0/24       | chi1-vlan20-Corp-Voice
  VLAN  30 | 10.40.4.0/22       | chi1-vlan30-Corp-WiFi
  VLAN  40 | 10.40.8.0/23       | chi1-vlan40-Guest-WiFi
  VLAN  60 | 10.40.10.128/26    | chi1-vlan60-Mgmt
  VLAN  70 | 10.40.11.0/24      | chi1-vlan70-IoT-BMS

3. Create DNS zone: chi1.corp.example.com

4. Create DHCP ranges:
  VLAN  10 | 10.40.0.100 - 10.40.1.254 | lease=8h
  VLAN  30 | 10.40.4.50 - 10.40.7.254 | lease=4h
  VLAN  40 | 10.40.8.10 - 10.40.9.254 | lease=2h

5. Hardware provisioning:
  switches        | sw-core01            | 10.40.10.129    | AA:BB:CC:01:01:01
  wireless_aps    | ap-1f-01             | 10.40.10.140    | AA:BB:CC:02:01:01
  printers        | pr-1f-01             | 10.40.0.20      | AA:BB:CC:03:01:01
  firewall        | fw01                 | 10.40.10.254    | (static)

6. WiFi SSIDs (configure on wireless controller):
  VLAN  30 | SSID: CorpNet-CHI1         | WPA3-Enterprise
  VLAN  40 | SSID: Guest-CHI1           | WPA3-Personal + captive portal

[DRY RUN] Total actions: 20
```

## v1 to v2 example mapping

| Original v1 file | v2 Python | v2 Bun |
|---|---|---|
| `Episode1/1-firstscript-REST.py` | `01_connect_and_sysinfo.py` | `01-connect.ts` |
| `Episode1/2-addHost-REST.py` | `02_add_host_record.py` | `02-add-host.ts` |
| `Episode1/3-bulk-addhostrecords.py` | `03_bulk_add_from_csv.py` | -- |
| `Episode2/2-assignDHCPReservation-REST.py` | `04_dhcp_reservation.py` | `03-dhcp-reservation.ts` |
| `Episode2/4-SimpleSearch-REST.py` | `05_search.py` | -- |
| `Episode6/2-getServers-REST.py` | `06_servers_and_deploy.py` | -- |
| `Episode7/2-fulldeploy-REST.py` | `06_servers_and_deploy.py` | -- |
| (new) | `07_office_template.py` | `04-office-template.ts` |

## Existing open-source ecosystem

See `research/02-opensource-ecosystem.md` for full details. Key findings:

- **Python**: Official SDK is [`bluecat-libraries`](https://pypi.org/project/bluecat-libraries/) (Apache 2.0, actively maintained). Our `bam_client.py` is a lightweight alternative using only `requests`.
- **Node.js/TypeScript**: No standalone SDK exists. Our `bam-client.ts` fills this gap.
- **Go**: [`umich-vci/gobam`](https://github.com/umich-vci/gobam) and the [lego ACME client](https://github.com/go-acme/lego) have BlueCat providers.
- **Terraform**: Official provider at [`bluecatlabs/terraform-provider-bluecat`](https://registry.terraform.io/providers/bluecatlabs/bluecat/latest).

## API version compatibility

The endpoint paths and request bodies in this project were verified against the BAM v2 API documentation (25.1.0). Some paths differ between BAM versions (9.5, 9.6, 25.1). If a call returns 404 or 400, check your BAM's Swagger UI for the exact paths your version supports.

Endpoints that are known to vary between versions:

| Operation | This repo uses | Some versions use |
|---|---|---|
| Logout | `PATCH /sessions/current` | `DELETE /sessions` |
| Create zone | `absoluteName` field | `name` field |
| DHCP range | `POST .../ranges` | `POST .../dhcpRanges` |
| Deploy server | `POST .../deployments` | `POST .../deploy` |
| Next available IP | `POST .../nextAvailableAddress` | `GET .../nextAvailableAddress` |

The definitive source is always the Swagger UI on your BAM instance at `https://<BAM_IP>/api/docs` and the OpenAPI spec at `https://<BAM_IP>/api/openapi.json`. If something doesn't match, download the OpenAPI spec from your instance and adjust the client accordingly.

## No BAM instance?

All examples work in **dry run mode** by default. The office template provisioner prints exactly what it would create without connecting to BAM. When you have access to a BAM instance, set the environment variables and use `DRY_RUN=false`.

## License

Apache 2.0 (matching the original bluecatlabs/making-apis-work-for-you).
