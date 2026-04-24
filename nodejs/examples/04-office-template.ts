/**
 * Office Template Provisioner (Bun)
 *
 * Reads the YAML office template and provisions in BAM.
 * Dry-run by default -- set DRY_RUN=false to execute against BAM.
 * Run: bun examples/04-office-template.ts
 */

import { readFileSync } from "node:fs";
import { join } from "node:path";
import yaml from "js-yaml";
import { BAMClient } from "../bam-client";

const TEMPLATE_PATH = join(import.meta.dir, "office-template.yaml");

interface OfficeTemplate {
  site: { code: string; name: string };
  network: {
    supernet: string;
    domain: string;
    dns_servers: string[];
    ntp_servers?: string[];
    bam_config?: string;
    bam_view?: string;
  };
  vlans: Array<{
    id: number;
    name: string;
    subnet: string;
    gateway: string;
    dhcp?: { type: string; range_start?: string; range_end?: string; lease_time?: string };
    ddns?: boolean;
    wifi?: { ssid: string; security: string; captive_portal?: boolean };
  }>;
  hardware: Record<string, Array<{ name: string; mac?: string; ip?: string; vlan?: number }>>;
}

async function provisionOffice(bam: BAMClient | null, t: OfficeTemplate, dryRun = true) {
  const tag = dryRun ? "[DRY RUN] " : "";
  console.log(`${tag}Provisioning: ${t.site.name} (${t.site.code})`);
  console.log(`  Domain: ${t.network.domain}`);
  console.log(`  Supernet: ${t.network.supernet}`);

  const actions: Record<string, unknown>[] = [];
  const configName = t.network.bam_config ?? "main";
  const viewName = t.network.bam_view ?? "default";

  // Resolved BAM objects (populated in live mode)
  let config = { id: 0 };
  let view = { id: 0 };
  let block = { id: 0 };
  let zone = { id: 0 };
  const networksCreated: Record<number, { id: number }> = {};

  if (!dryRun && bam) {
    config = await bam.findConfiguration(configName);
    view = await bam.findView(config.id, viewName);
  }

  // 1. IP block
  console.log(`\n1. Create IP block: ${t.network.supernet}`);
  actions.push({ action: "create_block", cidr: t.network.supernet });
  if (!dryRun && bam) {
    block = (await bam.createBlock(config.id, t.network.supernet, `${t.site.code}-supernet`)) as { id: number };
  }

  // 2. Networks per VLAN
  console.log("\n2. Create networks:");
  for (const vlan of t.vlans) {
    const name = `${t.site.code}-vlan${vlan.id}-${vlan.name}`;
    console.log(`  VLAN ${String(vlan.id).padStart(3)} | ${vlan.subnet.padEnd(18)} | ${name}`);
    actions.push({ action: "create_network", cidr: vlan.subnet, name });
    if (!dryRun && bam) {
      networksCreated[vlan.id] = (await bam.createNetwork(block.id, vlan.subnet, name)) as { id: number };
    }
  }

  // 3. DNS zone
  console.log(`\n3. Create DNS zone: ${t.network.domain}`);
  actions.push({ action: "create_zone", name: t.network.domain });
  if (!dryRun && bam) {
    zone = (await bam.createZone(view.id, t.network.domain)) as { id: number };
  }

  // 4. DHCP ranges
  console.log("\n4. Create DHCP ranges:");
  for (const vlan of t.vlans) {
    const dhcp = vlan.dhcp;
    if (dhcp?.type === "dynamic" && dhcp.range_start && dhcp.range_end) {
      console.log(
        `  VLAN ${String(vlan.id).padStart(3)} | ${dhcp.range_start} - ${dhcp.range_end} | lease=${dhcp.lease_time ?? "8h"}`,
      );
      actions.push({ action: "create_dhcp_range", start: dhcp.range_start, end: dhcp.range_end });
      if (!dryRun && bam) {
        const net = networksCreated[vlan.id];
        if (net) await bam.createDhcpRange(net.id, dhcp.range_start, dhcp.range_end);
      }
    }
  }

  // 5. Hardware
  console.log("\n5. Hardware provisioning:");
  for (const [deviceType, devices] of Object.entries(t.hardware ?? {})) {
    for (const device of devices) {
      if (device.mac && device.ip) {
        console.log(
          `  ${deviceType.padEnd(15)} | ${device.name.padEnd(20)} | ${device.ip.padEnd(15)} | ${device.mac}`,
        );
        actions.push({ action: "reserve_and_register", ...device, type: deviceType });
        if (!dryRun && bam) {
          const net = device.vlan != null ? networksCreated[device.vlan] : undefined;
          if (net) {
            await bam.assignIp(net.id, device.ip, {
              mac: device.mac,
              name: device.name,
              action: "MAKE_DHCP_RESERVED",
            });
          }
          await bam.createHostRecord(zone.id, device.name, device.ip);
        }
      } else if (device.ip) {
        console.log(
          `  ${deviceType.padEnd(15)} | ${device.name.padEnd(20)} | ${device.ip.padEnd(15)} | (static)`,
        );
        actions.push({ action: "dns_only", name: device.name, ip: device.ip });
        if (!dryRun && bam) {
          await bam.createHostRecord(zone.id, device.name, device.ip);
        }
      }
    }
  }

  // 6. WiFi
  console.log("\n6. WiFi SSIDs (configure on controller):");
  for (const vlan of t.vlans) {
    if (vlan.wifi) {
      const portal = vlan.wifi.captive_portal ? " + captive portal" : "";
      console.log(
        `  VLAN ${String(vlan.id).padStart(3)} | SSID: ${vlan.wifi.ssid.padEnd(20)} | ${vlan.wifi.security}${portal}`,
      );
    }
  }

  console.log(`\n${tag}Total actions: ${actions.length}`);
  return actions;
}

// --- Main ---
let template: OfficeTemplate;
try {
  template = yaml.load(readFileSync(TEMPLATE_PATH, "utf8")) as OfficeTemplate;
} catch (err) {
  console.error(`Failed to load template: ${TEMPLATE_PATH}`);
  console.error(err instanceof Error ? err.message : err);
  process.exit(1);
}

const dryRun = (Bun.env.DRY_RUN ?? "true").toLowerCase() !== "false";

if (dryRun) {
  await provisionOffice(null, template, true);
} else {
  const bamUrl = Bun.env.BAM_URL;
  const bamUser = Bun.env.BAM_USER;
  const bamPass = Bun.env.BAM_PASS;
  if (!bamUrl || !bamUser || !bamPass) {
    console.error("BAM_URL, BAM_USER, and BAM_PASS must be set for live mode.");
    process.exit(1);
  }
  const bam = new BAMClient(bamUrl, bamUser, bamPass);
  await bam.login();
  try {
    await provisionOffice(bam, template, false);
  } finally {
    await bam.logout();
  }
}
