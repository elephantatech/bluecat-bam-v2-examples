/**
 * BlueCat Address Manager v2 API Client
 *
 * Simple TypeScript client for BAM RESTful v2 API.
 * Uses native fetch (Bun built-in).
 *
 * NOTE: Endpoint paths verified against BAM v2 docs (25.1.0).
 * Some paths may differ between BAM versions (9.5, 9.6, 25.1).
 * If a call returns 404 or 400, check your BAM's Swagger UI
 * at https://<BAM_IP>/api/docs for your version's exact paths.
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

function escapeFilterValue(value: string): string {
  return value.replace(/'/g, "''");
}

export class BAMClient {
  private apiUrl: string;
  private token: string | null = null;
  private verifySsl: boolean;

  constructor(
    url: string,
    private username: string,
    private password: string,
    options: { verifySsl?: boolean } = {},
  ) {
    this.apiUrl = `${url.replace(/\/$/, "")}/api/v2`;
    this.verifySsl = options.verifySsl ?? false;
  }

  // --- Session ---

  async login() {
    const resp = await fetch(`${this.apiUrl}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: this.username, password: this.password }),
      tls: { rejectUnauthorized: this.verifySsl },
    } as RequestInit);
    if (!resp.ok) throw new Error(`Login failed: ${resp.status} ${await resp.text()}`);
    const data = await resp.json();
    this.token = data.apiToken;
    return data;
  }

  async logout() {
    if (!this.token) return;
    try {
      // v2 documented logout: PATCH /sessions/current with state change
      await this.apiFetch("/sessions/current", {
        method: "PATCH",
        body: JSON.stringify({ state: "LOGGED_OUT" }),
      });
    } catch {
      // Logout errors should not mask caller exceptions
    } finally {
      this.token = null;
    }
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
      tls: { rejectUnauthorized: this.verifySsl },
    } as RequestInit);
    if (!resp.ok) {
      const body = await resp.text();
      throw new Error(`BAM API ${resp.status}: ${body}`);
    }
    if (resp.status === 204 || resp.status === 205) return null;
    const text = await resp.text();
    return text ? JSON.parse(text) : null;
  }

  async get(path: string, params: Record<string, unknown> = {}): Promise<BAMCollection> {
    const entries = Object.entries(params).map(([k, v]) => [k, String(v)]);
    const qs = new URLSearchParams(entries).toString();
    const url = qs ? `${path}?${qs}` : path;
    const result = await this.apiFetch(url);
    if (!result) throw new Error(`Unexpected empty response for GET ${path}`);
    return result;
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

  async findConfiguration(name: string): Promise<BAMEntity> {
    const escaped = escapeFilterValue(name);
    const r = await this.get("/configurations", { filter: `name:eq('${escaped}')` });
    const item = r?.data?.[0];
    if (!item) throw new Error(`Configuration '${name}' not found`);
    return item;
  }

  // --- Views ---

  getViews(configId: number) {
    return this.get(`/configurations/${configId}/views`);
  }

  async findView(configId: number, name: string): Promise<BAMEntity> {
    const escaped = escapeFilterValue(name);
    const r = await this.get(`/configurations/${configId}/views`, {
      filter: `name:eq('${escaped}')`,
    });
    const item = r?.data?.[0];
    if (!item) throw new Error(`View '${name}' not found in configuration ${configId}`);
    return item;
  }

  // --- Zones ---

  getZones(viewId: number) {
    return this.get(`/views/${viewId}/zones`);
  }

  createZone(viewId: number, absoluteName: string) {
    return this.post(`/views/${viewId}/zones`, { type: "Zone", absoluteName });
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
    const data: Record<string, string> = { type: "IPv4Block", range: cidr };
    if (name) data.name = name;
    return this.post(`/configurations/${configId}/blocks`, data);
  }

  getNetworks(blockId: number) {
    return this.get(`/blocks/${blockId}/networks`);
  }

  createNetwork(blockId: number, cidr: string, name?: string) {
    const data: Record<string, string> = { type: "IPv4Network", range: cidr };
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

  /** NOTE: May be GET on some BAM versions. Check /api/docs. */
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

  /** NOTE: Some BAM versions use /ranges with different body format. Check /api/docs. */
  createDhcpRange(networkId: number, start: string, end: string) {
    return this.post(`/networks/${networkId}/ranges`, {
      type: "DHCP4Range",
      start,
      end,
    });
  }

  // --- Servers ---

  getServers(configId: number) {
    return this.get(`/configurations/${configId}/servers`);
  }

  /** NOTE: Some BAM versions use /deploy instead of /deployments. Check /api/docs. */
  deployServer(serverId: number, services: string[] = ["DNS", "DHCP"]) {
    return this.post(`/servers/${serverId}/deployments`, { services });
  }

  // --- Search ---

  /**
   * Search by filtering configurations. The v2 API has no /search endpoint;
   * use get() with filters on specific collections for targeted searches.
   */
  search(keyword: string, opts: { limit?: number } = {}) {
    const escaped = escapeFilterValue(keyword);
    const params: Record<string, unknown> = {
      filter: `name:contains('${escaped}')`,
      limit: opts.limit ?? 100,
    };
    return this.get("/configurations", params);
  }
}
