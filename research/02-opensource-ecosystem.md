# BlueCat Open-Source Ecosystem

## Official Libraries (from BlueCat)

### bluecat-libraries (Python) - RECOMMENDED
- **PyPI**: [bluecat-libraries](https://pypi.org/project/bluecat-libraries/)
- **Python**: >=3.11.0
- **License**: Apache Software License
- **Latest**: 25.3.0 (Nov 2025) - active releases every few months
- **Coverage**: BAM v2 API (9.5, 9.6, 25.1), Legacy v1 API, Failover API, DNS Edge API
- **Status**: Actively maintained, production-ready

### bluecatlabs/gateway-workflows
- **Repo**: [github.com/bluecatlabs/gateway-workflows](https://github.com/bluecatlabs/gateway-workflows)
- **Stars**: ~55 | **License**: Apache 2.0
- **Purpose**: Example/community workflows for BlueCat Gateway
- **Status**: Actively maintained, accepts contributions

### bluecatlabs/terraform-provider-bluecat
- **Registry**: [Terraform Registry](https://registry.terraform.io/providers/bluecatlabs/bluecat/latest)
- **Downloads**: 258K+ all-time
- **Status**: Actively maintained

### bluecatlabs/bluecat-gateway-ansible-module
- **Purpose**: Ansible playbooks for IPAM/DNS/DHCP via Gateway REST API
- **Status**: Official, moderate activity

### bluecatlabs/making-apis-work-for-you
- **Purpose**: Sample code from BlueCat webinar series (SOAP + REST)
- **Status**: Educational/reference

---

## Community Python Libraries

### ForrestT/pyBluecat
- **PyPI**: [pybluecat](https://pypi.org/project/pybluecat/)
- **Stars**: 7 | **Forks**: 8
- **API**: v1 REST API wrapper
- **Status**: Low activity, likely unmaintained

### marcowartmann/py-bluecat-bam-sdk
- **Purpose**: Python SDK for BAM API v2 with API models
- **Status**: Newer community project, low stars

### quistian/BAM-CLI / bamcli
- **Purpose**: Python library and CLI for v1 and v2 APIs
- **Status**: Active development

### struegamer/proteus-api
- **Stars**: 16 | **Forks**: 14 | **License**: LGPL-2.1
- **Purpose**: SOAP API wrapper for older Proteus systems
- **Status**: Legacy

### University of Michigan - bluecat_bam (GitLab)
- **Repo**: [gitlab.umich.edu/its-public/bluecat_bam](https://gitlab.umich.edu/its-public/bluecat_bam)
- **Purpose**: BAM REST API module + CLI with CI/CD

---

## Go Libraries

### umich-vci/gobam
- **Docs**: [pkg.go.dev](https://pkg.go.dev/github.com/umich-vci/gobam)
- **License**: MPL-2.0
- **Purpose**: Full Go client for BAM API
- **Status**: Foundation for UMich Terraform provider

### go-acme/lego (BlueCat DNS provider)
- **Purpose**: ACME/Let's Encrypt client with built-in BlueCat DNS provider
- **Status**: Actively maintained - good reference for API integration

---

## Node.js / JavaScript - GAPS IDENTIFIED

### @itentialopensource/adapter-bluecat
- **npm**: [@itentialopensource/adapter-bluecat](https://www.npmjs.com/package/@itentialopensource/adapter-bluecat)
- **Purpose**: BlueCat adapter for Itential Automation Platform
- **Status**: Platform-specific, NOT a standalone SDK

### chenchaoyi/bluecat (npm)
- **Note**: Generic REST testing framework, NOT related to BlueCat Networks

### FINDING: No standalone Node.js/TypeScript SDK exists for BlueCat BAM

---

## PowerShell

- **Bluecat.Address.Manager** - PowerShell Gallery module
- **chelnak/BAM-API-PowerShell** - PowerShell functions for SOAP API
- **ccamacho1966/BlueCatPoSh** - Enhanced PowerShell library

---

## Ansible

- **jonjozwiak/bluecat-ipam-rest** - Direct BAM REST API (no Gateway needed)
- **automateyournetwork/BlueCatAddressManagerNetworkFacts** - Reporting playbook

---

## Summary & Contribution Strategy

| Project | Lang | Maintained | Contribute? |
|---|---|---|---|
| **bluecat-libraries** | Python | Yes (official) | Fork/extend for our needs |
| **py-bluecat-bam-sdk** | Python | New | Potential contribution target |
| **gobam** | Go | Moderate | Reference implementation |
| **adapter-bluecat** | Node.js | Moderate | Too platform-specific |

### Recommendations

1. **Python**: Use official `bluecat-libraries` as the foundation. No need to reinvent.
2. **Node.js**: **Build a new open-source SDK** - this is the biggest gap in the ecosystem. Generate initial client from OpenAPI spec, then add higher-level abstractions.
3. **Contribution opportunity**: The `py-bluecat-bam-sdk` project could benefit from contributions adding office provisioning workflows.
4. **OpenAPI approach**: Both Python and Node.js clients can be bootstrapped from the BAM OpenAPI spec at `/api/openapi.json`.
