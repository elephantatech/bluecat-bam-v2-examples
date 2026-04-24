# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-04-24

### Added

- **Python BAM v2 API client** (`python/bam_client.py`) -- lightweight client using `requests` for BlueCat Address Manager RESTful v2 API
- **Bun/TypeScript BAM v2 API client** (`nodejs/bam-client.ts`) -- typed client using native `fetch`
- **Python examples** rewritten from the original [bluecatlabs/making-apis-work-for-you](https://github.com/bluecatlabs/making-apis-work-for-you) v1 examples:
  - `01_connect_and_sysinfo.py` -- connect and get system info (replaces Episode 1)
  - `02_add_host_record.py` -- create A + CNAME records (replaces Episode 1)
  - `03_bulk_add_from_csv.py` -- bulk host records from CSV (replaces Episode 1)
  - `04_dhcp_reservation.py` -- DHCP reservation with next available IP (replaces Episode 2)
  - `05_search.py` -- search BAM objects (replaces Episodes 2/3)
  - `06_servers_and_deploy.py` -- list servers and deploy config (replaces Episodes 6/7)
  - `07_office_template.py` -- office network provisioner from YAML template (new)
- **Bun/TypeScript examples** with feature parity:
  - `01-connect.ts`, `02-add-host.ts`, `03-dhcp-reservation.ts`, `04-office-template.ts`
- **Office template format** (`office-template.yaml`) -- YAML-based office network definition covering VLANs, DHCP pools, reservations, DNS zones, hardware inventory, and WiFi SSIDs
- **Dry run mode** -- all examples run without a BAM connection by default
- **Research documentation** covering BAM v2 API, open-source ecosystem, office network design patterns
- Python project management with **uv** and linting with **ruff**
- Node.js runtime via **Bun** with native TypeScript support
- Apache 2.0 license

### Changed

- All API calls migrated from BAM v1 REST/SOAP to **RESTful v2 API**
- Authentication changed from v1 token-parsing (`"Session Token-> BAMAuthToken: ..."`) to v2 JSON sessions (`POST /api/v2/sessions`)
- Entity responses changed from pipe-delimited property strings to proper JSON objects
- Endpoint style changed from RPC (`/v1/addHostRecord?viewId=...`) to REST resources (`/api/v2/zones/{id}/resourceRecords`)
