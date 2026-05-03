import React, { useMemo } from "react";
import {
  AlertTriangle,
  Zap,
  CloudRain,
  Brain,
  RefreshCw,
  Wifi,
  WifiOff,
} from "lucide-react";
import { ResponsiveContainer, AreaChart, Area } from "recharts";
import { MetricCard } from "./MetricCard";
import { cn } from "../../lib/utils";
import { useMetrics, useEvents } from "../../hooks/useAtlasData";

const SEVERITY_CLASSES: Record<string, { color: string; bg: string; border: string }> = {
  critical: { color: "text-error", bg: "bg-error/10", border: "border-error/20" },
  warning: { color: "text-tertiary", bg: "bg-tertiary/10", border: "border-tertiary/20" },
  info: { color: "text-primary", bg: "bg-primary/10", border: "border-primary/20" },
};

export const DashboardView = () => {
  const { metrics, loading: mLoading, source: metricsSource } = useMetrics();
  const { events, loading: eLoading, refresh, source: eventsSource, ingestLiveSignals } = useEvents();
  const liveEventTrend = useMemo(() => {
    const days = 7;
    const formatter = new Intl.DateTimeFormat("en-US", { weekday: "short" });
    const buckets = Array.from({ length: days }, (_, index) => {
      const day = new Date();
      day.setHours(0, 0, 0, 0);
      day.setDate(day.getDate() - (days - index - 1));
      return {
        day,
        key: day.toISOString().slice(0, 10),
        name: formatter.format(day),
        value: 0,
      };
    });

    const bucketMap = new Map(buckets.map((bucket) => [bucket.key, bucket]));
    events.forEach((event) => {
      const key = new Date(event.timestamp).toISOString().slice(0, 10);
      const bucket = bucketMap.get(key);
      if (bucket) {
        bucket.value += 1;
      }
    });

    return buckets.map(({ name, value }) => ({ name, value }));
  }, [events]);

  const totalEvents = mLoading ? "—" : String(metrics?.total_active_events ?? "—");
  const highRisk = mLoading ? "—" : String(metrics?.high_risk_nodes ?? "—");
  const weatherAlerts = mLoading ? "—" : String(metrics?.weather_alerts ?? "0");
  const monitored = mLoading ? "—" : String(metrics?.monitored_nodes ?? "—");
  const isLive = !mLoading && metrics !== null;
  const dataSource = metricsSource ?? eventsSource;
  const sourceLabel = dataSource === "live" ? "Neo4j Live" : dataSource === "demo" ? "Demo Scenario" : "Unavailable";
  const isNeo4jLive = dataSource === "live";

  return (
    <div className="space-y-6">
      {/* Live indicator pill */}
      <div className="flex items-center gap-2">
        {isLive ? (
          <span className="flex items-center gap-1.5 text-success text-xs font-bold">
            <Wifi className="w-3 h-3" />
            Connected to ReliefRoute API
          </span>
        ) : (
          <span className="flex items-center gap-1.5 text-on-surface-variant text-xs">
            <WifiOff className="w-3 h-3" />
            Connecting...
          </span>
        )}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard label="Active Hazards" value={totalEvents} trend={sourceLabel} icon={AlertTriangle} colorClass="bg-error/10 text-error" pulse={isLive} />
        <MetricCard label="High Risk Roads" value={highRisk} trend={sourceLabel} icon={Zap} colorClass="bg-tertiary/10 text-tertiary" />
        <MetricCard label="Weather Alerts" value={weatherAlerts} trend="live" icon={CloudRain} colorClass="bg-primary/10 text-primary" />
        <MetricCard label="Monitored Points" value={monitored} trend={sourceLabel} icon={Brain} colorClass="bg-success/10 text-success" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map placeholder with summary */}
        <div className="lg:col-span-2 glass rounded-xl relative overflow-hidden min-h-[500px]">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(125,211,252,0.12),transparent_38%),linear-gradient(135deg,rgba(15,23,42,0.95),rgba(12,18,34,0.95))]" />
          <div className="absolute top-4 left-4 z-10">
            <h3 className="text-lg font-bold flex items-center gap-2">
              Karnataka Relief Map
              <span className={cn("flex h-2 w-2 rounded-full", isLive ? "bg-success animate-pulse" : "bg-on-surface-variant")} />
            </h3>
            <p className="text-xs text-on-surface-variant font-medium">Relief hubs, roads, villages, and active disruption overlays</p>
          </div>

          <div className="absolute bottom-4 left-4 z-10 glass-elevated px-3 py-2 rounded-lg text-xs space-y-2">
            <div className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-error border border-white/20" /><span>Blocked roads</span></div>
            <div className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-primary border border-white/20" /><span>Relief points</span></div>
          </div>

          {/* Live event stats overlay */}
          <div className="absolute top-1/3 left-1/2 -translate-x-1/2 z-20 glass-elevated p-4 rounded-xl border border-primary/30 w-56 shadow-2xl">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[10px] font-bold uppercase text-on-surface-variant tracking-widest">Relief Situation</span>
              <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-bold", events.some(e => e.type === "critical") ? "bg-error/20 text-error" : "bg-success/20 text-success")}>
                {events.some(e => e.type === "critical") ? "DISRUPTED" : "NORMAL"}
              </span>
            </div>
            <h4 className="text-sm font-bold mb-3">{events[0]?.title ?? "No current disruptions"}</h4>
            <div className="space-y-2">
              <div className="flex justify-between text-xs"><span className="text-on-surface-variant">Hazards:</span><span className="text-on-surface">{events.length} active</span></div>
              <div className="flex justify-between text-xs"><span className="text-on-surface-variant">Critical:</span><span className="text-on-surface">{events.filter(e => e.type === "critical").length}</span></div>
              <div className="flex justify-between text-xs"><span className="text-on-surface-variant">Source:</span><span className={cn("font-bold", isNeo4jLive ? "text-success" : dataSource === "demo" ? "text-primary" : "text-tertiary")}>{sourceLabel}</span></div>
            </div>
            <p className="mt-4 rounded-lg border border-primary/20 bg-primary/10 px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-primary">
              Open Karnataka Map for full route view
            </p>
          </div>
        </div>

        {/* Live Event Feed */}
        <div className="glass rounded-xl flex flex-col h-full max-h-[500px]">
          <div className="p-4 border-b border-white/5 flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-widest">Weather And Road Feed</h3>
            <div className="flex items-center gap-2">
              <button 
                onClick={ingestLiveSignals}
                disabled={eLoading}
                className="px-2 py-1 text-[10px] font-bold rounded bg-tertiary/20 text-tertiary hover:bg-tertiary/30 border border-tertiary/30 transition-colors uppercase tracking-widest flex items-center gap-1 disabled:opacity-50"
              >
                Ingest Hazards
              </button>
              <span className="text-[10px] text-primary bg-primary/10 px-2 py-1 rounded font-bold uppercase tracking-widest">{sourceLabel}</span>
              <button onClick={refresh} className="p-1 hover:bg-white/5 rounded" title="Refresh">
                <RefreshCw className={cn("w-3.5 h-3.5 text-on-surface-variant", eLoading && "animate-spin")} />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4 no-scrollbar">
            {eLoading && <p className="text-xs text-on-surface-variant">Loading events...</p>}
            {!eLoading && events.length === 0 && <p className="text-xs text-on-surface-variant">No active flood, landslide, or road disruption signals detected.</p>}
            {events.map(event => {
              const cls = SEVERITY_CLASSES[event.type] ?? SEVERITY_CLASSES.info;
              return (
                <div key={event.id} className="flex gap-3 group">
                  <div className={cn("flex-shrink-0 mt-1 w-2 h-2 rounded-full mt-2 ring-2 ring-offset-1 ring-offset-background", cls.bg, event.type === "critical" ? "bg-error animate-pulse" : event.type === "warning" ? "bg-tertiary" : "bg-primary")} />
                  <div className="space-y-1 flex-1">
                    <div className="flex justify-between items-start">
                      <p className="text-xs font-bold leading-tight">{event.title}</p>
                      <span className="text-[9px] text-on-surface-variant uppercase font-medium">
                        {new Date(event.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <span className={cn("inline-block text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-tighter", cls.bg, cls.color)}>
                      {event.type}
                    </span>
                    <p className="text-[11px] text-on-surface-variant leading-relaxed">{event.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Chart + AI Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 glass rounded-xl p-6">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h3 className="font-bold text-sm uppercase tracking-widest">Hazards Over Time</h3>
              <p className="text-xs text-on-surface-variant">Daily count of flood, landslide, and road disruption signals in the current feed</p>
            </div>
            <div className="flex gap-2">
              <button className="px-2 py-1 text-[10px] font-bold rounded-md bg-primary/10 text-primary border border-primary/20">7 DAYS</button>
            </div>
          </div>
          <div className="h-48 w-full">
            {liveEventTrend.some((entry) => entry.value > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={liveEventTrend}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#7dd3fc" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#7dd3fc" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area type="monotone" dataKey="value" stroke="#7dd3fc" strokeWidth={3} fillOpacity={1} fill="url(#colorValue)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-white/10 text-sm text-on-surface-variant">
                No hazard history available yet.
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-1 glass rounded-xl p-5 bg-gradient-to-br from-surface/60 to-tertiary/10 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-tertiary/20 flex items-center justify-center text-tertiary border border-tertiary/30">
                <Brain className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold">Relief Route Advisor</h4>
                <span className="text-[10px] text-tertiary">Powered by local Llama-3.2</span>
              </div>
            </div>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              {events.length > 0
                ? `${events.filter(e => e.type === "critical").length} critical hazard(s) detected. Open AI Assistant to simulate blocked roads and generate response actions.`
                : "No active hazards are currently available. Connect Neo4j or enable demo mode to test route analysis."}
            </p>
          </div>
          <p className="mt-6 rounded-lg border border-tertiary/20 bg-tertiary/10 px-3 py-2 text-xs font-bold uppercase tracking-widest text-tertiary">
            Use AI Assistant for route simulation
          </p>
        </div>
      </div>
    </div>
  );
};
