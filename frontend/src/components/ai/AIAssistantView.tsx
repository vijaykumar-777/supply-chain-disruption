import React, { useEffect, useMemo, useState } from "react";
import { useEvents, useGraphNodes, useSimulation, useRecommendation, useFeedback } from "../../hooks/useAtlasData";
import { Bot, Play, ChevronRight, CheckCircle, ThumbsUp, ThumbsDown, MessageSquare, AlertTriangle, ArrowRight, RefreshCw } from "lucide-react";
import { cn } from "../../lib/utils";

export const AIAssistantView = () => {
  const { events, loading: eventsLoading } = useEvents(30000);
  const { nodes, loading: nodesLoading, source: nodesSource } = useGraphNodes(30000);
  const simul = useSimulation();
  const recomm = useRecommendation();
  const feedb = useFeedback();

  const [step, setStep] = useState(1);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [sourceNode, setSourceNode] = useState("");
  const [targetNode, setTargetNode] = useState("");

  const selectedEvent = events.find(e => e.id === selectedEventId);
  const routeNodes = useMemo(
    () => nodes.filter(node => !node.labels.includes("Event")),
    [nodes]
  );

  useEffect(() => {
    if (routeNodes.length === 0) return;

    const ids = new Set(routeNodes.map(node => node.id));
    const preferredSource =
      routeNodes.find(node => node.id === "PORT_SHANGHAI")?.id ??
      routeNodes.find(node => node.id === "NODE_LOC_SHANGHAI")?.id ??
      routeNodes[0]?.id ??
      "";
    const preferredTarget =
      routeNodes.find(node => node.id === "PORT_LA")?.id ??
      routeNodes.find(node => node.id === "NODE_LOC_LOS_ANGELES")?.id ??
      routeNodes.find(node => node.id !== preferredSource)?.id ??
      routeNodes[0]?.id ??
      "";

    if (!sourceNode || !ids.has(sourceNode)) {
      setSourceNode(preferredSource);
    }

    if (!targetNode || !ids.has(targetNode) || targetNode === preferredSource) {
      setTargetNode(preferredTarget);
    }
  }, [routeNodes, sourceNode, targetNode]);

  // Extract simulation display data from either flat or nested structure
  const getSimData = () => {
    if (!simul.result) return null;
    const r = simul.result as any;
    return {
      baseDuration: r.base_duration ?? r.simulation?.mean_days ?? 0,
      meanDelay: r.mean_delay ?? (r.simulation?.mean_days ? r.simulation.mean_days - (r.base_duration ?? 0) : 0),
      p95Delay: r.p95_delay ?? r.simulation?.p95_days ?? 0,
      riskScore: r.risk_score ?? (r.simulation?.max_risk_days ? Math.min(r.simulation.max_risk_days / 30, 1) : 0.5),
    };
  };

  const handleRunSimulation = async () => {
    if (!selectedEvent) return;
    if (!sourceNode || !targetNode) return;
    setStep(2);
    const res = await simul.run(sourceNode, targetNode, selectedEvent.locations);
    if (res) setStep(3);
  };

  const handleGetRecommendation = async () => {
    if (!selectedEvent || !simul.result) return;
    setStep(4);
    // Fix #6: Pass actual alternative_route from simulation result
    const altRoute = (simul.result as any).alternative_route ?? [];
    const res = await recomm.run(
      selectedEvent.title,
      selectedEvent.category,
      selectedEvent.locations,
      simul.result,
      altRoute
    );
    if (res) setStep(5);
  };

  const handleSubmitFeedback = async (rating: number) => {
    if (!recomm.result) return;
    await feedb.submit(recomm.result.recommendation_id, rating);
  };

  const handleReset = () => {
    setStep(1);
    setSelectedEventId(null);
  };

  const simData = getSimData();

  return (
    <div className="h-full flex flex-col gap-6 max-w-5xl mx-auto w-full p-6 overflow-y-auto no-scrollbar">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center text-primary">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-on-surface">Atlas AI Strategist</h2>
            <p className="text-sm text-on-surface-variant">Llama-3 powered supply chain resolution</p>
          </div>
        </div>
        {step > 1 && (
          <button onClick={handleReset} className="text-xs text-on-surface-variant border border-white/10 px-3 py-1.5 rounded-lg hover:bg-white/5 transition">
            ↺ Start Over
          </button>
        )}
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-between mt-2 mb-2 px-4">
        {[
          { num: 1, label: "Select Disruption" },
          { num: 2, label: "Simulate Impact" },
          { num: 3, label: "Generate Strategy" },
          { num: 4, label: "Review & Rate" }
        ].map((s, i) => (
          <div key={s.num} className="flex flex-col items-center gap-2 relative flex-1">
             <div className={cn("w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold z-10 transition-colors", 
               step > s.num ? "bg-primary text-white" : step === s.num ? "bg-primary text-white ring-4 ring-primary/20" : "bg-surface text-on-surface-variant border border-white/10")}>
               {step > s.num ? <CheckCircle className="w-4 h-4" /> : s.num}
             </div>
             <span className={cn("text-xs uppercase tracking-wider font-semibold", step >= s.num ? "text-primary" : "text-on-surface-variant opacity-50")}>{s.label}</span>
             {i !== 3 && <div className={cn("absolute top-4 left-[50%] right-[-50%] h-[2px]", step > s.num ? "bg-primary" : "bg-white/10")}></div>}
          </div>
        ))}
      </div>

      <div className="flex flex-col gap-6 pb-10">
        {/* STEP 1: Select Event */}
        <div className={cn("glass-elevated p-6 rounded-xl border border-primary/20 transition-all", step > 1 && "opacity-40 grayscale pointer-events-none")}>
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-tertiary" /> Step 1: Target Active Disruption</h3>
          
          {eventsLoading && events.length === 0 ? (
            <div className="text-center p-6 text-on-surface-variant">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
              Loading active events...
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {events.slice(0, 6).map(e => (
                <div 
                  key={e.id} 
                  onClick={() => setSelectedEventId(e.id)}
                  className={cn("p-4 rounded-xl border cursor-pointer transition-all relative", 
                    selectedEventId === e.id ? "bg-primary/20 border-primary shadow-lg shadow-primary/10" : "bg-surface/50 border-white/10 hover:border-primary/50 hover:bg-white/5")}
                >
                  {selectedEventId === e.id && <div className="absolute top-3 right-3 text-primary"><CheckCircle className="w-5 h-5" /></div>}
                  <div className="font-bold text-on-surface pr-8 text-sm">{e.title}</div>
                  <div className="text-xs text-on-surface-variant mt-1">{e.category} • Severity: {(e.severity * 100).toFixed(0)}%</div>
                  <div className="text-xs text-on-surface-variant mt-0.5">{e.locations.join(", ")}</div>
                </div>
              ))}
              {events.length === 0 && <div className="col-span-full text-on-surface-variant p-4 text-center">No active events found. Backend may be starting up.</div>}
            </div>
          )}
          
            <div className="mt-6 flex flex-wrap gap-4 items-end border-t border-white/10 pt-6">
            <div className="flex-1 min-w-[150px]">
              <label className="text-xs text-on-surface-variant uppercase mb-2 block font-semibold">Route Source Node</label>
              <select value={sourceNode} onChange={e => setSourceNode(e.target.value)} className="w-full bg-surface border border-white/10 rounded-lg p-2.5 text-sm focus:border-primary focus:outline-none text-on-surface" disabled={nodesLoading || routeNodes.length === 0}>
                {routeNodes.length === 0 ? (
                  <option value="">{nodesLoading ? "Loading nodes..." : "No nodes available"}</option>
                ) : (
                  routeNodes.map(node => (
                    <option key={node.id} value={node.id}>
                      {node.name} ({node.id})
                    </option>
                  ))
                )}
              </select>
            </div>
            <ArrowRight className="w-5 h-5 text-on-surface-variant mb-3 hidden md:block" />
            <div className="flex-1 min-w-[150px]">
              <label className="text-xs text-on-surface-variant uppercase mb-2 block font-semibold">Route Target Node</label>
              <select value={targetNode} onChange={e => setTargetNode(e.target.value)} className="w-full bg-surface border border-white/10 rounded-lg p-2.5 text-sm focus:border-primary focus:outline-none text-on-surface" disabled={nodesLoading || routeNodes.length === 0}>
                {routeNodes.length === 0 ? (
                  <option value="">{nodesLoading ? "Loading nodes..." : "No nodes available"}</option>
                ) : (
                  routeNodes.map(node => (
                    <option key={node.id} value={node.id}>
                      {node.name} ({node.id})
                    </option>
                  ))
                )}
              </select>
            </div>
            <button 
              disabled={!selectedEventId || !sourceNode || !targetNode || nodesLoading || routeNodes.length === 0}
              onClick={handleRunSimulation}
              className="bg-primary text-white px-6 py-2.5 rounded-lg font-bold flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-primary/80 transition shadow-lg shadow-primary/20"
            >
              Analyze Route Impact <ChevronRight className="w-4 h-4" />
            </button>
          </div>
          {nodesSource === "live" && (
            <div className="mt-3 text-xs text-on-surface-variant">
              Route IDs are loaded from the live supply chain graph, so only valid Neo4j nodes are selectable.
            </div>
          )}
        </div>

        {/* STEP 2: Simulation Results */}
        {step >= 2 && (
          <div className={cn("glass-elevated p-6 rounded-xl border border-primary/20 transition-all", step > 3 && "opacity-40 grayscale pointer-events-none")}>
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2"><Play className="w-5 h-5 text-primary" /> Step 2: Impact Simulation</h3>
            {simul.loading ? (
               <div className="flex gap-4 text-primary p-6 bg-primary/5 rounded-xl border border-primary/20 items-center justify-center">
                 <RefreshCw className="w-6 h-6 animate-spin" /> 
                 <div>
                   <div className="font-bold">Running Monte Carlo simulation...</div>
                   <div className="text-sm opacity-70">Analyzing route from {sourceNode} → {targetNode}</div>
                 </div>
               </div>
            ) : simData ? (
               <div className="bg-surface/50 border border-white/10 rounded-xl p-5">
                 <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                   <div><div className="text-xs text-on-surface-variant uppercase tracking-wider font-semibold">Base Duration</div><div className="text-xl font-bold text-on-surface mt-1">{simData.baseDuration.toFixed(1)} days</div></div>
                   <div><div className="text-xs text-on-surface-variant uppercase tracking-wider font-semibold">Mean Delay</div><div className="text-xl font-bold text-error mt-1">+{simData.meanDelay.toFixed(1)} days</div></div>
                   <div><div className="text-xs text-on-surface-variant uppercase tracking-wider font-semibold">P95 Delay (Worst)</div><div className="text-xl font-bold text-error mt-1">+{simData.p95Delay.toFixed(1)} days</div></div>
                   <div><div className="text-xs text-on-surface-variant uppercase tracking-wider font-semibold">Risk Score</div><div className="text-xl font-bold text-tertiary mt-1">{(simData.riskScore * 100).toFixed(0)}%</div></div>
                 </div>
                 {step === 3 && (
                   <div className="mt-6 border-t border-white/10 pt-6 flex justify-end">
                     <button onClick={handleGetRecommendation} className="bg-primary text-white px-6 py-2.5 rounded-lg font-bold flex items-center gap-2 hover:bg-primary/80 transition shadow-lg shadow-primary/20">
                       Generate AI Mitigation Strategy <Bot className="w-4 h-4" />
                     </button>
                   </div>
                 )}
               </div>
            ) : simul.error ? (
               <div className="text-error bg-error/10 p-4 rounded-lg border border-error/20 flex gap-2"><AlertTriangle className="w-5 h-5"/> Error: {simul.error}</div>
            ) : null}
          </div>
        )}

        {/* STEP 3 & 4: AI Recommendation */}
        {step >= 4 && (
          <div className="glass-elevated p-6 rounded-xl border border-primary/50 shadow-[0_0_30px_rgba(59,130,246,0.15)] bg-gradient-to-br from-surface to-primary/5">
             <h3 className="text-xl font-bold mb-4 flex items-center gap-2"><Bot className="w-6 h-6 text-primary" /> Step 3: AI Mitigation Strategy</h3>
             {recomm.loading ? (
                <div className="flex flex-col gap-3 text-primary p-6 bg-primary/5 rounded-xl border border-primary/20 items-center justify-center">
                  <Bot className="w-10 h-10 animate-bounce" />
                  <div className="font-bold">Llama-3 is analyzing the supply chain network...</div>
                  <div className="text-sm opacity-70">Synthesizing alternatives for {targetNode}</div>
                </div>
             ) : recomm.result ? (
                <div className="flex flex-col gap-6">
                  <div className="p-6 bg-surface/80 rounded-xl border border-primary/20 text-on-surface max-w-none text-sm md:text-base leading-relaxed whitespace-pre-wrap">
                     {recomm.result.recommendation}
                  </div>
                  
                  {/* STEP 4: Feedback */}
                  <div className="border-t border-white/10 pt-6 mt-2">
                    <h4 className="text-sm font-bold text-on-surface-variant uppercase tracking-wider mb-4 flex items-center gap-2">
                      <MessageSquare className="w-4 h-4" /> Rate this Recommendation
                    </h4>
                    {feedb.success ? (
                       <div className="bg-success/20 text-success border border-success/30 p-4 rounded-lg flex items-center gap-3 font-bold">
                         <CheckCircle className="w-5 h-5" /> Feedback saved. Thank you!
                       </div>
                    ) : (
                       <div className="flex gap-4">
                         <button onClick={() => handleSubmitFeedback(1)} className="flex-1 py-3 px-4 bg-surface/50 hover:bg-primary/20 border border-white/10 hover:border-primary/50 rounded-xl transition flex justify-center items-center gap-2 text-primary font-bold">
                           <ThumbsUp className="w-5 h-5" /> Helpful
                         </button>
                         <button onClick={() => handleSubmitFeedback(-1)} className="flex-1 py-3 px-4 bg-surface/50 hover:bg-error/20 border border-white/10 hover:border-error/50 rounded-xl transition flex justify-center items-center gap-2 text-error font-bold">
                           <ThumbsDown className="w-5 h-5" /> Not Useful
                         </button>
                       </div>
                    )}
                  </div>
                </div>
             ) : recomm.error ? (
                <div className="text-error bg-error/10 p-4 rounded-lg border border-error/20 flex gap-2"><AlertTriangle className="w-5 h-5"/> Error: {recomm.error}</div>
             ) : null}
          </div>
        )}
      </div>
    </div>
  );
};
