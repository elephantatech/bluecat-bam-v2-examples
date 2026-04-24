/**
 * Episode 1 (v2): Connect to BAM, list configs.
 * Run: bun examples/01-connect.ts
 */

import { BAMClient } from "../bam-client";

const bam = new BAMClient(
  Bun.env.BAM_URL ?? "https://bam.lab.corp",
  Bun.env.BAM_USER ?? "admin",
  Bun.env.BAM_PASS ?? "admin",
);

await bam.login();
console.log("Connected to BAM\n");

const configs = await bam.getConfigurations();
console.log("=== Configurations ===");
for (const cfg of configs.data ?? []) {
  console.log(`  [${cfg.id}] ${cfg.name}`);
}

await bam.logout();
console.log("\nDone.");
