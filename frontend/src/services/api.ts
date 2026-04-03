const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
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

export interface APINode {
  id: string;
  name: string;
  labels: string[];
  lat?: number;
  lon?: number;
  country?: string;
  resilience_score?: number;  // Fix #9: canonical 0..1 range
}

// Fix #10: source metadata type
export type DataSource = "live" | "fallback";

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

// ─── API Methods ──────────────────────────────────────────────────────────────

export const api = {
  health: () => request<{ status: string }>("/health"),

  // Fix #10: response now includes source field
  getEvents: () =>
    request<{ events: APIEvent[]; count: number; source?: DataSource }>("/api/events"),

  getGraphNodes: () =>
    request<{ nodes: APINode[]; count: number; source?: DataSource }>("/api/graph/nodes"),

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
};
