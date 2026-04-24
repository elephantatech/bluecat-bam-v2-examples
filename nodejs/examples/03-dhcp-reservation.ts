/**
 * Episode 2 (v2): DHCP reservation with next available IP.
 * Run: bun examples/03-dhcp-reservation.ts
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

const MAC = "BB:CC:DD:AA:AA:AA";
const HOSTNAME = "appsrv23";
const NETWORK_CIDR = "192.168.3.0/24";

await bam.login();

const config = await bam.findConfiguration("main");
const blocks = await bam.getBlocks(config.id);

let network = null;
for (const block of blocks.data ?? []) {
  const nets = await bam.getNetworks(block.id);
  network = nets.data?.find((n) => n.range === NETWORK_CIDR) ?? null;
  if (network) break;
}

if (!network) {
  console.error(`Network ${NETWORK_CIDR} not found`);
  process.exit(1);
}

console.log(`Network: [${network.id}] ${network.range}`);

const result = await bam.assignNextAvailableIp(network.id, {
  mac: MAC,
  name: HOSTNAME,
  action: "MAKE_DHCP_RESERVED",
});
console.log("\nReservation created:", result);

await bam.logout();
