import React, { useMemo, useState } from "react";
import { AlertTriangle, ExternalLink, RefreshCw, Search, ShieldAlert, Waves } from "lucide-react";
import { useLiveDisasters } from "../../hooks/useAtlasData";
import { cn } from "../../lib/utils";
import type { LiveDisastersResponse } from "../../services/api";

const SEVERITY_CLASSES: Record<string, string> = {
  critical: "border-error/25 bg-error/10 text-error",
  warning: "border-warning/25 bg-warning/10 text-warning",
  info: "border-primary/25 bg-primary/10 text-primary",
};

type DisasterSourceStatus = LiveDisastersResponse["source_status"][string];

function sourceStatusEntries(status: LiveDisastersResponse["source_status"]): Array<[string, DisasterSourceStatus]> {
  return Object.entries(status) as Array<[string, DisasterSourceStatus]>;
}

export const LiveDisastersView = () => {
  const { data, loading, error, refresh } = useLiveDisasters();
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("all");

  const alerts = data?.alerts ?? [];
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return alerts.filter((alert) => {
      if (severity !== "all" && alert.type !== severity) return false;
      if (!q) return true;
      return [
        alert.title,
        alert.description,
        alert.category,
        alert.source,
        ...alert.locations,
      ].some((value) => value.toLowerCase().includes(q));
    });
  }, [alerts, query, severity]);

  const criticalCount = alerts.filter((alert) => alert.type === "critical").length;
  const warningCount = alerts.filter((alert) => alert.type === "warning").length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-on-surface">Live Disaster Alerts</h2>
          <p className="mt-1 max-w-3xl text-sm text-on-surface-variant">
            Broad scan across Karnataka disaster terms, Western Ghats/coastal districts, road names, and at-risk villages. This is designed for early warning coverage, not certified incident confirmation.
          </p>
        </div>
        <button
          type="button"
          onClick={refresh}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-bold text-primary transition-colors hover:border-primary/30 disabled:opacity-50"
        >
          <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          Refresh
        </button>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <div className="glass rounded-xl p-5">
          <p className="text-[11px] uppercase tracking-[0.2em] text-on-surface-variant">Total Alerts</p>
          <p className="mt-3 text-3xl font-black">{alerts.length}</p>
        </div>
        <div className="glass rounded-xl p-5">
          <p className="text-[11px] uppercase tracking-[0.2em] text-on-surface-variant">Critical</p>
          <p className="mt-3 text-3xl font-black text-error">{criticalCount}</p>
        </div>
        <div className="glass rounded-xl p-5">
          <p className="text-[11px] uppercase tracking-[0.2em] text-on-surface-variant">Warning</p>
          <p className="mt-3 text-3xl font-black text-warning">{warningCount}</p>
        </div>
        <div className="glass rounded-xl p-5">
          <p className="text-[11px] uppercase tracking-[0.2em] text-on-surface-variant">Places Tracked</p>
          <p className="mt-3 text-3xl font-black text-primary">{data?.coverage.places_tracked ?? 0}</p>
        </div>
      </div>

      <div className="glass-elevated rounded-xl p-4">
        <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
          <div className="flex rounded-xl border border-white/10 bg-surface/60 px-3 py-2">
            <Search className="mr-2 h-4 w-4 text-on-surface-variant" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search village, district, road, source..."
              className="w-full bg-transparent text-sm text-on-surface outline-none placeholder:text-on-surface-variant"
            />
          </div>
          <select
            value={severity}
            onChange={(event) => setSeverity(event.target.value)}
            className="rounded-xl border border-white/10 bg-surface/60 px-3 py-2 text-sm text-on-surface outline-none"
          >
            <option value="all">All severities</option>
            <option value="critical">Critical only</option>
            <option value="warning">Warning only</option>
            <option value="info">Info only</option>
          </select>
        </div>

        {data && (
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {sourceStatusEntries(data.source_status).map(([source, status]) => (
              <div key={source} className={cn("rounded-xl border p-4", status.live ? "border-success/20 bg-success/10 text-success" : "border-warning/20 bg-warning/10 text-warning")}>
                <p className="text-[11px] font-bold uppercase tracking-[0.2em]">{source}</p>
                <p className="mt-2 text-sm font-semibold">{status.live ? "Live" : "Unavailable or partial"}</p>
                <p className="mt-1 text-xs opacity-80">{status.error ?? `${status.queries ?? 0} query batch(es) checked.`}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {error && <div className="rounded-xl border border-error/25 bg-error/10 px-4 py-3 text-sm text-error">{error}</div>}
      {loading && !data && <div className="rounded-xl border border-white/10 bg-white/5 p-8 text-center text-on-surface-variant">Scanning live disaster sources...</div>}

      <div className="space-y-3">
        {!loading && filtered.length === 0 && (
          <div className="rounded-xl border border-white/10 bg-white/5 p-8 text-center text-on-surface-variant">
            No live disaster alerts matched the current filters.
          </div>
        )}
        {filtered.map((alert) => {
          const tone = SEVERITY_CLASSES[alert.type] ?? SEVERITY_CLASSES.info;
          return (
            <div key={alert.id} className="rounded-xl border border-white/10 bg-surface/70 p-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="flex gap-3">
                  <div className={cn("mt-1 rounded-xl border p-3", tone)}>
                    {alert.type === "critical" ? <ShieldAlert className="h-5 w-5" /> : alert.category === "flood" ? <Waves className="h-5 w-5" /> : <AlertTriangle className="h-5 w-5" />}
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={cn("rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em]", tone)}>{alert.type}</span>
                      <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-on-surface-variant">{alert.category}</span>
                      <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-on-surface-variant">{alert.source}</span>
                    </div>
                    <h3 className="mt-3 text-lg font-bold">{alert.title}</h3>
                    <p className="mt-1 text-sm text-on-surface-variant">{alert.description}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {alert.locations.map((location) => (
                        <span key={location} className="rounded-full border border-white/10 bg-black/10 px-2 py-1 text-xs text-on-surface-variant">{location}</span>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="min-w-[170px] text-sm text-on-surface-variant lg:text-right">
                  <p>{new Date(alert.timestamp).toLocaleString()}</p>
                  <p className="mt-1">Severity {(alert.severity * 100).toFixed(0)}%</p>
                  {alert.url && (
                    <a href={alert.url} target="_blank" rel="noreferrer" className="mt-3 inline-flex items-center gap-1 text-primary hover:underline">
                      Source <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {data && (
        <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-xs leading-5 text-on-surface-variant">
          {data.coverage.policy}
        </div>
      )}
    </div>
  );
};
