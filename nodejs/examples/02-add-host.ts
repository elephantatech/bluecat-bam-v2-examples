/**
 * Episode 1 (v2): Add a host record + CNAME alias.
 * Run: bun examples/02-add-host.ts
 * Env: BAM_URL, BAM_USER, BAM_PASS
 */

import { BAMClient } from "../bam-client";

const bamUrl = Bun.env.BAM_URL ?? "https://bam.lab.corp";
const bamUser = Bun.env.BAM_USER ?? "admin";
const bamPass = Bun.env.BAM_PASS;
if (!bamPass) {
  console.error("Set BAM_PASS environment variable.");
  process.exit(1);
}

const bam = new BAMClient(bamUrl, bamUser, bamPass);

const HOSTNAME = "FINRPT02";
const IP = "192.168.0.16";
const ALIAS = "reporting2";
const ZONE = "lab.corp";

await bam.login();

const config = await bam.findConfiguration("main");
console.log(`Config: [${config.id}] ${config.name}`);

const view = await bam.findView(config.id, "default");
console.log(`View: [${view.id}] ${view.name}`);

const zones = await bam.getZones(view.id);
const zone = zones.data?.find((z) => z.name === ZONE);
if (!zone) {
  console.error(`Zone '${ZONE}' not found`);
  process.exit(1);
}
console.log(`Zone: [${zone.id}] ${zone.name}`);

// Create host record (A + PTR)
const host = await bam.createHostRecord(zone.id, HOSTNAME, IP);
console.log("\nHost created:", host);

// Create CNAME
const alias = await bam.createAliasRecord(zone.id, ALIAS, `${HOSTNAME}.${ZONE}`);
console.log("Alias created:", alias);

await bam.logout();
