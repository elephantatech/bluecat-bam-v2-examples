# Office Network Provisioning - Design Patterns

## 1. Network Segmentation (VLAN Layout)

| VLAN ID | Name | Purpose | Typical Subnet |
|---|---|---|---|
| 10 | Corp-Data | Wired workstations, docked laptops | /23 or /24 |
| 20 | Corp-Voice | IP phones (QoS priority) | /24 |
| 30 | Corp-WiFi | Corporate wireless (802.1X) | /22 or /23 |
| 40 | Guest-WiFi | Captive-portal guest access (isolated) | /23 or /24 |
| 50 | Infra/Servers | On-prem servers, hypervisors, UPS mgmt | /25 or /26 |
| 60 | Mgmt | Switch/AP/IPMI management interfaces | /26 or /27 |
| 70 | IoT/BMS | HVAC, cameras, badge readers, sensors | /24 |
| 99 | Native | Trunk native VLAN (unused, security) | N/A |

### Segmentation Rules
- Guest WiFi: fully isolated, internet-only via captive portal
- IoT/BMS: untrusted, no access to corporate VLANs
- Management: reachable only from jump host / admin workstation
- Voice: separated for QoS (DSCP marking, priority queuing)

---

## 2. DHCP Design

### Static Reservations (MAC-based)

| Device Type | Why Static | Count per Office |
|---|---|---|
| Network printers/MFPs | Print queues reference IP | 2-10 |
| IP phones | Provisioning/E911 mapping | 1 per desk |
| Wireless access points | Controller/monitoring | 5-50 |
| Network switches | SNMP/syslog/monitoring | 3-20 |
| Servers/appliances | DNS records, services | 2-10 |
| Security cameras | NVR configuration | 5-30 |
| Badge readers | Access control system | 5-20 |
| UPS (network-managed) | Monitoring | 2-4 |

### Dynamic DHCP Pools

| Device Type | VLAN |
|---|---|
| Laptops (wired) | Corp-Data |
| Laptops/phones (WiFi) | Corp-WiFi |
| Guest devices | Guest-WiFi |
| Personal IoT | IoT |

### Subnet Sizing Rules
- **Small (25-50 users)**: /24 per VLAN
- **Medium (50-200 users)**: /23 data/WiFi, /24 voice, /25-/26 infra
- **Large (200-500+ users)**: /22 WiFi, /23 data, /24 voice
- **WiFi needs 2-3x user count** (multiple devices per person)

### DHCP Options

| Option | # | Purpose | Typical Value |
|---|---|---|---|
| DNS servers | 6 | Name resolution | Internal DNS IPs |
| Domain name | 15 | Search suffix | `{site}.corp.example.com` |
| Default gateway | 3 | Routing | First usable IP |
| Lease (corporate) | 51 | Address retention | 8-12h wired, 4-8h WiFi |
| Lease (guest) | 51 | Address turnover | 1-2h |
| NTP servers | 42 | Time sync | Internal NTP |
| TFTP server | 66 | Phone/AP provisioning | Provisioning server IP |
| Voice VLAN | 150 | Phone VLAN discovery | VLAN ID |

---

## 3. DNS Requirements

### Forward Zones
```
{site-code}.corp.example.com
```

Example (`chi1` = Chicago site 1):
```dns
sw-core01.chi1.corp.example.com.    A    10.40.1.1
ap-3f-01.chi1.corp.example.com.     A    10.40.1.10
fw01.chi1.corp.example.com.         A    10.40.1.254
pr-3f-01.chi1.corp.example.com.     A    10.40.10.20
```

### Reverse Zones
PTR zones for each subnet. Every static reservation needs a PTR record.

### DDNS Configuration
- **Corporate wired/WiFi**: DHCP server registers A + PTR via TSIG-signed updates
- **Domain-joined Windows**: Machine registers A, DHCP registers PTR
- **Guest network**: No DDNS
- **Scavenging**: Enable aging (no-refresh = half DHCP lease time)

### Naming Conventions
```
<role><sequence>.<site>.<domain>
```

| Device | Example |
|---|---|
| Core switch | `sw-core01.chi1.corp.example.com` |
| Access switch | `sw-acc01.chi1.corp.example.com` |
| Access point | `ap-3f-01.chi1.corp.example.com` |
| Firewall | `fw01.chi1.corp.example.com` |
| Printer | `pr-3f-01.chi1.corp.example.com` |
| IP phone | `phone-3f-042.chi1.corp.example.com` |

---

## 4. Hardware Inventory (Medium Office, ~100 users, 2 floors)

| Category | Device | Qty | Static IP | MAC Reservation |
|---|---|---|---|---|
| Security | Firewall/router | 1-2 (HA) | Yes (manual) | No |
| Switching | Core switch (L3) | 1-2 | Yes | N/A |
| | Access switches (L2, PoE+) | 4-8 | Yes | N/A |
| Wireless | Access points (Wi-Fi 6/6E) | 8-15 | Yes | Yes |
| Telephony | IP phones | 50-100 | Yes | Yes |
| Printing | Network printers/MFPs | 3-6 | Yes | Yes |
| Servers | Local AD/DNS/DHCP | 1-2 | Yes (static) | No |
| Surveillance | IP cameras | 10-30 | Yes | Yes |
| Access Control | Badge readers | 5-15 | Yes | Yes |
| | NVR | 1 | Yes | No |
| Power | Network-managed UPS | 2-4 | Yes | Yes |
| Conference | Video units | 2-6 | Optional | Optional |
| Building | HVAC/lighting/sensors | Varies | Yes | Yes |

---

## 5. Provisioning Intake Questionnaire

### Site Identification
- Office location code (e.g., "chi1", "lon2", "sfo3")
- Physical address (E911, compliance)
- Region / time zone
- Parent site (hub connection)

### Capacity Planning
- Number of employees / desks
- Number of floors
- Expected visitors / contractors
- Growth forecast (1yr, 3yr)

### Network Allocation
- WAN circuit type (MPLS, SD-WAN, DIA)
- Supernet allocation (e.g., "assign /20 from 10.0.0.0/8")
- VLAN scheme (standard template or custom)

### Hardware Manifest
- Switch/AP/printer/phone counts
- MAC addresses for all reservation devices
- Floor plans / AP placement maps

### Services
- Local servers required?
- DNS: local resolver or relay to central?
- DHCP: local or centralized with relay?
- VoIP: on-prem PBX vs cloud UCaaS?
- Guest WiFi captive portal: local or cloud?

### Security & Compliance
- 802.1X / NAC required?
- Regulatory (PCI, HIPAA)?
- VPN: local or central concentrator?

---

## 6. Automation Pipeline

1. **IPAM allocation** - Carve subnets from supernet per VLAN sizing rules
2. **DNS zone creation** - Forward zone + reverse zones, populate infra records
3. **DHCP scope creation** - Scopes per VLAN with options, exclusions, reservations
4. **Config generation** - Switch/FW/AP configs from templates (Jinja2/Ansible)
5. **Monitoring onboarding** - SNMP, syslog, alerting for all infra devices
6. **Validation** - Ping sweep, DNS checks, DHCP offer tests, VLAN isolation verify
