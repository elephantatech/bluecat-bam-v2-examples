/**
 * BlueCat Address Manager v2 API Client
 *
 * Simple TypeScript client for BAM RESTful v2 API.
 * Uses native fetch (Bun built-in).
 *
 * Usage:
 *   import { BAMClient } from './bam-client';
 *   const bam = new BAMClient('https://bam.example.com', 'admin', 'password');
 *   await bam.login();
 *   const configs = await bam.getConfigurations();
 *   await bam.logout();
 */

interface BAMEntity {
  id: number;
  name: string;
  type?: string;
  [key: string]: unknown;
}

interface BAMCollection {
  data: BAMEntity[];
  count?: number;
}

export class BAMClient {
  private apiUrl: string;
  private token: string | null = null;

  constructor(
    url: string,
    private username: string,
    private password: string,
  ) {
    this.apiUrl = `${url.replace(/\/$/, "")}/api/v2`;
  }

  // --- Session ---

  async login() {
    const resp = await fetch(`${this.apiUrl}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: this.username, password: this.password }),
      tls: { rejectUnauthorized: false },
    } as RequestInit);
    if (!resp.ok) throw new Error(`Login failed: ${resp.status}`);
    const data = await resp.json();
    this.token = data.apiToken;
    return data;
  }

  async logout() {
    if (!this.token) return;
    await this.apiFetch("/sessions", { method: "DELETE" });
    this.token = null;
  }

  // --- Low-level helpers ---

  private async apiFetch(path: string, options: RequestInit = {}) {
    const resp = await fetch(`${this.apiUrl}${path}`, {
      ...options,
      headers: {
        Authorization: `Bearer ${this.token}`,
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string>),
      },
      tls: { rejectUnauthorized: false },
    } as RequestInit);
    if (!resp.ok) {
      const body = await resp.text();
      throw new Error(`BAM API ${resp.status}: ${body}`);
    }
    if (resp.status === 204) return null;
    return resp.json();
  }

  async get(path: string, params: Record<string, unknown> = {}): Promise<BAMCollection> {
    const qs = new URLSearchParams(params as Record<string, string>).toString();
    const url = qs ? `${path}?${qs}` : path;
    return this.apiFetch(url);
  }

  async post(path: string, data: unknown) {
    return this.apiFetch(path, { method: "POST", body: JSON.stringify(data) });
  }

  async put(path: string, data: unknown) {
    return this.apiFetch(path, { method: "PUT", body: JSON.stringify(data) });
  }

  async del(path: string) {
    return this.apiFetch(path, { method: "DELETE" });
  }

  // --- Configurations ---

  getConfigurations() {
    return this.get("/configurations");
  }

  async findConfiguration(name: string): Promise<BAMEntity | null> {
    const r = await this.get("/configurations", { filter: `name:eq('${name}')` });
    return r?.data?.[0] ?? null;
  }

  // --- Views ---

  getViews(configId: number) {
    return this.get(`/configurations/${configId}/views`);
  }

  async findView(configId: number, name: string): Promise<BAMEntity | null> {
    const r = await this.get(`/configurations/${configId}/views`, {
      filter: `name:eq('${name}')`,
    });
    return r?.data?.[0] ?? null;
  }

  // --- Zones ---

  getZones(viewId: number) {
    return this.get(`/views/${viewId}/zones`);
  }

  createZone(viewId: number, name: string) {
    return this.post(`/views/${viewId}/zones`, { type: "Zone", name });
  }

  // --- Resource Records ---

  createHostRecord(zoneId: number, name: string, ip: string, reverse = true) {
    return this.post(`/zones/${zoneId}/resourceRecords`, {
      type: "HostRecord",
      name,
      addresses: [{ address: ip }],
      reverseRecord: reverse,
    });
  }

  createAliasRecord(zoneId: number, name: string, linkedRecord: string) {
    return this.post(`/zones/${zoneId}/resourceRecords`, {
      type: "AliasRecord",
      name,
      linkedRecord,
    });
  }

  getResourceRecords(zoneId: number) {
    return this.get(`/zones/${zoneId}/resourceRecords`);
  }

  deleteResourceRecord(recordId: number) {
    return this.del(`/resourceRecords/${recordId}`);
  }

  // --- IP Blocks & Networks ---

  getBlocks(configId: number) {
    return this.get(`/configurations/${configId}/blocks`);
  }

  createBlock(configId: number, cidr: string, name?: string) {
    const data: Record<string, string> = { range: cidr };
    if (name) data.name = name;
    return this.post(`/configurations/${configId}/blocks`, data);
  }

  getNetworks(blockId: number) {
    return this.get(`/blocks/${blockId}/networks`);
  }

  createNetwork(blockId: number, cidr: string, name?: string) {
    const data: Record<string, string> = { range: cidr };
    if (name) data.name = name;
    return this.post(`/blocks/${blockId}/networks`, data);
  }

  // --- IP Addresses ---

  assignIp(
    networkId: number,
    address: string,
    opts: { mac?: string; name?: string; action?: string } = {},
  ) {
    const data: Record<string, string> = { address, action: opts.action ?? "MAKE_STATIC" };
    if (opts.mac) data.macAddress = opts.mac;
    if (opts.name) data.name = opts.name;
    return this.post(`/networks/${networkId}/addresses`, data);
  }

  assignNextAvailableIp(
    networkId: number,
    opts: { mac?: string; name?: string; action?: string } = {},
  ) {
    const data: Record<string, string> = { action: opts.action ?? "MAKE_DHCP_RESERVED" };
    if (opts.mac) data.macAddress = opts.mac;
    if (opts.name) data.name = opts.name;
    return this.post(`/networks/${networkId}/nextAvailableAddress`, data);
  }

  // --- DHCP ---

  createDhcpRange(networkId: number, start: string, end: string) {
    return this.post(`/networks/${networkId}/dhcpRanges`, { start, end });
  }

  // --- Servers ---

  getServers(configId: number) {
    return this.get(`/configurations/${configId}/servers`);
  }

  deployServer(serverId: number, services = "DNS,DHCP") {
    return this.post(`/servers/${serverId}/deploy`, { services });
  }

  // --- Search ---

  search(keyword: string, opts: { type?: string; limit?: number } = {}) {
    const params: Record<string, unknown> = {
      filter: `keyword:contains('${keyword}')`,
      limit: opts.limit ?? 100,
    };
    if (opts.type) params.type = opts.type;
    return this.get("/search", params);
  }
}
