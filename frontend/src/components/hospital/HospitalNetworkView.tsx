import React, { useState, useEffect, useCallback } from "react";
import {
  MapPin,
  Route,
  AlertTriangle,
  Hospital,
  Activity,
  Navigation,
  Clock,
  Shield,
  Zap,
  RefreshCw,
  Search,
  Filter,
  ChevronRight,
  Building2,
  FlaskConical,
  Siren,
} from "lucide-react";
import { api, type Hospital as HospitalType, type Route as RouteType, type DisasterAlert, type NetworkSummary, type RouteOptimizationResult } from "../../services/api";
import { cn } from "../../lib/utils";

const SEVERITY_COLORS: Record<string, string> = {
  flood: "text-cyan-400 border-cyan-400/30 bg-cyan-400/10",
  landslide: "text-amber-400 border-amber-400/30 bg-amber-400/10",
  fire: "text-red-400 border-red-400/30 bg-red-400/10",
  bridge_collapse: "text-purple-400 border-purple-400/30 bg-purple-400/10",
};

const DISTRCIT_COLORS: Record<string, string> = {
  "Bengaluru Urban": "bg-blue-500/20 text-blue-400 border-blue-500/30",
  "Mysuru": "bg-purple-500/20 text-purple-400 border-purple-500/30",
  "Hubballi": "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  "Belagavi": "bg-green-500/20 text-green-400 border-green-500/30",
  "Mangaluru": "bg-orange-500/20 text-orange-400 border-orange-500/30",
  "Shivamogga": "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  "Ballari": "bg-pink-500/20 text-pink-400 border-pink-500/30",
  "Davanagere": "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  "Tumakuru": "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
  "Kalaburagi": "bg-rose-500/20 text-rose-400 border-rose-500/30",
};

function formatTime(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

function formatDistance(km: number): string {
  return `${km.toFixed(1)} km`;
}

interface HospitalCardProps {
  hospital: HospitalType;
  onClick: () => void;
  isSelected: boolean;
}

const HospitalCard: React.FC<HospitalCardProps> = ({ hospital, onClick, isSelected }) => (
  <div
    onClick={onClick}
    className={cn(
      "cursor-pointer rounded-xl border p-4 transition-all duration-300 hover:scale-[1.02]",
      isSelected
        ? "border-cyan-500/50 bg-cyan-500/10 shadow-lg shadow-cyan-500/20"
        : "border-white/10 bg-black/20 hover:border-white/20 hover:bg-black/40"
    )}
  >
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <Hospital className="h-4 w-4 text-cyan-400" />
          <span className={cn("rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
            DISTRCIT_COLORS[hospital.district] || "border-white/20 text-white/60")}>
            {hospital.district}
          </span>
        </div>
        <h4 className="mt-2 truncate font-semibold text-white">{hospital.hospital_name}</h4>
      </div>
    </div>

    <div className="mt-3 flex items-center gap-4 text-xs text-white/60">
      <div className="flex items-center gap-1">
        <Building2 className="h-3 w-3" />
        <span>{hospital.available_beds}/{hospital.capacity} beds</span>
      </div>
      {hospital.oxygen_available && (
        <div className="flex items-center gap-1">
          <Zap className="h-3 w-3 text-green-400" />
          <span className="text-green-400">O2</span>
        </div>
      )}
    </div>
  </div>
);

interface AlertCardProps {
  alert: DisasterAlert;
}

const AlertCard: React.FC<AlertCardProps> = ({ alert }) => {
  const cls = SEVERITY_COLORS[alert.disaster_type] || "text-white border-white/20";

  return (
    <div className={cn("rounded-lg border p-3", cls)}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Siren className="h-4 w-4" />
          <span className="font-semibold capitalize">{alert.disaster_type.replace("_", " ")}</span>
        </div>
        <span className="rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase">
          {(alert.severity * 100).toFixed(0)}%
        </span>
      </div>
      <p className="mt-1 text-xs text-white/70">{alert.location_name}, {alert.district}</p>
    </div>
  );
};

interface RouteCardProps {
  route: RouteType;
  onClick: () => void;
  isSelected: boolean;
}

const RouteCard: React.FC<RouteCardProps> = ({ route, onClick, isSelected }) => (
  <div
    onClick={onClick}
    className={cn(
      "cursor-pointer rounded-lg border p-3 transition-all",
      route.blocked
        ? "border-red-500/30 bg-red-500/10"
        : isSelected
        ? "border-green-500/50 bg-green-500/10"
        : "border-white/10 bg-black/20 hover:bg-black/40"
    )}
  >
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        {route.blocked ? (
          <AlertTriangle className="h-4 w-4 text-red-400" />
        ) : (
          <Route className="h-4 w-4 text-green-400" />
        )}
        <span className="text-sm text-white">{route.source_name}</span>
        <ChevronRight className="h-3 w-3 text-white/40" />
        <span className="text-sm text-white">{route.target_name}</span>
      </div>
    </div>
    <div className="mt-2 flex items-center gap-4 text-xs text-white/60">
      <span>{formatDistance(route.distance_km)}</span>
      <span>{formatTime(route.estimated_time)}</span>
      {route.danger_level > 0 && (
        <span className="text-amber-400">Risk: {(route.danger_level * 100).toFixed(0)}%</span>
      )}
    </div>
  </div>
);

const RouteDetails = ({ route }: { route: RouteOptimizationResult }) => (
  <div className="rounded-xl border border-white/10 bg-black/40 p-4">
    <h4 className="mb-4 flex items-center gap-2 font-bold text-white">
      <Navigation className="h-5 w-5 text-cyan-400" />
      Optimal Route
    </h4>
    <div className="space-y-2">
      {route.path_details.map((hop, idx) => (
        <div key={idx} className="flex items-center gap-3">
          <div className={cn(
            "flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold",
            idx === 0 ? "bg-green-500/20 text-green-400" : idx === route.path_details.length - 1 ? "bg-red-500/20 text-red-400" : "bg-cyan-500/20 text-cyan-400"
          )}>
            {idx + 1}
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-white">{hop.hospital_name}</p>
            <p className="text-xs text-white/60">{hop.district} • {hop.available_beds} beds</p>
          </div>
          {idx < route.path_details.length - 1 && (
            <div className="h-8 w-px bg-white/20" />
          )}
        </div>
      ))}
    </div>
    <div className="mt-4 flex items-center justify-between border-t border-white/10 pt-4">
      <div className="flex items-center gap-4 text-sm text-white/60">
        <span className="flex items-center gap-1">
          <Route className="h-4 w-4" />
          {formatDistance(route.total_distance_km)}
        </span>
        <span className="flex items-center gap-1">
          <Clock className="h-4 w-4" />
          {formatTime(route.total_time_minutes)}
        </span>
        <span className="flex items-center gap-1">
          <Shield className="h-4 w-4" />
          Safety: {((1 - route.max_danger_level) * 100).toFixed(0)}%
        </span>
        {(route.blocked_segments ?? 0) > 0 && (
          <span className="flex items-center gap-1 text-red-400">
            <AlertTriangle className="h-4 w-4" />
            {route.blocked_segments} blocked segment{route.blocked_segments === 1 ? "" : "s"}
          </span>
        )}
      </div>
    </div>
  </div>
);

const AlternativeRoutes = ({ routes }: { routes: RouteOptimizationResult[] }) => {
  if (!routes.length) return null;

  return (
    <div className="mt-4 grid gap-2 lg:grid-cols-3">
      {routes.map((route) => (
        <div key={`${route.strategy}-${route.path.join("-")}`} className="rounded-lg border border-white/10 bg-black/30 p-3">
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-semibold capitalize text-white">{route.strategy}</span>
            <span className={cn("rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase", (route.blocked_segments ?? 0) > 0 ? "border-red-400/40 text-red-400" : "border-green-400/40 text-green-400")}>
              {(route.blocked_segments ?? 0) > 0 ? "Affected" : "Open"}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-3 text-xs text-white/60">
            <span>{formatDistance(route.total_distance_km)}</span>
            <span>{formatTime(route.total_time_minutes)}</span>
            <span>{route.num_hops} hops</span>
          </div>
          <p className="mt-2 line-clamp-2 text-xs text-white/70">
            {route.path_details.map((item) => item.hospital_name).join(" -> ")}
          </p>
        </div>
      ))}
    </div>
  );
};

export function HospitalNetworkView() {
  const [hospitals, setHospitals] = useState<HospitalType[]>([]);
  const [routes, setRoutes] = useState<RouteType[]>([]);
  const [alerts, setAlerts] = useState<DisasterAlert[]>([]);
  const [summary, setSummary] = useState<NetworkSummary | null>(null);
  const [selectedHospital, setSelectedHospital] = useState<HospitalType | null>(null);
  const [selectedRoute, setSelectedRoute] = useState<RouteType | null>(null);
  const [optimizedRoute, setOptimizedRoute] = useState<RouteOptimizationResult | null>(null);
  const [alternativeRoutes, setAlternativeRoutes] = useState<RouteOptimizationResult[]>([]);
  const [aiAnalysis, setAiAnalysis] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [filterDistrict, setFilterDistrict] = useState<string>("");
  const [sourceHospital, setSourceHospital] = useState<string>("");
  const [targetHospital, setTargetHospital] = useState<string>("");
  const [routeStrategy, setRouteStrategy] = useState<string>("safest");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [hospData, routesData, alertsData, summaryData] = await Promise.all([
        api.getHospitals(),
        api.getRoutes(),
        api.getAlerts({ active_only: true }),
        api.getNetworkSummary(),
      ]);
      setHospitals(hospData.hospitals);
      setRoutes(routesData.routes);
      setAlerts(alertsData.alerts);
      setSummary(summaryData);
    } catch (err) {
      console.error("Failed to load hospital network:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const calculateRoute = async () => {
    if (!sourceHospital || !targetHospital) return;
    setCalculating(true);
    try {
      await api.recalculateHospitalRoutes();
      const [routeResult, aiResult] = await Promise.all([
        api.optimizeRoute(sourceHospital, targetHospital, routeStrategy),
        api.aiRouteAnalysis(sourceHospital, targetHospital, true),
      ]);
      setOptimizedRoute(routeResult);
      setAiAnalysis(aiResult.analysis);
      setAlternativeRoutes(aiResult.alternatives || []);
      await loadData();
    } catch (err) {
      console.error("Failed to calculate route:", err);
    } finally {
      setCalculating(false);
    }
  };

  const filteredHospitals = filterDistrict
    ? hospitals.filter(h => h.district === filterDistrict)
    : hospitals;

  const districts = [...new Set(hospitals.map(h => h.district))];

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <RefreshCw className="h-8 w-8 animate-spin text-cyan-400" />
          <p className="text-white/60">Loading Karnataka Hospital Network...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 bg-black/40 p-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Karnataka Hospital Network</h1>
          <p className="text-sm text-white/60">Emergency routing and disaster impact analysis</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-black/40 px-3 py-2">
            <Activity className="h-4 w-4 text-green-400" />
            <span className="text-sm text-white">{summary?.total_hospitals || 0} hospitals</span>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-black/40 px-3 py-2">
            <Route className="h-4 w-4 text-cyan-400" />
            <span className="text-sm text-white">{summary?.total_routes || 0} routes</span>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
            <AlertTriangle className="h-4 w-4 text-red-400" />
            <span className="text-sm text-red-400">{summary?.active_alerts || 0} alerts</span>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            <span className="text-sm text-amber-400">{summary?.blocked_routes || 0} blocked</span>
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel - Hospital List */}
        <div className="w-80 border-r border-white/10 bg-black/20 p-4">
          <div className="mb-4 flex items-center gap-2">
            <Search className="h-4 w-4 text-white/40" />
            <select
              value={filterDistrict}
              onChange={(e) => setFilterDistrict(e.target.value)}
              className="flex-1 rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white"
            >
              <option value="">All Districts</option>
              {districts.map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
          <div className="space-y-2 overflow-y-auto">
            {filteredHospitals.map(h => (
              <HospitalCard
                key={h.hospital_id}
                hospital={h}
                onClick={() => setSelectedHospital(h)}
                isSelected={selectedHospital?.hospital_id === h.hospital_id}
              />
            ))}
          </div>
        </div>

        {/* Center - Map/Routes Visualization */}
        <div className="flex-1 overflow-y-auto p-4">
          {/* Route Calculator */}
          <div className="mb-6 rounded-xl border border-white/10 bg-black/40 p-4">
            <h3 className="mb-4 font-bold text-white">Calculate Emergency Route</h3>
            <div className="flex flex-wrap items-end gap-4">
              <div className="flex-1 min-w-[200px]">
                <label className="mb-1 block text-xs text-white/60">Source Hospital</label>
                <select
                  value={sourceHospital}
                  onChange={(e) => setSourceHospital(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white"
                >
                  <option value="">Select source...</option>
                  {hospitals.map(h => (
                    <option key={h.hospital_id} value={h.hospital_id}>{h.hospital_name}</option>
                  ))}
                </select>
              </div>
              <div className="flex-1 min-w-[200px]">
                <label className="mb-1 block text-xs text-white/60">Target Hospital</label>
                <select
                  value={targetHospital}
                  onChange={(e) => setTargetHospital(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white"
                >
                  <option value="">Select target...</option>
                  {hospitals.map(h => (
                    <option key={h.hospital_id} value={h.hospital_id}>{h.hospital_name}</option>
                  ))}
                </select>
              </div>
              <div className="w-32">
                <label className="mb-1 block text-xs text-white/60">Strategy</label>
                <select
                  value={routeStrategy}
                  onChange={(e) => setRouteStrategy(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white"
                >
                  <option value="shortest">Shortest</option>
                  <option value="fastest">Fastest</option>
                  <option value="safest">Safest</option>
                </select>
              </div>
              <button
                onClick={calculateRoute}
                disabled={!sourceHospital || !targetHospital || calculating}
                className="flex items-center gap-2 rounded-lg bg-cyan-500 px-4 py-2 font-bold text-black transition-all hover:bg-cyan-400 disabled:opacity-50"
              >
                {calculating ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Navigation className="h-4 w-4" />}
                {calculating ? "Calculating..." : "Find Route"}
              </button>
            </div>
          </div>

          {/* Route Results */}
          {optimizedRoute && (
            <div className="mb-6">
              <RouteDetails route={optimizedRoute} />
              {aiAnalysis && (
                <div className="mt-4 rounded-xl border border-white/10 bg-black/40 p-4">
                  <h4 className="mb-2 flex items-center gap-2 font-bold text-white">
                    <Zap className="h-5 w-5 text-amber-400" />
                    AI Alternate Route Suggestions
                  </h4>
                  <p className="text-sm text-white/80">{aiAnalysis}</p>
                  <AlternativeRoutes routes={alternativeRoutes} />
                </div>
              )}
            </div>
          )}

          {/* Routes List */}
          <h3 className="mb-4 font-bold text-white">Network Routes</h3>
          <div className="grid gap-2">
            {routes.filter(r => !filterDistrict || r.source_district === filterDistrict || r.target_district === filterDistrict).slice(0, 20).map((route, idx) => (
              <RouteCard
                key={idx}
                route={route}
                onClick={() => setSelectedRoute(route)}
                isSelected={selectedRoute?.source_id === route.source_id && selectedRoute?.target_id === route.target_id}
              />
            ))}
          </div>
        </div>

        {/* Right Panel - Alerts */}
        <div className="w-72 border-l border-white/10 bg-black/20 p-4">
          <h3 className="mb-4 flex items-center gap-2 font-bold text-white">
            <Siren className="h-5 w-5 text-red-400" />
            Active Alerts ({alerts.length})
          </h3>
          <div className="space-y-2 overflow-y-auto">
            {alerts.map(alert => (
              <AlertCard key={alert.alert_id} alert={alert} />
            ))}
          </div>

          {summary && (
            <div className="mt-6">
              <h3 className="mb-4 font-bold text-white">Network Stats</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-white/60">Total Beds</span>
                  <span className="text-white">{summary.total_available_beds}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/60">O2 Available</span>
                  <span className="text-green-400">{summary.hospitals_with_oxygen}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/60">Occupancy</span>
                  <span className="text-amber-400">{summary.beds_occupancy_pct}%</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default HospitalNetworkView;
