import React, { useState, useMemo } from "react";
import { AlertTriangle, Info, CloudRain, Search, RefreshCw, Download } from "lucide-react";
import { useEvents } from "../../hooks/useAtlasData";
import { cn } from "../../lib/utils";
import { APIEvent } from "../../services/api";

const SEVERITY_CLASSES: Record<string, { color: string; bg: string; border: string }> = {
  critical: { color: "text-error", bg: "bg-error/10", border: "border-error/20" },
  warning: { color: "text-tertiary", bg: "bg-tertiary/10", border: "border-tertiary/20" },
  info: { color: "text-primary", bg: "bg-primary/10", border: "border-primary/20" },
};

export const LiveFeedView = () => {
  const { events, loading, refresh, source } = useEvents(15000);
  
  const [search, setSearch] = useState("");
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [filterCategory, setFilterCategory] = useState<string>("all");

  const categories = useMemo(() => {
    const cats = new Set(events.map(e => e.category));
    return ["all", ...Array.from(cats)];
  }, [events]);

  const filteredEvents = useMemo(() => {
    return events.filter(e => {
      if (filterSeverity !== "all" && e.type !== filterSeverity) return false;
      if (filterCategory !== "all" && e.category.toLowerCase() !== filterCategory.toLowerCase()) return false;
      if (search) {
        const q = search.toLowerCase();
        if (!e.title.toLowerCase().includes(q) && !e.description.toLowerCase().includes(q) && !e.locations.some(l => l.toLowerCase().includes(q))) return false;
      }
      return true;
    });
  }, [events, search, filterSeverity, filterCategory]);

  return (
    <div className="h-full flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-on-surface">Live Disruption Feed</h2>
          <p className="text-sm text-on-surface-variant">
            {source === "live" ? "Real-time supply chain event monitoring from Neo4j" : "No live event stream is currently available"}
          </p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={refresh} 
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface/50 border border-primary/20 hover:bg-primary/10 transition text-sm"
          >
            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
            Refresh
          </button>
        </div>
      </div>

      <div className="glass-elevated p-4 rounded-xl flex flex-wrap gap-4 items-center">
        <div className="flex bg-surface/50 border border-primary/20 rounded-lg px-3 py-2 flex-1 min-w-[200px]">
          <Search className="w-4 h-4 text-on-surface-variant mr-2 opacity-50" />
          <input 
            type="text" 
            placeholder="Search events or locations..."
            className="bg-transparent border-none focus:outline-none text-sm w-full text-on-surface"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <select 
          className="bg-surface/50 border border-primary/20 rounded-lg px-3 py-2 text-sm focus:outline-none text-on-surface"
          value={filterSeverity}
          onChange={e => setFilterSeverity(e.target.value)}
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical Only</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
        </select>
        <select 
          className="bg-surface/50 border border-primary/20 rounded-lg px-3 py-2 text-sm focus:outline-none capitalize text-on-surface"
          value={filterCategory}
          onChange={e => setFilterCategory(e.target.value)}
        >
          {categories.map(c => <option key={c} value={c}>{c === "all" ? "All Categories" : c}</option>)}
        </select>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 pr-2 no-scrollbar">
        {loading && events.length === 0 && <p className="text-on-surface-variant text-center p-10">Loading active events...</p>}
        {!loading && filteredEvents.length === 0 && <p className="text-on-surface-variant text-center p-10">No events found matching criteria.</p>}
        
        {filteredEvents.map(event => {
          const cls = SEVERITY_CLASSES[event.type] || SEVERITY_CLASSES.info;
          return (
            <div key={event.id} className="glass-elevated p-5 rounded-xl border border-primary/10 flex flex-col md:flex-row gap-4 hover:border-primary/30 transition">
              <div className={cn("w-12 h-12 rounded-full flex items-center justify-center shrink-0 border", cls.bg, cls.color, cls.border)}>
                 {event.type === 'critical' ? <AlertTriangle className="w-5 h-5" /> : event.type === 'warning' ? <AlertTriangle className="w-5 h-5 opacity-70" /> : <Info className="w-5 h-5" /> }
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-start mb-1">
                  <h3 className="font-bold text-lg text-on-surface">{event.title}</h3>
                  <span className="text-xs font-medium text-on-surface-variant">
                    {new Date(event.timestamp).toLocaleString()}
                  </span>
                </div>
                <div className="flex gap-2 mb-3">
                  <span className={cn("text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded", cls.bg, cls.color)}>{event.type}</span>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-surface/50 border border-white/10">{event.category}</span>
                </div>
                <p className="text-on-surface-variant text-sm col-span-full">{event.description}</p>
                {event.locations.length > 0 && (
                  <div className="mt-3 flex gap-2 flex-wrap text-xs text-on-surface-variant">
                    <span className="opacity-50">Affected:</span>
                    {event.locations.map((loc, i) => <span key={i} className="font-medium text-on-surface bg-white/5 px-1.5 rounded border border-white/10">{loc}</span>)}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
