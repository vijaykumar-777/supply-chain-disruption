const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers ?? {});
  if (!(options?.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

// ─── Types ────────────────────────────────────────────────────────────────────

export interface APIEvent {
  id: string;
  title: string;
  category: string;
  severity: number;
  type: "critical" | "warning" | "info";
  timestamp: string;
  locations: string[];
  description: string;
}

export interface LiveDisasterAlert extends APIEvent {
  source: string;
  sources?: string[];
  duplicate_count?: number;
  evidence_urls?: string[];
  url?: string | null;
  confidence?: number;
}

export interface LiveDisastersResponse {
  alerts: LiveDisasterAlert[];
  count: number;
  raw_count?: number;
  duplicate_count?: number;
  source_status: Record<string, { enabled: boolean; live: boolean; error?: string | null; queries?: number; returned?: number }>;
  coverage: {
    places_tracked: number;
    places_sample: string[];
    disaster_terms: string[];
    news_lookback_days?: number;
    news_sources?: string[];
    deduplication_policy?: string;
    policy: string;
  };
}

export interface APINode {
  id: string;
  name: string;
  labels: string[];
  lat?: number;
  lon?: number;
  country?: string;
  resilience_score?: number;  // Fix #9: canonical 0..1 range
}

export interface APILink {
  source_id: string;
  target_id: string;
  rel_type: string;
}

// Fix #10: source metadata type
export type DataSource = "live" | "demo" | "unavailable";
export type AppMode = "live" | "demo";

export interface ModeResponse {
  mode: AppMode;
  source_policy: string;
}

export interface CompanyIntelSourceStatusItem {
  enabled: boolean;
  live: boolean;
  error?: string | null;
}

export interface CompanyIntelCompany {
  entity_id: string;
  name: string;
  legal_name?: string | null;
  lei?: string | null;
  cik?: string | null;
  ticker?: string | null;
  country?: string | null;
  jurisdiction?: string | null;
  entity_status?: string | null;
  legal_form?: string | null;
  registered_as?: string | null;
  legal_address?: string | null;
  headquarters_address?: string | null;
  source_labels: string[];
  description: string;
}

export interface CompanyIntelSearchResponse {
  companies: CompanyIntelCompany[];
  count: number;
  source_status: Record<string, CompanyIntelSourceStatusItem>;
}

export interface CompanyIntelImportResult {
  company_id: string;
  name: string;
  lei?: string | null;
  cik?: string | null;
  tickers: string[];
  country?: string | null;
  filings_imported: number;
  sources: string[];
}

export interface CompanyIntelImportResponse {
  imported: CompanyIntelImportResult[];
  count: number;
  source: DataSource;
}

export interface CompanyIntelBulkImportResponse extends CompanyIntelImportResponse {
  skipped: Array<{ name: string; reason: string }>;
  skipped_count: number;
}

export interface DashboardMetrics {
  total_active_events: number;
  high_risk_nodes: number;
  monitored_nodes: number;
  weather_alerts: number;
  source?: DataSource;  // Fix #10
}

export interface SimulationResult {
  optimal_route: string[];
  alternative_route: string[];
  simulation: {
    iterations: number;
    mean_days: number;
    p50_days: number;
    p95_days: number;
    max_risk_days: number;
    std_dev: number;
  };
  source?: DataSource;  // Fix #10
}

export interface SupplyChainSourceStatusItem {
  enabled: boolean;
  live: boolean;
  error?: string;
}

export interface SupplyChainAlert {
  id: string;
  title: string;
  description: string;
  category: string;
  severity: number;
  type: "critical" | "warning" | "info";
  locations: string[];
  companies: string[];
  timestamp: string;
  source: string;
  url?: string;
}

export interface SupplyChainMatchedAlert {
  alert_id: string;
  alert_title: string;
  alert_source: string;
  alert_type: "critical" | "warning" | "info";
  category: string;
  severity: number;
  reasons: string[];
  url?: string;
}

export interface SupplyChainAlternativeRoute {
  strategy: "supplier_substitution" | "network_reroute" | "supplier_network_reroute";
  summary: string;
  reason: string;
  estimated_risk_score: number;
  risk_reduction: number;
  route_ids: string[];
  route_names: string[];
  company_path: string[];
  location_path: string[];
}

export interface SupplyChainImpactLink {
  route_id: string;
  route_name: string;
  source_company: string;
  target_company: string;
  material: string;
  origin: string;
  destination: string;
  transport_mode: string;
  criticality: string;
  status: "blocked" | "at_risk";
  risk_score: number;
  matched_alerts: SupplyChainMatchedAlert[];
  downstream_companies: string[];
  alternative_route?: SupplyChainAlternativeRoute | null;
}

export interface SupplyChainImpactCompany {
  company: string;
  status: "blocked" | "at_risk" | "watch";
  risk_score: number;
  direct_impacts: number;
  downstream_exposure: string[];
}

export interface SupplyChainNetworkNode {
  id: string;
  label: string;
  type: "company" | "location";
  lat?: number | null;
  lon?: number | null;
}

export interface SupplyChainNetworkLink {
  id: string;
  source_company: string;
  target_company: string;
  relationship_type: string;
  material: string;
  origin: string;
  destination: string;
  transport_mode: string;
  criticality: string;
  route_name: string;
  origin_lat?: number | null;
  origin_lon?: number | null;
  destination_lat?: number | null;
  destination_lon?: number | null;
}

export interface SupplyChainTemplate {
  columns: string[];
  sample_rows: Record<string, string>[];
}

export interface SupplyChainSnapshotSummary {
  snapshot_id: string;
  file_name: string;
  uploaded_at: string;
  route_count: number;
  last_checked_at?: string;
}

export interface ReliefReferenceData {
  counts: Record<string, number>;
  files: Record<string, string>;
  datasets: Record<string, Array<Record<string, string>>>;
  provenance?: Record<string, string>;
  required_live_integrations?: Array<{
    name: string;
    env_vars: string[];
    purpose: string;
    required_for_mvp: boolean;
  }>;
  coverage_places?: string[];
}

export interface SupplyChainReport {
  snapshot_id: string;
  file_name: string;
  uploaded_at: string;
  last_checked_at: string;
  metrics: {
    total_routes: number;
    blocked_routes: number;
    at_risk_routes: number;
    healthy_routes: number;
    monitored_companies: number;
    watched_locations: number;
    active_alerts: number;
  };
  alerts: SupplyChainAlert[];
  impacted_links: SupplyChainImpactLink[];
  impacted_companies: SupplyChainImpactCompany[];
  network: {
    nodes: SupplyChainNetworkNode[];
    links: SupplyChainNetworkLink[];
  };
  source_status: Record<string, SupplyChainSourceStatusItem>;
  watch_terms: string[];
}

// ─── API Methods ──────────────────────────────────────────────────────────────

export const api = {
  health: () => request<{ status: string }>("/health"),

  getMode: () => request<ModeResponse>("/api/mode"),

  setMode: (mode: AppMode) =>
    request<ModeResponse>("/api/mode", {
      method: "POST",
      body: JSON.stringify({ mode }),
    }),

  // Fix #10: response now includes source field
  getEvents: () =>
    request<{ events: APIEvent[]; count: number; source?: DataSource }>("/api/events"),

  getLiveDisasters: () =>
    request<LiveDisastersResponse>("/api/disasters/live"),

  ingestEvents: () =>
    request<{ success: boolean; inserted_events: number; source_status: any }>("/api/ingest/events", {
      method: "POST",
    }),

  getGraphNodes: () =>
    request<{ nodes: APINode[]; links: APILink[]; count: number; source?: DataSource }>("/api/graph/nodes"),

  getMetrics: () => request<DashboardMetrics>("/api/metrics"),

  simulate: (
    source: string,
    target: string,
    disrupted_nodes: string[] = [],
    iterations = 5000
  ) =>
    request<SimulationResult>("/api/simulate", {
      method: "POST",
      body: JSON.stringify({ source, target, disrupted_nodes, iterations }),
    }),

  recommend: (
    event_title: string,
    event_category: string,
    locations: string[],
    simulation_results: object,
    alt_route: string[] = []
  ) =>
    request<{ recommendation_id: string; recommendation: string }>(
      "/api/recommend",
      {
        method: "POST",
        body: JSON.stringify({
          event_title,
          event_category,
          locations,
          simulation_results,
          alt_route,
        }),
      }
    ),

  // Fix #5: response type updated to include optional error field
  feedback: (recommendation_id: string, rating: number, comment = "") =>
    request<{ success: boolean; error?: string }>("/api/feedback", {
      method: "POST",
      body: JSON.stringify({ recommendation_id, rating, comment }),
    }),

  searchCompanyIntelligence: (query: string, limit = 8) =>
    request<CompanyIntelSearchResponse>(`/api/company-intel/search?q=${encodeURIComponent(query)}&limit=${limit}`),

  importCompanyIntelligence: (companies: Array<{ lei?: string; cik?: string; name?: string; ticker?: string }>) =>
    request<CompanyIntelImportResponse>("/api/company-intel/import", {
      method: "POST",
      body: JSON.stringify({ companies }),
    }),

  importCompanyIntelligenceBulk: (company_names: string[]) =>
    request<CompanyIntelBulkImportResponse>("/api/company-intel/import-bulk", {
      method: "POST",
      body: JSON.stringify({ company_names }),
    }),

  getSupplyChainTemplate: () =>
    request<SupplyChainTemplate>("/api/relief/template"),

  getReliefReferenceData: () =>
    request<ReliefReferenceData>("/api/relief/reference-data"),

  loadReliefReferenceNetwork: () =>
    request<SupplyChainReport>("/api/relief/load-reference", {
      method: "POST",
    }),

  listSupplyChainSnapshots: () =>
    request<{ snapshots: SupplyChainSnapshotSummary[] }>("/api/relief/snapshots"),

  uploadSupplyChainFile: (file: File) => {
    return request<SupplyChainReport>("/api/relief/upload", {
      method: "POST",
      body: file,
      headers: {
        "Content-Type": file.type || "application/octet-stream",
        "X-Filename": file.name,
      },
    });
  },

  getSupplyChainSnapshot: (snapshotId: string, refresh = true) =>
    request<SupplyChainReport>(`/api/relief/snapshots/${snapshotId}?refresh=${refresh ? "true" : "false"}`),
};
