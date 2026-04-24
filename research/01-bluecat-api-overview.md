# BlueCat Address Manager API Overview

## API Versions

BlueCat provides **two generations** of REST API:

### Legacy v1 API (Deprecated)
- **Base URL**: `https://{BAM_IP}/Services/REST/v1/`
- RPC-style endpoints (e.g., `POST /v1/addHostRecord`, `GET /v1/getEntityById`)
- Officially called "Address Manager Legacy v1 API" as of BAM 9.5.0
- Documentation: [Legacy v1 API Guide](https://docs.bluecatnetworks.com/r/en-US/Address-Manager-Legacy-v1-API-Guide/9.5.0)

### RESTful v2 API (Recommended)
- **Base URL**: `https://{BAM_IP}/api/v2/`
- Resource-oriented REST with proper JSON responses
- OpenAPI 3.0 spec available at: `https://{BAM_IP}/api/openapi.json`
- Interactive Swagger UI at: `https://{BAM_IP}/api/docs`
- Supports filtering, field selection, ordering, pagination, HAL links
- Documentation: [RESTful v2 API Guide](https://docs.bluecatnetworks.com/r/Address-Manager-RESTful-v2-API-Guide/Introduction/25.1.0)
- Migration guide: [v1 to v2 Migration](https://docs.bluecatnetworks.com/r/Address-Manager-RESTful-v2-API-Guide/v1-REST-API-to-RESTful-v2-API-migration-guide/9.5.0)

---

## Authentication

### v1 API - Session Token
```
GET /Services/REST/v1/login?username={user}&password={pass}
```
Returns a session token string, passed in `Authorization` header.

### v2 API - Two Methods

**Session creation:**
```http
POST /api/v2/sessions
Content-Type: application/json

{"username": "user1", "password": "pass1"}
```

Response includes:
- `apiToken` - token for auth headers
- `apiTokenExpirationDateTime` - typically 24 hours
- `basicAuthenticationCredentials` - pre-encoded base64 credentials

**Basic Auth**: `Authorization: Basic {base64(username:apiToken)}`
**Bearer Auth**: `Authorization: Bearer {apiToken}`

### BlueCat Gateway
- `POST /rest_login` with JSON `{"username": "...", "password": "..."}`
- Returns `access_token` for `auth: Basic <Token>` header

---

## Data Model (Hierarchical)

```
Configuration (top-level container)
  |
  +-- View (DNS views for split-horizon)
  |     +-- Zone (forward/reverse DNS zones)
  |           +-- Resource Records (A, CNAME, MX, SRV, TXT, etc.)
  |
  +-- IP4Block / IP6Block (large address space, e.g., /8, /16)
        +-- IP4Network / IP6Network (subnets)
              +-- IP4Address / IP6Address (individual IPs with state)
              +-- DHCP4Range / DHCP6Range (dynamic pools)
```

### Key Entity Types (90+)
- **DNS**: Zone, ZoneTemplate, HostRecord, AliasRecord, MXRecord, SRVRecord, TXTRecord, GenericRecord, ResponsePolicy, DNSSEC keys
- **IPAM**: IP4Block, IP6Block, IP4Network, IP6Network, IP4Address, IP6Address, IPGroup
- **DHCP**: DHCP4Range, DHCP6Range, DHCPMatchClass, DeploymentOption, DeploymentRole
- **Infrastructure**: Server, ServerInterface, XHAPair, TFTPGroup
- **Admin**: User, UserGroup, AccessRight, ACL, Tag, TagGroup, UserDefinedField
- **Inventory**: Device, DeviceType, Location, MACAddress, MACPool

---

## Key API Endpoints

### DNS Management
| Operation | v1 | v2 |
|---|---|---|
| Add zone | `POST /v1/addZone` | `POST /api/v2/views/{id}/zones` |
| Add host record | `POST /v1/addHostRecord` | `POST /api/v2/resourceRecords` |
| Add CNAME | `POST /v1/addAliasRecord` | `POST /api/v2/resourceRecords` |
| DNS deployment role | `POST /v1/addDNSDeploymentRole` | `POST /api/v2/.../deploymentRoles` |

### DHCP Management
| Operation | v1 |
|---|---|
| Add DHCP4 range | `POST /v1/addDHCP4Range` |
| Add DHCP4 range by size | `POST /v1/addDHCP4RangeBySize` |
| DHCP client option | `POST /v1/addDHCPClientDeploymentOption` |
| DHCP deployment role | `POST /v1/addDHCPDeploymentRole` |

### IPAM
| Operation | v1 | v2 |
|---|---|---|
| Add IPv4 block | `POST /v1/addIP4BlockByCIDR` | `POST /api/v2/configurations/{id}/blocks` |
| Add IPv4 network | `POST /v1/addIP4Network` | `POST /api/v2/blocks/{id}/networks` |
| Assign IP | `POST /v1/assignIP4Address` | via `/api/v2/networks/{id}/addresses` |
| Next available IP | `POST /v1/assignNextAvailableIP4Address` | `nextAvailableAddress` endpoint |

### Generic Operations (v1)
- `GET /v1/getEntityById` - retrieve any entity
- `GET /v1/getEntities` - get children
- `GET /v1/customSearch` - search across types
- `PUT /v1/update` - update any entity
- `DELETE /v1/delete` - delete any entity

---

## Official SDKs

### Python - `bluecat-libraries` (Official)
```bash
pip install bluecat-libraries
```
- Supports BAM v2 API (9.5, 9.6, 25.1)
- Core classes: `Client`, `BAMV2ErrorResponse`, `MediaType`
- HTTP methods: `http_get`, `http_post`, `http_put`, `http_patch`, `http_delete`
- Standalone (no Gateway dependency)

### OpenAPI-Generated SDKs
Use `https://{BAM_IP}/api/openapi.json` with `openapi-generator` to build clients in any language (including Node.js/TypeScript).

---

## Key Recommendations

1. **Use v2 API** for all new development - v1 is deprecated
2. **Best documentation source** is the Swagger UI on your own BAM instance at `/api/docs`
3. **Official Python SDK** is `bluecat-libraries` on PyPI
4. **No official Node.js SDK** exists - generate from OpenAPI spec or build custom
5. **Authentication** is session-based with ~24h token expiry
