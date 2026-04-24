# Architecture Decision Record

## Context

We need a library that works with BlueCat Address Manager for automating office network provisioning (DNS, DHCP, IPAM) across Python and Node.js projects.

## Decision: Dual-Language SDK + Shared Provisioning Logic

### Python Strategy
- **Use official `bluecat-libraries`** as the API client layer
- Build higher-level provisioning workflows on top
- No need to reinvent the API client

### Node.js Strategy
- **Generate TypeScript client from OpenAPI spec** (`/api/openapi.json`)
- Build higher-level provisioning workflows matching Python parity
- This fills the biggest gap in the open-source ecosystem

### Contribution Strategy
- **Upstream contributions**: Consider contributing Node.js SDK back as an open-source package
- **py-bluecat-bam-sdk**: Could contribute provisioning workflows there
- **Official repo**: Gateway workflows repo accepts contributions

## Project Structure

```
bluecat-office-provisioner/
  research/               # This research
  shared/
    schemas/              # Shared JSON schemas for office config
    templates/            # VLAN/subnet templates
  python/
    src/
      provisioner/        # High-level provisioning logic
      bluecat_client/     # Thin wrapper over bluecat-libraries
  nodejs/
    src/
      provisioner/        # High-level provisioning logic (parity with Python)
      bluecat-client/     # Generated from OpenAPI + custom extensions
  examples/
    new-office.yaml       # Sample office definition
```

## Key Design Decisions

1. **v2 API only** - v1 is deprecated, no point supporting it
2. **OpenAPI-first for Node.js** - generate client, add typings
3. **Shared schemas** - office definition format shared between languages
4. **Template-driven** - standard VLAN/subnet templates with overrides
5. **Idempotent operations** - safe to re-run provisioning

## Open Questions

- [ ] Do we have access to a BAM instance for testing?
- [ ] Which BAM version are we targeting? (9.5, 9.6, or 25.1)
- [ ] Should we support BlueCat Gateway as an alternative endpoint?
- [ ] What's the MAC address collection workflow for new hardware?
- [ ] Do we need 802.1X/NAC integration?
