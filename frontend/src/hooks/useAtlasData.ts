import { startTransition, useState, useEffect, useCallback } from "react";
import {
  api,
  DashboardMetrics,
  APIEvent,
  SimulationResult,
  DataSource,
  APINode,
  SupplyChainReport,
  SupplyChainTemplate,
  SupplyChainSnapshotSummary,
  CompanyIntelCompany,
  CompanyIntelBulkImportResponse,
  CompanyIntelImportResponse,
  CompanyIntelSearchResponse,
  CompanyIntelSourceStatusItem,
  APILink,
} from "../services/api";

// ─── useMetrics ───────────────────────────────────────────────────────────────
export function useMetrics(pollMs = 30000) {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState<DataSource | null>(null);  // Fix #10

  const fetch = useCallback(async () => {
    try {
      const data = await api.getMetrics();
      setMetrics(data);
      setSource(data.source ?? null);  // Fix #10
    } catch (e) {
      console.warn("Metrics fetch failed, using cached data", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    const id = setInterval(fetch, pollMs);
    return () => clearInterval(id);
  }, [fetch, pollMs]);

  return { metrics, loading, source };  // Fix #10
}

// ─── useEvents ────────────────────────────────────────────────────────────────
export function useEvents(pollMs = 15000) {
  const [events, setEvents] = useState<APIEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState<DataSource | null>(null);  // Fix #10

  const fetch = useCallback(async () => {
    try {
      const data = await api.getEvents();
      setEvents(data.events);
      setSource(data.source ?? null);  // Fix #10
    } catch (e) {
      console.warn("Events fetch failed", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    const id = setInterval(fetch, pollMs);
    return () => clearInterval(id);
  }, [fetch, pollMs]);

  const ingestLiveSignals = useCallback(async () => {
    setLoading(true);
    try {
      await api.ingestEvents();
      await fetch();
    } catch (e) {
      console.error("Failed to ingest live signals", e);
    } finally {
      setLoading(false);
    }
  }, [fetch]);

  return { events, loading, refresh: fetch, ingestLiveSignals, source };  // Fix #10
}

// ─── useGraphNodes ────────────────────────────────────────────────────────────
export function useGraphNodes(pollMs = 30000) {
  const [nodes, setNodes] = useState<APINode[]>([]);
  const [links, setLinks] = useState<APILink[]>([]);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState<DataSource | null>(null);

  const fetch = useCallback(async () => {
    try {
      const data = await api.getGraphNodes();
      setNodes(data.nodes);
      setLinks(data.links || []);
      setSource(data.source ?? null);
    } catch (e) {
      console.warn("Graph nodes fetch failed", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    const id = setInterval(fetch, pollMs);
    return () => clearInterval(id);
  }, [fetch, pollMs]);

  return { nodes, links, loading, refresh: fetch, source };
}

// ─── useSimulation ───────────────────────────────────────────────────────────
export function useSimulation() {
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(
    async (source: string, target: string, disruptedNodes: string[] = []) => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.simulate(source, target, disruptedNodes);
        setResult(data);
        return data;
      } catch (e: any) {
        setError(e.message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { result, loading, error, run };
}

// ─── useRecommendation ────────────────────────────────────────────────────────
export function useRecommendation() {
  const [result, setResult] = useState<{ recommendation_id: string; recommendation: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(
    async (
      eventTitle: string,
      eventCategory: string,
      locations: string[],
      simulationResults: object,
      altRoute: string[] = []
    ) => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.recommend(eventTitle, eventCategory, locations, simulationResults, altRoute);
        setResult(data);
        return data;
      } catch (e: any) {
        setError(e.message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { result, loading, error, run };
}

// ─── useFeedback ──────────────────────────────────────────────────────────────
export function useFeedback() {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<boolean | null>(null);

  const submit = useCallback(async (recommendationId: string, rating: number, comment = "") => {
    setLoading(true);
    setSuccess(null);
    try {
      const res = await api.feedback(recommendationId, rating, comment);
      setSuccess(res.success);
      return res.success;
    } catch (e: any) {
      console.error(e);
      setSuccess(false);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return { submit, loading, success };
}

// ─── useCompanyIntelligence ──────────────────────────────────────────────────
export function useCompanyIntelligence() {
  const [results, setResults] = useState<CompanyIntelCompany[]>([]);
  const [sourceStatus, setSourceStatus] = useState<Record<string, CompanyIntelSourceStatusItem>>({});
  const [loading, setLoading] = useState(false);
  const [importingId, setImportingId] = useState<string | null>(null);
  const [lastImport, setLastImport] = useState<CompanyIntelImportResponse | null>(null);
  const [bulkImportLoading, setBulkImportLoading] = useState(false);
  const [lastBulkImport, setLastBulkImport] = useState<CompanyIntelBulkImportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (query: string, limit = 8) => {
    setLoading(true);
    setError(null);
    try {
      const data: CompanyIntelSearchResponse = await api.searchCompanyIntelligence(query, limit);
      startTransition(() => {
        setResults(data.companies);
        setSourceStatus(data.source_status);
      });
      return data;
    } catch (e: any) {
      setError(e.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const importCompany = useCallback(async (company: CompanyIntelCompany) => {
    setImportingId(company.entity_id);
    setError(null);
    try {
      const data = await api.importCompanyIntelligence([
        {
          lei: company.lei ?? undefined,
          cik: company.cik ?? undefined,
          name: company.name,
          ticker: company.ticker ?? undefined,
        },
      ]);
      startTransition(() => {
        setLastImport(data);
      });
      return data;
    } catch (e: any) {
      setError(e.message);
      return null;
    } finally {
      setImportingId(null);
    }
  }, []);

  const bulkImportCompanies = useCallback(async (companyNames: string[]) => {
    setBulkImportLoading(true);
    setError(null);
    try {
      const data = await api.importCompanyIntelligenceBulk(companyNames);
      startTransition(() => {
        setLastBulkImport(data);
      });
      return data;
    } catch (e: any) {
      setError(e.message);
      return null;
    } finally {
      setBulkImportLoading(false);
    }
  }, []);

  return {
    results,
    sourceStatus,
    loading,
    importingId,
    bulkImportLoading,
    lastImport,
    lastBulkImport,
    error,
    search,
    importCompany,
    bulkImportCompanies,
  };
}

// ─── useSupplyChainMonitor ────────────────────────────────────────────────────
export function useSupplyChainMonitor(pollMs = 30000) {
  const [report, setReport] = useState<SupplyChainReport | null>(null);
  const [template, setTemplate] = useState<SupplyChainTemplate | null>(null);
  const [snapshots, setSnapshots] = useState<SupplyChainSnapshotSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [bootLoading, setBootLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTemplateAndSnapshots = useCallback(async () => {
    try {
      const [templateData, snapshotsData] = await Promise.all([
        api.getSupplyChainTemplate(),
        api.listSupplyChainSnapshots(),
      ]);
      startTransition(() => {
        setTemplate(templateData);
        setSnapshots(snapshotsData.snapshots);
      });
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBootLoading(false);
    }
  }, []);

  const refresh = useCallback(async (snapshotId?: string) => {
    const activeSnapshotId = snapshotId ?? report?.snapshot_id;
    if (!activeSnapshotId) {
      return null;
    }

    try {
      const data = await api.getSupplyChainSnapshot(activeSnapshotId, true);
      startTransition(() => {
        setReport(data);
      });
      return data;
    } catch (e: any) {
      setError(e.message);
      return null;
    }
  }, [report?.snapshot_id]);

  const uploadFile = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.uploadSupplyChainFile(file);
      startTransition(() => {
        setReport(data);
        setSnapshots(prev => [
          {
            snapshot_id: data.snapshot_id,
            file_name: data.file_name,
            uploaded_at: data.uploaded_at,
            route_count: data.metrics.total_routes,
            last_checked_at: data.last_checked_at,
          },
          ...prev.filter(item => item.snapshot_id !== data.snapshot_id),
        ]);
      });
      return data;
    } catch (e: any) {
      setError(e.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSnapshot = useCallback(async (snapshotId: string, refreshRemote = false) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSupplyChainSnapshot(snapshotId, refreshRemote);
      startTransition(() => {
        setReport(data);
      });
      return data;
    } catch (e: any) {
      setError(e.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTemplateAndSnapshots();
  }, [loadTemplateAndSnapshots]);

  useEffect(() => {
    if (!report?.snapshot_id) {
      return;
    }
    const id = setInterval(() => {
      refresh(report.snapshot_id);
    }, pollMs);
    return () => clearInterval(id);
  }, [pollMs, refresh, report?.snapshot_id]);

  return {
    report,
    template,
    snapshots,
    loading,
    bootLoading,
    error,
    uploadFile,
    refresh,
    loadSnapshot,
  };
}
