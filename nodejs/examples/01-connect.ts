/**
 * Episode 1 (v2): Connect to BAM, list configs.
 * Run: bun examples/01-connect.ts
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

await bam.login();
console.log("Connected to BAM\n");

const configs = await bam.getConfigurations();
console.log("=== Configurations ===");
for (const cfg of configs.data ?? []) {
  console.log(`  [${cfg.id}] ${cfg.name}`);
}

await bam.logout();
console.log("\nDone.");
