import React, { useDeferredValue, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  Building2,
  DatabaseZap,
  FileUp,
  Link2,
  LoaderCircle,
  Radar,
  RefreshCw,
  Route,
  Search,
  ShieldAlert,
  Waves,
} from "lucide-react";
import { useCompanyIntelligence, useSupplyChainMonitor } from "../../hooks/useAtlasData";
import { cn } from "../../lib/utils";
import type { CompanyIntelCompany, SupplyChainReport, SupplyChainSourceStatusItem } from "../../services/api";

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

function getSourceEntries(report: SupplyChainReport): Array<[string, SupplyChainSourceStatusItem]> {
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
  <div className="glass rounded-2xl p-5">
    <div className="flex items-start justify-between gap-4">
      <div>
        <p className="text-[11px] uppercase tracking-[0.24em] text-on-surface-variant">{label}</p>
        <p className="mt-3 text-3xl font-black tracking-tight">{value}</p>
      </div>
      <div className={cn("rounded-2xl border p-3", tone)}>
        <Icon className="h-5 w-5" />
      </div>
    </div>
  </div>
);

const CompanySearchCard = ({
  company,
  importing,
  onImport,
}: {
  company: CompanyIntelCompany;
  importing: boolean;
  onImport: () => void;
}) => (
  <div className="rounded-2xl border border-white/5 bg-black/10 p-4">
    <div className="flex items-start justify-between gap-3">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-on-surface-variant">
            {company.source_labels.join(" + ")}
          </span>
          {company.ticker && (
            <span className="rounded-full border border-success/15 bg-success/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-success">
              {company.ticker}
            </span>
          )}
        </div>
        <div className="mt-3 flex items-center gap-2">
          <div className="rounded-xl border border-white/10 bg-white/5 p-2 text-on-surface-variant">
            <Building2 className="h-4 w-4" />
          </div>
          <div>
            <p className="font-semibold">{company.name}</p>
            <p className="text-xs text-on-surface-variant">{company.description}</p>
          </div>
        </div>
      </div>
      <button
        type="button"
        onClick={onImport}
        disabled={importing}
        className="inline-flex items-center gap-2 rounded-full border border-success/20 bg-success/10 px-3 py-1.5 text-xs font-bold uppercase tracking-[0.2em] text-success transition-colors hover:border-success/30 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {importing ? <LoaderCircle className="h-3.5 w-3.5 animate-spin" /> : <DatabaseZap className="h-3.5 w-3.5" />}
        Import
      </button>
    </div>

    <div className="mt-4 grid gap-3 text-xs text-on-surface-variant sm:grid-cols-2">
      <div className="rounded-2xl border border-white/5 bg-white/3 p-3">
        <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-on-surface-variant">Identifiers</p>
        <p className="mt-2">LEI: {company.lei ?? "Not available"}</p>
        <p className="mt-1">CIK: {company.cik ?? "Not available"}</p>
        <p className="mt-1">Jurisdiction: {company.jurisdiction ?? "Not available"}</p>
      </div>
      <div className="rounded-2xl border border-white/5 bg-white/3 p-3">
        <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-on-surface-variant">Address Coverage</p>
        <p className="mt-2">{company.country ?? "Country not available"}</p>
        <p className="mt-1">{company.legal_address ?? company.headquarters_address ?? "Address not available"}</p>
      </div>
    </div>
  </div>
);

export const SupplyChainMonitorView = () => {
  const { report, template, snapshots, loading, bootLoading, error, uploadFile, refresh, loadSnapshot } = useSupplyChainMonitor();
  const {
    results: companyResults,
    sourceStatus: companySourceStatus,
    loading: companyLoading,
    importingId,
    bulkImportLoading,
    lastImport,
    lastBulkImport,
    error: companyError,
    search: searchCompanies,
    importCompany,
    bulkImportCompanies,
  } = useCompanyIntelligence();
  const deferredReport = useDeferredValue(report);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [companyQuery, setCompanyQuery] = useState("");
  const [bulkCompanyNames, setBulkCompanyNames] = useState("");

  const onUpload = async () => {
    if (!selectedFile) {
      return;
    }
    await uploadFile(selectedFile);
  };

  const onCompanySearch = async () => {
    if (!companyQuery.trim()) {
      return;
    }
    await searchCompanies(companyQuery.trim());
  };

  const onBulkImport = async () => {
    const companyNames = bulkCompanyNames
      .split(/[\n,]+/)
      .map((value) => value.trim())
      .filter(Boolean);

    if (companyNames.length === 0) {
      return;
    }

    await bulkImportCompanies(companyNames);
  };

  const latestReport = deferredReport ?? report;

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="glass rounded-[28px] overflow-hidden">
          <div className="relative overflow-hidden border-b border-white/5 bg-[radial-gradient(circle_at_top_left,_rgba(125,211,252,0.16),_transparent_38%),linear-gradient(135deg,rgba(15,21,36,0.95),rgba(10,14,26,0.95))] p-6">
            <div className="max-w-2xl space-y-3">
              <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.24em] text-primary">
                <Radar className="h-3.5 w-3.5" />
                Dependency Monitoring
              </span>
              <h2 className="text-3xl font-black tracking-tight">Upload only your company network, then watch the weak links in real time.</h2>
              <p className="max-w-xl text-sm leading-6 text-on-surface-variant">
                This view turns your supplier-to-supplier routes into a monitored graph, checks live disruption signals from GDELT and OpenWeatherMap, and recommends safer alternate lanes whenever your uploaded network has one.
              </p>
            </div>
          </div>

          <div className="grid gap-6 p-6 lg:grid-cols-[1fr_0.9fr]">
            <div className="space-y-4">
              <div className="rounded-2xl border border-white/5 bg-white/3 p-5">
                <div className="flex items-start gap-3">
                  <div className="rounded-2xl border border-success/20 bg-success/10 p-3 text-success">
                    <DatabaseZap className="h-5 w-5" />
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-lg font-bold">Search real companies from free public sources</h3>
                    <p className="text-sm text-on-surface-variant">
                      GLEIF gives us broad global legal-entity coverage, and SEC EDGAR enriches public-company tickers and recent filings. Importing a match writes only live source data into Neo4j.
                    </p>
                  </div>
                </div>

                <div className="mt-5 flex flex-col gap-3 md:flex-row">
                  <input
                    type="text"
                    value={companyQuery}
                    onChange={(event) => setCompanyQuery(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        void onCompanySearch();
                      }
                    }}
                    placeholder="Search Apple, Siemens, TSMC, Reliance..."
                    className="flex-1 rounded-2xl border border-white/10 bg-surface/60 px-4 py-3 text-sm text-on-surface outline-none transition-colors placeholder:text-on-surface-variant focus:border-primary/25"
                  />
                  <button
                    type="button"
                    onClick={onCompanySearch}
                    disabled={!companyQuery.trim() || companyLoading}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl bg-success px-5 py-3 text-sm font-bold text-background transition-all disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {companyLoading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                    Search Live Sources
                  </button>
                </div>

                <div className="mt-4 rounded-2xl border border-white/5 bg-black/10 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h4 className="text-sm font-bold uppercase tracking-[0.22em] text-on-surface-variant">Bulk Import</h4>
                      <p className="mt-1 text-sm text-on-surface-variant">
                        Paste one company per line, or separate names with commas. We will resolve the best live match for each one and import everything in one run.
                      </p>
                    </div>
                  </div>

                  <textarea
                    value={bulkCompanyNames}
                    onChange={(event) => setBulkCompanyNames(event.target.value)}
                    placeholder={"Apple Inc.\nTSMC\nSiemens AG\nReliance Industries"}
                    className="mt-4 min-h-[132px] w-full rounded-2xl border border-white/10 bg-surface/60 px-4 py-3 text-sm text-on-surface outline-none transition-colors placeholder:text-on-surface-variant focus:border-primary/25"
                  />

                  <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                    <p className="text-xs text-on-surface-variant">
                      Best for loading your top suppliers, manufacturers, and customers into Neo4j before uploading route lanes.
                    </p>
                    <button
                      type="button"
                      onClick={onBulkImport}
                      disabled={!bulkCompanyNames.trim() || bulkImportLoading}
                      className="inline-flex items-center justify-center gap-2 rounded-2xl bg-tertiary px-5 py-3 text-sm font-bold text-background transition-all disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      {bulkImportLoading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <DatabaseZap className="h-4 w-4" />}
                      Bulk Import To Neo4j
                    </button>
                  </div>

                  {lastBulkImport && (
                    <div className="mt-4 space-y-3">
                      <div className="rounded-2xl border border-success/20 bg-success/10 px-4 py-3 text-sm text-success">
                        Imported {lastBulkImport.count} compan{lastBulkImport.count === 1 ? "y" : "ies"} from the pasted list.
                        {lastBulkImport.skipped_count > 0 ? ` ${lastBulkImport.skipped_count} could not be matched.` : ""}
                      </div>

                      {lastBulkImport.imported.length > 0 && (
                        <div className="rounded-2xl border border-white/5 bg-white/3 p-4">
                          <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-on-surface-variant">Imported</p>
                          <div className="mt-3 flex flex-wrap gap-2">
                            {lastBulkImport.imported.map((item) => (
                              <span key={item.company_id} className="rounded-full border border-success/15 bg-success/10 px-3 py-1 text-xs text-success">
                                {item.name}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {lastBulkImport.skipped.length > 0 && (
                        <div className="rounded-2xl border border-warning/20 bg-warning/10 p-4">
                          <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-warning">Needs Review</p>
                          <div className="mt-3 space-y-2">
                            {lastBulkImport.skipped.map((item) => (
                              <div key={`${item.name}-${item.reason}`} className="rounded-2xl border border-warning/15 bg-black/10 px-3 py-2 text-xs text-on-surface-variant">
                                <span className="font-semibold text-on-surface">{item.name}</span>
                                {` • ${item.reason}`}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {Object.entries(companySourceStatus).map(([source, status]) => {
                    const tone = status.live ? SOURCE_CLASSES.live : status.enabled ? SOURCE_CLASSES.standby : SOURCE_CLASSES.disabled;
                    return (
                      <div key={source} className={cn("rounded-2xl border p-4", tone)}>
                        <p className="text-[11px] font-bold uppercase tracking-[0.22em]">{source}</p>
                        <p className="mt-2 text-sm font-semibold">{status.live ? "Live" : "Unavailable"}</p>
                        <p className="mt-1 text-xs opacity-80">{status.error ?? "Source responded successfully."}</p>
                      </div>
                    );
                  })}
                </div>

                {companyError && (
                  <div className="mt-4 rounded-2xl border border-error/25 bg-error/10 px-4 py-3 text-sm text-error">
                    {companyError}
                  </div>
                )}

                {lastImport && (
                  <div className="mt-4 rounded-2xl border border-success/20 bg-success/10 px-4 py-3 text-sm text-success">
                    Imported {lastImport.count} live compan{lastImport.count === 1 ? "y" : "ies"} into Neo4j.
                  </div>
                )}

                <div className="mt-4 space-y-3">
                  {companyResults.length === 0 && !companyLoading && (
                    <div className="rounded-2xl border border-dashed border-white/10 p-5 text-sm text-on-surface-variant">
                      Search for a company to pull live registry and filing metadata into the graph.
                    </div>
                  )}

                  {companyResults.map((company) => (
                    <CompanySearchCard
                      key={company.entity_id}
                      company={company}
                      importing={importingId === company.entity_id}
                      onImport={() => importCompany(company)}
                    />
                  ))}
                </div>
              </div>

              <div className="rounded-2xl border border-dashed border-primary/25 bg-primary/5 p-5">
                <div className="flex items-start gap-3">
                  <div className="rounded-2xl border border-primary/20 bg-primary/10 p-3 text-primary">
                    <FileUp className="h-5 w-5" />
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-lg font-bold">Upload a CSV or JSON dependency file</h3>
                    <p className="text-sm text-on-surface-variant">
                      Include suppliers, buyers, route endpoints, transport mode, and criticality. The backend keeps the latest snapshot, refreshes live disruption checks, and suggests alternate routes when a lane becomes risky.
                    </p>
                  </div>
                </div>

                <div className="mt-5 flex flex-col gap-3 md:flex-row">
                  <label className="flex-1 cursor-pointer rounded-2xl border border-white/10 bg-surface/60 px-4 py-3 text-sm text-on-surface-variant transition-colors hover:border-primary/25 hover:text-on-surface">
                    <input
                      type="file"
                      accept=".csv,.json"
                      className="hidden"
                      onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                    />
                    {selectedFile ? selectedFile.name : "Choose file"}
                  </label>
                  <button
                    type="button"
                    onClick={onUpload}
                    disabled={!selectedFile || loading}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl bg-primary px-5 py-3 text-sm font-bold text-background transition-all disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />}
                    Upload And Monitor
                  </button>
                </div>
              </div>

              <div className="rounded-2xl border border-white/5 bg-white/3 p-5">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-bold uppercase tracking-[0.24em] text-on-surface-variant">Accepted Columns</h3>
                    <p className="mt-1 text-xs text-on-surface-variant">Flexible aliases are supported, but these are the canonical fields.</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {template?.columns.map((column) => (
                    <span key={column} className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-on-surface-variant">
                      {column}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-white/5 bg-white/3 p-5">
              <div className="mb-3 flex items-center gap-3">
                <div className="rounded-2xl border border-tertiary/20 bg-tertiary/10 p-3 text-tertiary">
                  <Route className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold">Template Preview</h3>
                  <p className="text-sm text-on-surface-variant">Paste these columns into Excel/CSV and replace with your real routes.</p>
                </div>
              </div>
              <pre className="overflow-x-auto rounded-2xl border border-white/5 bg-black/20 p-4 text-[11px] leading-5 text-on-surface-variant">
                {template ? JSON.stringify(template.sample_rows, null, 2) : "Loading template..."}
              </pre>
            </div>
          </div>
        </div>

        <div className="glass rounded-[28px] p-6">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 className="text-lg font-bold">Saved Uploads</h3>
              <p className="text-sm text-on-surface-variant">Re-open a previous network and run a fresh disruption check.</p>
            </div>
            {latestReport?.snapshot_id && (
              <button
                type="button"
                onClick={() => refresh(latestReport.snapshot_id)}
                className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-1.5 text-xs font-bold uppercase tracking-[0.2em] text-on-surface-variant transition-colors hover:border-primary/20 hover:text-primary"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Refresh
              </button>
            )}
          </div>

          <div className="mt-5 space-y-3">
            {bootLoading && <p className="text-sm text-on-surface-variant">Loading saved snapshots...</p>}
            {!bootLoading && snapshots.length === 0 && (
              <div className="rounded-2xl border border-dashed border-white/10 p-5 text-sm text-on-surface-variant">
                No uploaded networks yet. Upload a dependency file to start monitoring.
              </div>
            )}
            {snapshots.map((snapshot) => {
              const active = snapshot.snapshot_id === latestReport?.snapshot_id;
              return (
                <button
                  key={snapshot.snapshot_id}
                  type="button"
                  onClick={() => loadSnapshot(snapshot.snapshot_id, true)}
                  className={cn(
                    "w-full rounded-2xl border p-4 text-left transition-all",
                    active ? "border-primary/30 bg-primary/10" : "border-white/5 bg-white/3 hover:border-white/10"
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold">{snapshot.file_name}</p>
                      <p className="mt-1 text-xs text-on-surface-variant">{snapshot.route_count} routes captured</p>
                    </div>
                    <span className={cn("rounded-full border px-2 py-1 text-[10px] font-bold uppercase tracking-[0.2em]", active ? SOURCE_CLASSES.live : SOURCE_CLASSES.disabled)}>
                      {active ? "Open" : "Load"}
                    </span>
                  </div>
                  <p className="mt-3 text-xs text-on-surface-variant">
                    Uploaded {new Date(snapshot.uploaded_at).toLocaleString()}
                    {snapshot.last_checked_at ? ` • Last checked ${new Date(snapshot.last_checked_at).toLocaleString()}` : ""}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {error && (
        <div className="rounded-2xl border border-error/25 bg-error/10 px-4 py-3 text-sm text-error">
          {error}
        </div>
      )}

      {latestReport ? (
        <>
          <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricTile label="Total Routes" value={latestReport.metrics.total_routes} icon={Link2} tone="border-primary/20 bg-primary/10 text-primary" />
            <MetricTile label="Blocked Routes" value={latestReport.metrics.blocked_routes} icon={ShieldAlert} tone="border-error/20 bg-error/10 text-error" />
            <MetricTile label="At Risk" value={latestReport.metrics.at_risk_routes} icon={AlertTriangle} tone="border-warning/20 bg-warning/10 text-warning" />
            <MetricTile label="Live Alerts" value={latestReport.metrics.active_alerts} icon={Waves} tone="border-success/20 bg-success/10 text-success" />
          </section>

          <section className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
            <div className="glass rounded-[28px] p-6">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-bold">Monitoring Status</h3>
                  <p className="text-sm text-on-surface-variant">
                    Snapshot <span className="font-medium text-on-surface">{latestReport.file_name}</span> checked at{" "}
                    {new Date(latestReport.last_checked_at).toLocaleString()}.
                  </p>
                </div>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                {getSourceEntries(latestReport).map(([source, status]) => {
                  const tone = status.live ? SOURCE_CLASSES.live : status.enabled ? SOURCE_CLASSES.standby : SOURCE_CLASSES.disabled;
                  return (
                    <div key={source} className={cn("rounded-2xl border p-4", tone)}>
                      <p className="text-[11px] font-bold uppercase tracking-[0.22em]">{source}</p>
                      <p className="mt-2 text-sm font-semibold">
                        {status.live ? "Live" : status.enabled ? "Configured" : "Not configured"}
                      </p>
                      <p className="mt-1 text-xs opacity-80">{status.error ?? "Source checked successfully."}</p>
                    </div>
                  );
                })}
              </div>

              <div className="mt-6">
                <h4 className="text-sm font-bold uppercase tracking-[0.22em] text-on-surface-variant">Watchlist</h4>
                <div className="mt-3 flex flex-wrap gap-2">
                  {latestReport.watch_terms.map((term) => (
                    <span key={term} className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-on-surface-variant">
                      {term}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="glass rounded-[28px] p-6">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h3 className="text-lg font-bold">Current Disruption Signals</h3>
                  <p className="text-sm text-on-surface-variant">Live alerts that currently overlap your uploaded companies, materials, suppliers, or route endpoints.</p>
                </div>
              </div>

              <div className="mt-5 space-y-3">
                {latestReport.alerts.length === 0 && (
                  <div className="rounded-2xl border border-dashed border-white/10 p-5 text-sm text-on-surface-variant">
                    No overlapping disruption signals found in the latest check.
                  </div>
                )}

                {latestReport.alerts.map((alert) => (
                  <div key={alert.id} className="rounded-2xl border border-white/5 bg-white/3 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={cn("rounded-full border px-2 py-1 text-[10px] font-bold uppercase tracking-[0.2em]", STATUS_CLASSES[alert.type] ?? STATUS_CLASSES.watch)}>
                            {alert.type}
                          </span>
                          <span className="text-[10px] uppercase tracking-[0.2em] text-on-surface-variant">{alert.source}</span>
                        </div>
                        <p className="mt-3 font-semibold">{alert.title}</p>
                        <p className="mt-2 text-sm leading-6 text-on-surface-variant">{alert.description}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-on-surface-variant">Severity</p>
                        <p className="text-lg font-black">{Math.round(alert.severity * 100)}%</p>
                      </div>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {alert.locations.map((location) => (
                        <span key={location} className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] text-on-surface-variant">
                          {location}
                        </span>
                      ))}
                    </div>
                    <div className="mt-3 flex items-center justify-between gap-3 text-xs text-on-surface-variant">
                      <span>{new Date(alert.timestamp).toLocaleString()}</span>
                      {alert.url && (
                        <a className="text-primary hover:underline" href={alert.url} target="_blank" rel="noreferrer">
                          Open source
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="grid gap-6 xl:grid-cols-[1.08fr_0.92fr]">
            <div className="glass rounded-[28px] p-6">
              <div>
                <h3 className="text-lg font-bold">Impacted Trade Lanes</h3>
                <p className="text-sm text-on-surface-variant">Highest-risk supplier links in your uploaded network, ranked by matched disruption severity.</p>
              </div>
              <div className="mt-5 space-y-4">
                {latestReport.impacted_links.length === 0 && (
                  <div className="rounded-2xl border border-dashed border-white/10 p-5 text-sm text-on-surface-variant">
                    No route is currently flagged. Your uploaded network is being watched, but nothing overlaps the alert set right now.
                  </div>
                )}

                {latestReport.impacted_links.map((link) => (
                  <div key={link.route_id} className="rounded-3xl border border-white/5 bg-white/3 p-5">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={cn("rounded-full border px-2 py-1 text-[10px] font-bold uppercase tracking-[0.2em]", STATUS_CLASSES[link.status])}>
                            {link.status === "at_risk" ? "At Risk" : "Blocked"}
                          </span>
                          <span className="text-[10px] uppercase tracking-[0.2em] text-on-surface-variant">{link.transport_mode}</span>
                          <span className="text-[10px] uppercase tracking-[0.2em] text-on-surface-variant">{link.criticality}</span>
                        </div>
                        <h4 className="mt-3 text-lg font-bold">{link.route_name}</h4>
                        <p className="mt-1 text-sm text-on-surface-variant">{link.material}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs uppercase tracking-[0.2em] text-on-surface-variant">Risk Score</p>
                        <p className="text-2xl font-black">{Math.round(link.risk_score * 100)}%</p>
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-on-surface-variant">
                      <span className="font-medium text-on-surface">{link.source_company}</span>
                      <ArrowRight className="h-4 w-4" />
                      <span className="font-medium text-on-surface">{link.target_company}</span>
                      <span>•</span>
                      <span>{link.origin}</span>
                      <ArrowRight className="h-4 w-4" />
                      <span>{link.destination}</span>
                    </div>

                    <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_0.9fr]">
                      <div className="rounded-2xl border border-white/5 bg-black/10 p-4">
                        <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-on-surface-variant">Matched Alerts</p>
                        <div className="mt-3 space-y-3">
                          {link.matched_alerts.map((alert) => (
                            <div key={alert.alert_id} className="rounded-2xl border border-white/5 bg-white/3 p-3">
                              <div className="flex items-center justify-between gap-3">
                                <p className="text-sm font-semibold">{alert.alert_title}</p>
                                <span className="text-xs font-bold text-on-surface">{Math.round(alert.severity * 100)}%</span>
                              </div>
                              <p className="mt-2 text-xs leading-5 text-on-surface-variant">{alert.reasons.join(" • ")}</p>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-4">
                        <div className="rounded-2xl border border-white/5 bg-black/10 p-4">
                          <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-on-surface-variant">Alternate Route</p>
                          {link.alternative_route ? (
                            <div className="mt-3 space-y-3">
                              <div className="rounded-2xl border border-success/15 bg-success/5 p-3">
                                <div className="flex items-start justify-between gap-3">
                                  <div>
                                    <p className="text-sm font-semibold text-on-surface">{link.alternative_route.summary}</p>
                                    <p className="mt-2 text-xs leading-5 text-on-surface-variant">{link.alternative_route.reason}</p>
                                  </div>
                                  <div className="text-right">
                                    <p className="text-[11px] uppercase tracking-[0.2em] text-on-surface-variant">Projected Risk</p>
                                    <p className="text-lg font-black text-success">{Math.round(link.alternative_route.estimated_risk_score * 100)}%</p>
                                  </div>
                                </div>
                              </div>

                              <div className="grid gap-3 sm:grid-cols-2">
                                <div>
                                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-on-surface-variant">Company Path</p>
                                  <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-on-surface-variant">
                                    {link.alternative_route.company_path.map((company, index) => (
                                      <React.Fragment key={`${link.route_id}-company-${company}-${index}`}>
                                        {index > 0 && <ArrowRight className="h-3.5 w-3.5" />}
                                        <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1">{company}</span>
                                      </React.Fragment>
                                    ))}
                                  </div>
                                </div>

                                <div>
                                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-on-surface-variant">Location Path</p>
                                  <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-on-surface-variant">
                                    {link.alternative_route.location_path.map((location, index) => (
                                      <React.Fragment key={`${link.route_id}-location-${location}-${index}`}>
                                        {index > 0 && <ArrowRight className="h-3.5 w-3.5" />}
                                        <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1">{location}</span>
                                      </React.Fragment>
                                    ))}
                                  </div>
                                </div>
                              </div>

                              <div className="flex flex-wrap gap-2">
                                {link.alternative_route.route_names.map((routeName) => (
                                  <span key={`${link.route_id}-${routeName}`} className="rounded-full border border-success/15 bg-success/10 px-3 py-1 text-[11px] text-success">
                                    {routeName}
                                  </span>
                                ))}
                              </div>
                            </div>
                          ) : (
                            <p className="mt-3 text-sm text-on-surface-variant">
                              No safer alternate route was found inside the uploaded network yet. The lane stays monitored until a backup path or supplier is added.
                            </p>
                          )}
                        </div>

                        <div className="rounded-2xl border border-white/5 bg-black/10 p-4">
                          <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-on-surface-variant">Downstream Exposure</p>
                          <div className="mt-3 flex flex-wrap gap-2">
                            {link.downstream_companies.length > 0 ? (
                              link.downstream_companies.map((company) => (
                                <span key={company} className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-on-surface-variant">
                                  {company}
                                </span>
                              ))
                            ) : (
                              <span className="text-sm text-on-surface-variant">No downstream dependency recorded beyond this link.</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass rounded-[28px] p-6">
              <div>
                <h3 className="text-lg font-bold">Company Exposure</h3>
                <p className="text-sm text-on-surface-variant">Directly hit companies and downstream names that inherit risk from the disrupted lanes.</p>
              </div>

              <div className="mt-5 space-y-3">
                {latestReport.impacted_companies.length === 0 && (
                  <div className="rounded-2xl border border-dashed border-white/10 p-5 text-sm text-on-surface-variant">
                    No company exposure identified yet.
                  </div>
                )}

                {latestReport.impacted_companies.map((company) => (
                  <div key={company.company} className="rounded-2xl border border-white/5 bg-white/3 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold">{company.company}</p>
                        <p className="mt-1 text-xs text-on-surface-variant">
                          {company.direct_impacts > 0 ? `${company.direct_impacts} direct impacted route(s)` : "Indirect downstream exposure"}
                        </p>
                      </div>
                      <span className={cn("rounded-full border px-2 py-1 text-[10px] font-bold uppercase tracking-[0.2em]", STATUS_CLASSES[company.status] ?? STATUS_CLASSES.watch)}>
                        {company.status}
                      </span>
                    </div>
                    <div className="mt-4 flex items-end justify-between gap-4">
                      <div>
                        <p className="text-[11px] uppercase tracking-[0.2em] text-on-surface-variant">Risk</p>
                        <p className="text-xl font-black">{Math.round(company.risk_score * 100)}%</p>
                      </div>
                      <div className="max-w-[65%] text-right text-xs text-on-surface-variant">
                        {company.downstream_exposure.length > 0 ? `Impacted downstream by ${company.downstream_exposure.join(", ")}` : "Direct disruption overlap"}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </>
      ) : (
        <section className="glass rounded-[28px] p-10 text-center">
          <p className="text-lg font-semibold">No supply-chain snapshot loaded yet.</p>
          <p className="mt-2 text-sm text-on-surface-variant">
            Upload a CSV or JSON dependency file to create your first monitored network.
          </p>
        </section>
      )}
    </div>
  );
};
