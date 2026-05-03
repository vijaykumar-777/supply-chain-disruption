import React, { useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { useEvents } from "../../hooks/useAtlasData";
import { AlertCircle, TrendingUp, ShieldAlert, FileText } from "lucide-react";

const COLORS = ["#3b82f6", "#ef4444", "#f59e0b", "#10b981", "#8b5cf6"];

export const AnalyticsView = () => {
  const { events, loading } = useEvents(20000);

  const stats = useMemo(() => {
    if (!events.length) return { total: 0, critical: 0, byCategory: [], severityData: [] };
    
    const critical = events.filter(e => e.type === "critical").length;
    
    const catMap: Record<string, number> = {};
    events.forEach(e => {
      catMap[e.category] = (catMap[e.category] || 0) + 1;
    });
    const byCategory = Object.entries(catMap).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value);

    // Group by severity type
    const sevMap = { critical: 0, warning: 0, info: 0 };
    events.forEach(e => {
       if (e.type in sevMap) sevMap[e.type as keyof typeof sevMap]++;
    });
    const severityData = Object.entries(sevMap).map(([name, value]) => ({ name, value }));

    return { total: events.length, critical, byCategory, severityData };
  }, [events]);

  return (
    <div className="h-full flex flex-col gap-6 overflow-y-auto no-scrollbar pr-2 pb-4">
      <div>
        <h2 className="text-2xl font-bold text-on-surface">Relief Risk Analytics</h2>
        <p className="text-sm text-on-surface-variant">Breakdown of active flood, landslide, weather, and road-access hazards</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-elevated p-4 rounded-xl border border-primary/20 flex flex-col items-center justify-center text-center">
           <AlertCircle className="w-8 h-8 text-primary mb-2" />
           <p className="text-2xl font-bold text-on-surface">{stats.total}</p>
           <p className="text-xs text-on-surface-variant uppercase tracking-wider font-semibold">Active Hazards</p>
        </div>
        <div className="glass-elevated p-4 rounded-xl border border-error/30 flex flex-col items-center justify-center text-center bg-error/5 relative overflow-hidden">
           <div className="absolute top-0 right-0 w-16 h-16 bg-error/10 blur-xl rounded-full"></div>
           <ShieldAlert className="w-8 h-8 text-error mb-2 relative z-10" />
           <p className="text-2xl font-bold text-error relative z-10">{stats.critical}</p>
           <p className="text-xs text-error/80 uppercase tracking-wider font-semibold relative z-10">Critical Alerts</p>
        </div>
        <div className="glass-elevated p-4 rounded-xl border border-primary/10 flex flex-col items-center justify-center text-center opacity-50 grayscale">
           <TrendingUp className="w-8 h-8 text-on-surface-variant mb-2" />
           <p className="text-xl font-bold text-on-surface-variant">--</p>
           <p className="text-xs text-on-surface-variant uppercase tracking-wider">Rainfall Trends</p>
        </div>
        <div className="glass-elevated p-4 rounded-xl border border-primary/10 flex flex-col items-center justify-center text-center opacity-50 grayscale">
           <FileText className="w-8 h-8 text-on-surface-variant mb-2" />
           <p className="text-xl font-bold text-on-surface-variant">--</p>
           <p className="text-xs text-on-surface-variant uppercase tracking-wider">Export Sitrep</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-[320px]">
        <div className="glass-elevated p-5 rounded-xl border border-primary/10 flex flex-col">
          <h3 className="font-bold text-lg mb-6 text-on-surface">Hazard Distribution by Category</h3>
          <div className="flex-1 min-h-[250px]">
             {loading && events.length === 0 ? <p className="text-center mt-10 text-on-surface-variant">Loading...</p> : (
               <ResponsiveContainer width="100%" height="100%">
                 <PieChart>
                   <Pie data={stats.byCategory} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={70} outerRadius={90} paddingAngle={2} stroke="rgba(255,255,255,0.1)" strokeWidth={1}>
                     {stats.byCategory.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                   </Pie>
                   <RechartsTooltip contentStyle={{ backgroundColor: "#0f172a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", color: "#f8fafc" }} itemStyle={{ color: "#f8fafc" }}/>
                 </PieChart>
               </ResponsiveContainer>
             )}
          </div>
        </div>

        <div className="glass-elevated p-5 rounded-xl border border-primary/10 flex flex-col">
          <h3 className="font-bold text-lg mb-6 text-on-surface">Road-Access Threat Severities</h3>
          <div className="flex-1 min-h-[250px]">
             {loading && events.length === 0 ? <p className="text-center mt-10 text-on-surface-variant">Loading...</p> : (
               <ResponsiveContainer width="100%" height="100%">
                 <BarChart data={stats.severityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                   <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v) => v.charAt(0).toUpperCase() + v.slice(1)} />
                   <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                   <RechartsTooltip cursor={{fill: 'rgba(255,255,255,0.05)'}} contentStyle={{ backgroundColor: "#0f172a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", color: "#f8fafc" }} />
                   <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={60}>
                      {stats.severityData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.name === 'critical' ? '#ef4444' : entry.name === 'warning' ? '#f59e0b' : '#3b82f6'} />
                      ))}
                   </Bar>
                 </BarChart>
               </ResponsiveContainer>
             )}
          </div>
        </div>
      </div>
    </div>
  );
};
