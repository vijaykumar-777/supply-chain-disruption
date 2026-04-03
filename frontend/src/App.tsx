import React, { useState } from "react";
import { 
  Bell, 
  Search, 
  LayoutDashboard, 
  Globe, 
  Activity, 
  BarChart3, 
  Bot, 
  Settings, 
  HelpCircle 
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { SidebarItem } from "./components/layout/SidebarItem";
import { DashboardView } from "./components/dashboard/DashboardView";

// Placeholder imports for other views to be extracted
import { LIVE_EVENTS, LOGISTICS_VOLUME_DATA } from "./constants/mockData";
import { GlobalMapView } from "./components/dashboard/GlobalMapView";

const LiveFeedView = () => <div className="p-10 text-on-surface-variant font-bold">Live Feed View (Extracted soon)</div>;
const AnalyticsView = () => <div className="p-10 text-on-surface-variant font-bold">Analytics View (Extracted soon)</div>;
const AIAssistantView = () => <div className="p-10 text-on-surface-variant font-bold">AI Assistant View (Extracted soon)</div>;

import { View } from "./types";
import { cn } from "./lib/utils";

export default function App() {
  const [activeView, setActiveView] = useState<View>("dashboard");

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Top Bar */}
      <header className="fixed top-0 w-full z-50 flex justify-between items-center px-6 h-16 glass-elevated border-b border-primary/10">
        <div className="flex items-center gap-8">
          <span className="text-2xl font-black tracking-tighter text-primary">ATLAS AI</span>
          <div className="hidden md:flex items-center bg-white/5 rounded-full px-4 py-1.5 border border-white/10">
            <Search className="w-4 h-4 text-on-surface-variant mr-2" />
            <input className="bg-transparent border-none focus:ring-0 text-sm w-64 text-on-surface placeholder:text-on-surface-variant/50 outline-none" placeholder="Search supply chain nodes..." />
          </div>
        </div>
        <div className="flex items-center gap-4">
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
          <SidebarItem icon={Globe} label="Global Map" active={activeView === "global-map"} onClick={() => setActiveView("global-map")} />
          <SidebarItem icon={Activity} label="Live Feed" active={activeView === "live-feed"} onClick={() => setActiveView("live-feed")} />
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
              key={activeView}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="h-full"
            >
              {activeView === "dashboard" && <DashboardView />}
              {activeView === "global-map" && <GlobalMapView />}
              {activeView === "live-feed" && <LiveFeedView />}
              {activeView === "analytics" && <AnalyticsView />}
              {activeView === "ai-assistant" && <AIAssistantView />}
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
              Predicted disruptions in next 48h: Port of Long Beach congestion expected to increase by 15% due to labor negotiations.
            </p>
          </div>
          <button 
            onClick={() => setActiveView("ai-assistant")}
            className="h-14 w-14 rounded-full bg-primary text-background flex items-center justify-center shadow-2xl shadow-primary/30 active:scale-90 transition-transform relative"
          >
            <Bot className="w-8 h-8" />
            <div className="absolute -top-1 -right-1 h-5 w-5 bg-error text-[10px] font-bold rounded-full flex items-center justify-center border-2 border-background text-white">1</div>
          </button>
        </div>
      )}
    </div>
  );
}
