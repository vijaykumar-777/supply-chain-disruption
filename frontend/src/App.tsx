import React, { useEffect, useState, lazy, Suspense } from "react";
import {
  Bell,
  Search,
  LayoutDashboard,
  Route,
  Globe,
  Activity,
  BarChart3,
  Bot,
  Siren,
  Settings,
  HelpCircle,
  Hospital
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { SidebarItem } from "./components/layout/SidebarItem";
import { DashboardView } from "./components/dashboard/DashboardView";
import { api, AppMode } from "./services/api";

// Fix #11: Lazy-load heavy views to reduce initial bundle size
const GlobalMapView = lazy(() => import("./components/dashboard/GlobalMapView").then(m => ({ default: m.GlobalMapView })));
const AIAssistantView = lazy(() => import("./components/ai/AIAssistantView").then(m => ({ default: m.AIAssistantView })));
const SupplyChainMonitorView = lazy(() => import("./components/monitor/SupplyChainMonitorView").then(m => ({ default: m.SupplyChainMonitorView })));
const HospitalNetworkView = lazy(() => import("./components/hospital/HospitalNetworkView").then(m => ({ default: m.HospitalNetworkView })));

import { LiveFeedView } from "./components/feed/LiveFeedView";
import { AnalyticsView } from "./components/analytics/AnalyticsView";
import { LiveDisastersView } from "./components/disasters/LiveDisastersView";

import { View } from "./types";
import { cn } from "./lib/utils";

export default function App() {
  const [activeView, setActiveView] = useState<View>("dashboard");
  const [mode, setMode] = useState<AppMode>("live");
  const [modeLoading, setModeLoading] = useState(true);
  const [modeVersion, setModeVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    api.getMode()
      .then((data) => {
        if (!cancelled) {
          setMode(data.mode);
        }
      })
      .catch((error) => console.warn("Failed to load app mode", error))
      .finally(() => {
        if (!cancelled) {
          setModeLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const changeMode = async (nextMode: AppMode) => {
    if (nextMode === mode || modeLoading) return;
    setModeLoading(true);
    try {
      const data = await api.setMode(nextMode);
      setMode(data.mode);
      setModeVersion((version) => version + 1);
    } finally {
      setModeLoading(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Top Bar */}
      <header className="fixed top-0 w-full z-50 flex justify-between items-center px-6 h-16 glass-elevated border-b border-primary/10">
        <div className="flex items-center gap-8">
          <span className="text-2xl font-black tracking-tighter text-primary">ReliefRoute KA</span>
          <div className="hidden md:flex items-center bg-white/5 rounded-full px-4 py-1.5 border border-white/10">
            <Search className="w-4 h-4 text-on-surface-variant mr-2" />
            <input className="bg-transparent border-none focus:ring-0 text-sm w-64 text-on-surface placeholder:text-on-surface-variant/50 outline-none" placeholder="Search hubs, roads, villages..." />
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center rounded-full border border-white/10 bg-white/5 p-1">
            {(["live", "demo"] as AppMode[]).map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => void changeMode(item)}
                disabled={modeLoading}
                className={cn(
                  "rounded-full px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-[0.12em] transition-colors disabled:opacity-50 md:px-3 md:text-[11px] md:tracking-[0.16em]",
                  mode === item ? "bg-primary text-background" : "text-on-surface-variant hover:text-on-surface"
                )}
                title={item === "live" ? "Use only live Neo4j/weather data" : "Use only the built-in Karnataka demo scenario"}
              >
                {item}
              </button>
            ))}
          </div>
          <button className="p-2 rounded-full hover:bg-primary/10 transition-colors">
            <Bell className="w-5 h-5 text-on-surface-variant" />
          </button>
          <div className="h-8 w-8 rounded-full overflow-hidden border border-primary/20 cursor-pointer">
            <img className="h-full w-full object-cover" src="https://picsum.photos/seed/user/100/100" />
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <aside className="fixed left-0 top-16 h-[calc(100vh-64px)] w-64 z-40 glass-elevated border-r border-primary/10 hidden md:flex flex-col justify-between">
        <nav className="py-6 flex flex-col">
          <SidebarItem icon={LayoutDashboard} label="Dashboard" active={activeView === "dashboard"} onClick={() => setActiveView("dashboard")} />
          <SidebarItem icon={Hospital} label="Hospitals" active={activeView === "hospital-network"} onClick={() => setActiveView("hospital-network")} />
          <SidebarItem icon={Route} label="Road Network" active={activeView === "monitor"} onClick={() => setActiveView("monitor")} />
          <SidebarItem icon={Globe} label="Karnataka Map" active={activeView === "global-map"} onClick={() => setActiveView("global-map")} />
          <SidebarItem icon={Siren} label="Live Disasters" active={activeView === "live-disasters"} onClick={() => setActiveView("live-disasters")} />
          <SidebarItem icon={Activity} label="Weather Feed" active={activeView === "live-feed"} onClick={() => setActiveView("live-feed")} />
          <SidebarItem icon={BarChart3} label="Analytics" active={activeView === "analytics"} onClick={() => setActiveView("analytics")} />
          <SidebarItem icon={Bot} label="AI Assistant" active={activeView === "ai-assistant"} onClick={() => setActiveView("ai-assistant")} />
        </nav>
        <div className="pb-8 flex flex-col border-t border-white/5 pt-4">
          <SidebarItem icon={Settings} label="Settings" onClick={() => {}} />
          <SidebarItem icon={HelpCircle} label="Support" onClick={() => {}} />
        </div>
      </aside>

      {/* Main Content */}
      <main className="md:ml-64 mt-16 flex-1 h-[calc(100vh-64px)] overflow-y-auto bg-background no-scrollbar">
        <div className={cn("max-w-[1600px] mx-auto p-6 h-full", activeView === "ai-assistant" && "p-0")}>
          <AnimatePresence mode="wait">
            <motion.div
              key={`${activeView}-${modeVersion}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="h-full"
            >
              <Suspense fallback={<div className="flex items-center justify-center h-full text-on-surface-variant">Loading...</div>}>
              {activeView === "dashboard" && <DashboardView />}
              {activeView === "hospital-network" && <HospitalNetworkView />}
              {activeView === "monitor" && <SupplyChainMonitorView />}
              {activeView === "global-map" && <GlobalMapView />}
              {activeView === "live-disasters" && <LiveDisastersView />}
              {activeView === "live-feed" && <LiveFeedView />}
              {activeView === "analytics" && <AnalyticsView />}
              {activeView === "ai-assistant" && <AIAssistantView />}
              </Suspense>
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      {/* Floating AI Bubble (only on dashboard) */}
      {activeView === "dashboard" && (
        <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3 group">
          <div className="max-w-xs glass-elevated p-4 rounded-2xl rounded-br-none border border-primary/30 shadow-2xl transition-all duration-300 translate-y-2 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto">
            <div className="flex items-center gap-2 mb-2">
              <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-primary">AI Insights</span>
            </div>
            <p className="text-xs text-on-surface-variant">
              Open the AI Assistant to analyze relief routes, simulate blocked-road impact, and request grounded response actions from your local model.
            </p>
          </div>
          <button 
            onClick={() => setActiveView("ai-assistant")}
            className="h-14 w-14 rounded-full bg-primary text-background flex items-center justify-center shadow-2xl shadow-primary/30 active:scale-90 transition-transform relative"
          >
            <Bot className="w-8 h-8" />
          </button>
        </div>
      )}
    </div>
  );
}
