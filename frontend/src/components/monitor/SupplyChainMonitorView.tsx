import React, { useDeferredValue, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  DatabaseZap,
  Download,
  FileUp,
  LoaderCircle,
  MapPinned,
  Mountain,
  RefreshCw,
  Route,
  Truck,
  Waves,
} from "lucide-react";
import { useSupplyChainMonitor } from "../../hooks/useAtlasData";
import { cn } from "../../lib/utils";
import { api } from "../../services/api";
import type { SupplyChainAlert, SupplyChainImpactLink, SupplyChainReport, SupplyChainSourceStatusItem } from "../../services/api";

const STATUS_CLASSES: Record<string, string> = {
  blocked: "bg-error/15 text-error border-error/25",
  at_risk: "bg-warning/15 text-warning border-warning/25",
  watch: "bg-primary/15 text-primary border-primary/25",
  healthy: "bg-success/15 text-success border-success/25",
};

const SOURCE_CLASSES: Record<string, string> = {
  live: "text-success border-success/20 bg-success/10",
  standby: "text-tertiary border-tertiary/20 bg-tertiary/10",
  disabled: "text-on-surface-variant border-white/10 bg-white/5",
};

function sourceEntries(report: SupplyChainReport): Array<[string, SupplyChainSourceStatusItem]> {
  return Object.entries(report.source_status) as Array<[string, SupplyChainSourceStatusItem]>;
}

const MetricTile = ({
  label,
  value,
  icon: Icon,
  tone,
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  tone: string;
}) => (
  <div className="glass rounded-xl p-5">
    <div className="flex items-start justify-between gap-4">
      <div>
        <p className="text-[11px] uppercase tracking-[0.2em] text-on-surface-variant">{label}</p>
        <p className="mt-3 text-3xl font-black tracking-tight">{value}</p>
      </div>
      <div className={cn("rounded-xl border p-3", tone)}>
        <Icon className="h-5 w-5" />
      </div>
    </div>
  </div>
);

const AlertCard = ({ alert }: { alert: SupplyChainAlert }) => {
  const cls = alert.type === "critical" ? STATUS_CLASSES.blocked : alert.type === "warning" ? STATUS_CLASSES.at_risk : STATUS_CLASSES.watch;

  return (
    <div className="rounded-xl border border-white/10 bg-black/10 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-bold">{alert.title}</p>
          <p className="mt-1 text-sm text-on-surface-variant">{alert.description}</p>
        </div>
        <span className={cn("shrink-0 rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em]", cls)}>
          {alert.type}
        </span>
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs text-on-surface-variant">
        {alert.locations.map((location) => (
          <span key={location} className="rounded-full border border-white/10 bg-white/5 px-2 py-1">
            {location}
          </span>
        ))}
      </div>
    </div>
  );
};

const ImpactCard = ({ link }: { link: SupplyChainImpactLink }) => {
  const tone = STATUS_CLASSES[link.status] ?? STATUS_CLASSES.watch;

  return (
    <div className="rounded-xl border border-white/10 bg-surface/60 p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className={cn("rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em]", tone)}>
              {link.status.replace("_", " ")}
            </span>
            <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-on-surface-variant">
              risk {(link.risk_score * 100).toFixed(0)}%
            </span>
          </div>
          <h3 className="mt-3 text-lg font-bold">{link.route_name}</h3>
          <p className="mt-1 text-sm text-on-surface-variant">
            {link.source_company} to {link.target_company} via {link.origin} &rarr; {link.destination}
          </p>
          <p className="mt-2 text-sm text-on-surface-variant">
            Payload: {link.material || "Relief supplies"} | Mode: {link.transport_mode || "truck"} | Priority: {link.criticality}
          </p>
        </div>

        {link.alternative_route ? (
          <div className="min-w-[260px] rounded-xl border border-success/20 bg-success/10 p-4 text-sm text-success">
            <p className="font-bold">Alternate route available</p>
            <p className="mt-1 opacity-85">{link.alternative_route.summary}</p>
            <p className="mt-2 text-xs uppercase tracking-[0.16em]">Risk reduction {(link.alternative_route.risk_reduction * 100).toFixed(0)}%</p>
          </div>
        ) : (
          <div className="min-w-[260px] rounded-xl border border-error/20 bg-error/10 p-4 text-sm text-error">
            <p className="font-bold">No alternate in uploaded network</p>
            <p className="mt-1 opacity-85">Add backup road corridors or a secondary relief hub for this settlement.</p>
          </div>
        )}
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div className="rounded-xl border border-white/5 bg-black/10 p-3">
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-on-surface-variant">Evidence</p>
          <div className="mt-2 space-y-2 text-xs text-on-surface-variant">
            {link.matched_alerts.map((alert) => (
              <p key={alert.alert_id}>{alert.alert_title}</p>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-white/5 bg-black/10 p-3">
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-on-surface-variant">Cascading Impact</p>
          <p className="mt-2 text-xs text-on-surface-variant">
            {link.downstream_companies.length > 0
              ? `${link.downstream_companies.join(", ")} may lose access if this road remains blocked.`
              : "No downstream settlements are modeled beyond this road segment."}
          </p>
        </div>
      </div>
    </div>
  );
};

export const SupplyChainMonitorView = () => {
  const { report, template, snapshots, referenceData, loading, bootLoading, error, uploadFile, refresh, loadSnapshot, loadReferenceNetwork, seedReferenceGraph } = useSupplyChainMonitor();
  const deferredReport = useDeferredValue(report);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [seedMessage, setSeedMessage] = useState<string | null>(null);

  const latestReport = deferredReport ?? report;
  const provenanceValues: string[] = referenceData?.provenance ? Object.values(referenceData.provenance) : [];
  const provenanceSummary = provenanceValues.reduce<Record<string, number>>((acc, value) => {
    acc[value] = (acc[value] ?? 0) + 1;
    return acc;
  }, {});
  const requiredFeeds = referenceData?.required_live_integrations ?? [];

  const onUpload = async () => {
    if (!selectedFile) return;
    await uploadFile(selectedFile);
  };

  const onSeedGraph = async () => {
    setSeedMessage(null);
    const result = await seedReferenceGraph(false);
    if (result) {
      setSeedMessage(`${result.neo4j_nodes} nodes and ${result.neo4j_routes} routes available in Neo4j`);
    }
  };

  const onExport = (format: "csv" | "json") => {
    if (!latestReport?.snapshot_id) return;
    window.open(api.exportSupplyChainReportUrl(latestReport.snapshot_id, format), "_blank", "noreferrer");
  };

  return (
    <div className="space-y-6">
      <section className="glass rounded-xl overflow-hidden">
        <div className="border-b border-white/5 bg-[linear-gradient(135deg,rgba(8,31,44,0.95),rgba(13,24,38,0.95))] p-6">
          <div className="max-w-3xl space-y-3">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.22em] text-primary">
              <Truck className="h-3.5 w-3.5" />
              Relief Operations
            </span>
            <h2 className="text-3xl font-black tracking-tight">Upload Karnataka relief roads and find villages that get cut off.</h2>
            <p className="max-w-2xl text-sm leading-6 text-on-surface-variant">
              Model hubs, ghat roads, coastal access roads, and villages as a graph. Weather and disruption alerts are matched to road segments so the system can show blocked corridors, cascading isolation, and alternate truck routes.
            </p>
          </div>
        </div>

        <div className="grid gap-6 p-6 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="space-y-4">
            <div className="rounded-xl border border-dashed border-primary/25 bg-primary/5 p-5">
              <div className="flex items-start gap-3">
                <div className="rounded-xl border border-primary/20 bg-primary/10 p-3 text-primary">
                  <FileUp className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold">Upload a CSV or JSON road network</h3>
                  <p className="mt-1 text-sm text-on-surface-variant">
                    Include relief hubs, settlements, road endpoints, vehicle mode, and priority. The backend accepts common aliases like village, road_segment, corridor, relief_hub, and medical_priority.
                  </p>
                </div>
              </div>

              <div className="mt-5 flex flex-col gap-3 md:flex-row">
                <label className="flex-1 cursor-pointer rounded-xl border border-white/10 bg-surface/60 px-4 py-3 text-sm text-on-surface-variant transition-colors hover:border-primary/25 hover:text-on-surface">
                  <input
                    type="file"
                    accept=".csv,.json"
                    className="hidden"
                    onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                  />
                  {selectedFile ? selectedFile.name : "Choose road network file"}
                </label>
                <button
                  type="button"
                  onClick={onUpload}
                  disabled={!selectedFile || loading}
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-bold text-background transition-all disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />}
                  Analyze Network
                </button>
              </div>

              {error && (
                <div className="mt-4 rounded-xl border border-error/25 bg-error/10 px-4 py-3 text-sm text-error">
                  {error}
                </div>
              )}
            </div>

            {referenceData && (
              <div className="rounded-xl border border-success/20 bg-success/10 p-5">
                <div className="flex items-start gap-3">
                  <div className="rounded-xl border border-success/20 bg-success/10 p-3 text-success">
                    <DatabaseZap className="h-5 w-5" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-success">Karnataka reference data found</h3>
                    <p className="mt-1 text-sm text-on-surface-variant">
                      Loaded CSVs include roads, hubs, at-risk villages, historical disasters, rainfall thresholds, vehicle rules, simulated inventory, truck fleet, blocked roads, field reports, rescue teams, and API placeholders.
                    </p>
                    <div className="mt-4 grid grid-cols-2 gap-2 text-xs sm:grid-cols-3">
                      {Object.entries(referenceData.counts).map(([name, count]) => (
                        <div key={name} className="rounded-lg border border-success/15 bg-black/10 px-3 py-2">
                          <p className="font-bold text-success">{count}</p>
                          <p className="mt-1 capitalize text-on-surface-variant">{name.replaceAll("_", " ")}</p>
                        </div>
                      ))}
                    </div>
                    <div className="mt-4 grid gap-2 text-xs sm:grid-cols-3">
                      {Object.entries(provenanceSummary).map(([label, count]) => (
                        <div key={label} className="rounded-lg border border-white/10 bg-black/10 px-3 py-2">
                          <p className="font-bold text-on-surface">{count}</p>
                          <p className="mt-1 capitalize text-on-surface-variant">{label.replaceAll("_", " ")}</p>
                        </div>
                      ))}
                    </div>
                    {requiredFeeds.length > 0 && (
                      <div className="mt-4 rounded-xl border border-white/10 bg-black/10 p-3">
                        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-on-surface-variant">Live feeds to configure later</p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {requiredFeeds.map((feed) => (
                            <span key={feed.name} className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-on-surface-variant">
                              {feed.name}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    <button
                      type="button"
                      onClick={loadReferenceNetwork}
                      disabled={loading || (referenceData.counts.road_network ?? 0) === 0}
                      className="mt-4 inline-flex items-center justify-center gap-2 rounded-xl bg-success px-4 py-2 text-sm font-bold text-background transition-all disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <DatabaseZap className="h-4 w-4" />}
                      Load Reference Road Network
                    </button>
                    <button
                      type="button"
                      onClick={onSeedGraph}
                      disabled={loading}
                      className="ml-2 mt-4 inline-flex items-center justify-center gap-2 rounded-xl border border-success/25 bg-success/10 px-4 py-2 text-sm font-bold text-success transition-all disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <DatabaseZap className="h-4 w-4" />}
                      Seed Neo4j Graph
                    </button>
                    {seedMessage && <p className="mt-2 text-xs text-success">{seedMessage}</p>}
                  </div>
                </div>
              </div>
            )}

            {template && (
              <div className="rounded-xl border border-white/5 bg-white/3 p-5">
                <h3 className="text-sm font-bold uppercase tracking-[0.22em] text-on-surface-variant">Accepted Columns</h3>
                <div className="mt-3 flex flex-wrap gap-2">
                  {template.columns.map((column) => (
                    <span key={column} className="rounded-full border border-white/10 bg-black/10 px-2.5 py-1 text-xs text-on-surface-variant">
                      {column}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {snapshots.length > 0 && (
              <div className="rounded-xl border border-white/5 bg-white/3 p-5">
                <h3 className="text-sm font-bold uppercase tracking-[0.22em] text-on-surface-variant">Recent Networks</h3>
                <div className="mt-3 space-y-2">
                  {snapshots.map((snapshot) => (
                    <button
                      type="button"
                      key={snapshot.snapshot_id}
                      onClick={() => loadSnapshot(snapshot.snapshot_id)}
                      className="flex w-full items-center justify-between gap-3 rounded-xl border border-white/5 bg-black/10 px-3 py-2 text-left text-sm transition-colors hover:border-primary/25"
                    >
                      <span>{snapshot.file_name}</span>
                      <span className="text-xs text-on-surface-variant">{snapshot.route_count} roads</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-4">
            {bootLoading && !latestReport && (
              <div className="glass rounded-xl p-8 text-center text-on-surface-variant">
                <LoaderCircle className="mx-auto mb-3 h-6 w-6 animate-spin" />
                Loading latest relief network...
              </div>
            )}

            {!latestReport && !bootLoading && (
              <div className="rounded-xl border border-dashed border-white/10 bg-white/3 p-8 text-center">
                <MapPinned className="mx-auto h-10 w-10 text-primary" />
                <h3 className="mt-4 text-lg font-bold">No relief road network loaded</h3>
                <p className="mx-auto mt-2 max-w-md text-sm text-on-surface-variant">
                  Upload a road graph to identify blocked corridors and villages isolated by floods or landslides.
                </p>
              </div>
            )}

            {latestReport && (
              <>
                <div className="grid gap-3 md:grid-cols-4">
                  <MetricTile label="Road Segments" value={latestReport.metrics.total_routes} icon={Route} tone="text-primary border-primary/20 bg-primary/10" />
                  <MetricTile label="Blocked" value={latestReport.metrics.blocked_routes} icon={AlertTriangle} tone="text-error border-error/20 bg-error/10" />
                  <MetricTile label="At Risk" value={latestReport.metrics.at_risk_routes} icon={Waves} tone="text-warning border-warning/20 bg-warning/10" />
                  <MetricTile label="Watched Points" value={latestReport.metrics.watched_locations} icon={Mountain} tone="text-success border-success/20 bg-success/10" />
                </div>

                <div className="rounded-xl border border-white/5 bg-white/3 p-5">
                  <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div>
                      <h3 className="text-lg font-bold">{latestReport.file_name}</h3>
                      <p className="text-sm text-on-surface-variant">
                        Last checked {new Date(latestReport.last_checked_at).toLocaleString()} against {latestReport.alerts.length} active alert(s).
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={refresh}
                      disabled={loading}
                      className="inline-flex items-center justify-center gap-2 rounded-xl border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-bold text-primary transition-colors hover:border-primary/30 disabled:opacity-50"
                    >
                      <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
                      Refresh Alerts
                    </button>
                    <button
                      type="button"
                      onClick={() => onExport("csv")}
                      className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-bold text-on-surface-variant transition-colors hover:border-primary/25 hover:text-primary"
                    >
                      <Download className="h-4 w-4" />
                      Export CSV
                    </button>
                    <button
                      type="button"
                      onClick={() => onExport("json")}
                      className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-bold text-on-surface-variant transition-colors hover:border-primary/25 hover:text-primary"
                    >
                      <Download className="h-4 w-4" />
                      Export JSON
                    </button>
                  </div>

                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    {sourceEntries(latestReport).map(([source, status]) => {
                      const tone = status.live ? SOURCE_CLASSES.live : status.enabled ? SOURCE_CLASSES.standby : SOURCE_CLASSES.disabled;
                      return (
                        <div key={source} className={cn("rounded-xl border p-4", tone)}>
                          <p className="text-[11px] font-bold uppercase tracking-[0.2em]">{source}</p>
                          <p className="mt-2 text-sm font-semibold">{status.live ? "Live" : "Unavailable"}</p>
                          <p className="mt-1 text-xs opacity-80">{status.error ?? "Source responded successfully."}</p>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {latestReport.impacted_links.length > 0 ? (
                  <div className="space-y-3">
                    <h3 className="text-sm font-bold uppercase tracking-[0.22em] text-on-surface-variant">Blocked Roads And Cascading Impact</h3>
                    {latestReport.impacted_links.map((link) => (
                      <div key={link.route_id}>
                        <ImpactCard link={link} />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-xl border border-success/20 bg-success/10 p-5 text-success">
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="h-5 w-5" />
                      <div>
                        <p className="font-bold">No blocked or high-risk corridors detected</p>
                        <p className="mt-1 text-sm opacity-85">Keep refreshing alerts as rainfall conditions change.</p>
                      </div>
                    </div>
                  </div>
                )}

                {latestReport.alerts.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-bold uppercase tracking-[0.22em] text-on-surface-variant">Current Evidence</h3>
                    {latestReport.alerts.slice(0, 4).map((alert) => (
                      <div key={alert.id}>
                        <AlertCard alert={alert} />
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};
