import { useState, useEffect, useCallback } from "react";
import { api, DashboardMetrics, APIEvent, SimulationResult } from "../services/api";

// ─── useMetrics ───────────────────────────────────────────────────────────────
export function useMetrics(pollMs = 30000) {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    try {
      const data = await api.getMetrics();
      setMetrics(data);
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

  return { metrics, loading };
}

// ─── useEvents ────────────────────────────────────────────────────────────────
export function useEvents(pollMs = 15000) {
  const [events, setEvents] = useState<APIEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    try {
      const data = await api.getEvents();
      setEvents(data.events);
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

  return { events, loading, refresh: fetch };
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
