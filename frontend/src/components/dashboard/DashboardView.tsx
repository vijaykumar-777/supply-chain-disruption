import React from "react";
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
import { LOGISTICS_VOLUME_DATA } from "../../constants/mockData";
import { cn } from "../../lib/utils";
import { useMetrics, useEvents } from "../../hooks/useAtlasData";

const SEVERITY_CLASSES: Record<string, { color: string; bg: string; border: string }> = {
  critical: { color: "text-error", bg: "bg-error/10", border: "border-error/20" },
  warning: { color: "text-tertiary", bg: "bg-tertiary/10", border: "border-tertiary/20" },
  info: { color: "text-primary", bg: "bg-primary/10", border: "border-primary/20" },
};

export const DashboardView = () => {
  const { metrics, loading: mLoading, source: metricsSource } = useMetrics();
  const { events, loading: eLoading, refresh, source: eventsSource } = useEvents();

  const totalEvents = mLoading ? "—" : String(metrics?.total_active_events ?? "—");
  const highRisk = mLoading ? "—" : String(metrics?.high_risk_nodes ?? "—");
  const weatherAlerts = mLoading ? "—" : String(metrics?.weather_alerts ?? "0");
  const monitored = mLoading ? "—" : String(metrics?.monitored_nodes ?? "—");
  const isLive = !mLoading && metrics !== null;
  // Fix #10: Truthful data source indicator
  const dataSource = metricsSource ?? eventsSource;
  const isNeo4jLive = dataSource === "live";

  return (
    <div className="space-y-6">
      {/* Live indicator pill */}
      <div className="flex items-center gap-2">
        {isLive ? (
          <span className="flex items-center gap-1.5 text-success text-xs font-bold">
            <Wifi className="w-3 h-3" />
            Connected to ATLAS API
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
        <MetricCard label="Total Active Events" value={totalEvents} trend="+live" icon={AlertTriangle} colorClass="bg-error/10 text-error" pulse={isLive} />
        <MetricCard label="High Risk Nodes" value={highRisk} trend="live" icon={Zap} colorClass="bg-tertiary/10 text-tertiary" />
        <MetricCard label="Weather Alerts" value={weatherAlerts} trend="live" icon={CloudRain} colorClass="bg-primary/10 text-primary" />
        <MetricCard label="Monitored Nodes" value={monitored} trend="live" icon={Brain} colorClass="bg-success/10 text-success" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map placeholder with summary */}
        <div className="lg:col-span-2 glass rounded-xl relative overflow-hidden min-h-[500px]">
          <div className="absolute inset-0 bg-[url('https://picsum.photos/seed/map/1200/800')] bg-cover bg-center opacity-20 mix-blend-luminosity" />
          <div className="absolute top-4 left-4 z-10">
            <h3 className="text-lg font-bold flex items-center gap-2">
              Global Supply Chain Map
              <span className={cn("flex h-2 w-2 rounded-full", isLive ? "bg-success animate-pulse" : "bg-on-surface-variant")} />
            </h3>
            <p className="text-xs text-on-surface-variant font-medium">Real-time Node Monitoring — Switch to Global Map tab for full Leaflet view</p>
          </div>

          <div className="absolute bottom-4 left-4 z-10 glass-elevated px-3 py-2 rounded-lg text-xs space-y-2">
            <div className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-error border border-white/20" /><span>Disruptions</span></div>
            <div className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-primary border border-white/20" /><span>Healthy Nodes</span></div>
          </div>

          {/* Live event stats overlay */}
          <div className="absolute top-1/3 left-1/2 -translate-x-1/2 z-20 glass-elevated p-4 rounded-xl border border-primary/30 w-56 shadow-2xl">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[10px] font-bold uppercase text-on-surface-variant tracking-widest">Live Events</span>
              <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-bold", events.some(e => e.type === "critical") ? "bg-error/20 text-error" : "bg-success/20 text-success")}>
                {events.some(e => e.type === "critical") ? "DISRUPTED" : "NORMAL"}
              </span>
            </div>
            <h4 className="text-sm font-bold mb-3">{events[0]?.title ?? "No current disruptions"}</h4>
            <div className="space-y-2">
              <div className="flex justify-between text-xs"><span className="text-on-surface-variant">Events:</span><span className="text-on-surface">{events.length} active</span></div>
              <div className="flex justify-between text-xs"><span className="text-on-surface-variant">High Risk:</span><span className="text-on-surface">{events.filter(e => e.type === "critical").length} critical</span></div>
              <div className="flex justify-between text-xs"><span className="text-on-surface-variant">Source:</span><span className={cn("font-bold", isNeo4jLive ? "text-success" : "text-tertiary")}>{isNeo4jLive ? "Neo4j Live" : "Demo / Fallback"}</span></div>
            </div>
            <button className="w-full mt-4 py-2 bg-primary/20 hover:bg-primary/30 text-primary text-[10px] font-bold rounded transition-colors uppercase tracking-widest">
              View Full Map
            </button>
          </div>
        </div>

        {/* Live Event Feed */}
        <div className="glass rounded-xl flex flex-col h-full max-h-[500px]">
          <div className="p-4 border-b border-white/5 flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-widest">Live Event Feed</h3>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-primary bg-primary/10 px-2 py-0.5 rounded-full font-bold">REAL-TIME</span>
              <button onClick={refresh} className="p-1 hover:bg-white/5 rounded" title="Refresh">
                <RefreshCw className={cn("w-3.5 h-3.5 text-on-surface-variant", eLoading && "animate-spin")} />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4 no-scrollbar">
            {eLoading && <p className="text-xs text-on-surface-variant">Loading events...</p>}
            {!eLoading && events.length === 0 && (
              <p className="text-xs text-on-surface-variant">No active disruptions detected.</p>
            )}
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
              <h3 className="font-bold text-sm uppercase tracking-widest">Supply Chain Delays vs Time</h3>
              <p className="text-xs text-on-surface-variant">Aggregate network latency across all global hubs</p>
            </div>
            <div className="flex gap-2">
              <button className="px-2 py-1 text-[10px] font-bold rounded-md bg-primary/10 text-primary border border-primary/20">7 DAYS</button>
              <button className="px-2 py-1 text-[10px] font-bold rounded-md text-on-surface-variant hover:bg-white/5">30 DAYS</button>
            </div>
          </div>
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={LOGISTICS_VOLUME_DATA}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#7dd3fc" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#7dd3fc" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area type="monotone" dataKey="value" stroke="#7dd3fc" strokeWidth={3} fillOpacity={1} fill="url(#colorValue)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="lg:col-span-1 glass rounded-xl p-5 bg-gradient-to-br from-surface/60 to-tertiary/10 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-tertiary/20 flex items-center justify-center text-tertiary border border-tertiary/30">
                <Brain className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold">AI Optimization</h4>
                <span className="text-[10px] text-tertiary">Powered by ATLAS Llama-3.2</span>
              </div>
            </div>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              {events.length > 0
                ? `${events.filter(e => e.type === "critical").length} critical disruption(s) detected. AI recommendations are available via the AI Assistant panel → Switch to "AI Assistant" view.`
                : "No active disruptions. All supply chain routes are operating normally."}
            </p>
          </div>
          <button className="w-full mt-6 py-2.5 bg-tertiary text-background text-xs font-bold rounded-lg hover:bg-tertiary/80 transition-all shadow-lg shadow-tertiary/10">
            Run Risk Simulation
          </button>
        </div>
      </div>
    </div>
  );
};
