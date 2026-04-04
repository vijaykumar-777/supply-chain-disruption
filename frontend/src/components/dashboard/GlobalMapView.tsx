import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { api, APIEvent, APINode, APILink, DataSource } from '../../services/api';

const SEVERITY_COLOR = (type: string) =>
  type === 'critical' ? '#ff3366' : type === 'warning' ? '#ffaa00' : '#00dd99';

export const GlobalMapView = () => {
  const [events, setEvents] = useState<APIEvent[]>([]);
  const [nodes, setNodes] = useState<APINode[]>([]);
  const [links, setLinks] = useState<APILink[]>([]);
  const [loading, setLoading] = useState(true);

  const [dataSource, setDataSource] = useState<DataSource | null>(null);  // Fix #10

  useEffect(() => {
    (async () => {
      try {
        const [evRes, nodeRes] = await Promise.all([api.getEvents(), api.getGraphNodes()]);
        setEvents(evRes.events);
        setNodes(nodeRes.nodes);
        setLinks(nodeRes.links || []);
        setDataSource(nodeRes.source ?? evRes.source ?? null);  // Fix #10
      } catch (e) {
        console.warn("Failed to fetch map data from API:", e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // Nodes that have lat/lon coordinates from Neo4j
  const geoNodes = nodes.filter(n => n.lat != null && n.lon != null);

  return (
    <div className="h-full w-full flex flex-col gap-4">
      <div className="flex justify-between items-center mb-2">
        <div>
          <h2 className="text-2xl font-bold text-on-surface">Global Supply Chain Network</h2>
          <p className="text-on-surface-variant text-sm">
            {loading ? "Loading live data..." : `${geoNodes.length} nodes · ${links.length} trade routes · ${events.length} active disruptions — ${dataSource === "live" ? "Live from Neo4j" : "Neo4j unavailable"}`}
          </p>
        </div>
      </div>

      <div className="flex-1 w-full rounded-2xl overflow-hidden glass-elevated border border-primary/20 relative">
        <MapContainer
          center={[20, 0]}
          zoom={2}
          className="h-full w-full"
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />

          {/* ── Supply Chain Links (Edges) ── */}
          {links.map((link, idx) => {
            const sourceNode = geoNodes.find(n => n.id === link.source_id);
            const targetNode = geoNodes.find(n => n.id === link.target_id);
            if (!sourceNode || !targetNode) return null;
            return (
              <Polyline
                key={`link-${idx}`}
                positions={[[sourceNode.lat!, sourceNode.lon!], [targetNode.lat!, targetNode.lon!]]}
                color="#7dd3fc"
                weight={1.5}
                opacity={0.3}
                dashArray={link.rel_type === "TRADE_ROUTE" ? "5, 5" : undefined}
              />
            );
          })}

          {/* ── Supply Chain Nodes (real lat/lon) ── */}
          {geoNodes.map(node => {
            const isCompany = node.labels.includes("Company");
            const nodeColor = isCompany ? "#c084fc" : "#7dd3fc"; // Purple for company, blue for location
            
            return (
              <CircleMarker
                key={node.id}
                center={[node.lat!, node.lon!]}
                radius={isCompany ? 6 : 8}
                fillColor={nodeColor}
                color={nodeColor}
                fillOpacity={isCompany ? 0.8 : 0.5}
                weight={isCompany ? 2 : 1}
              >
                <Tooltip permanent={false} direction="top">
                  <span className="text-xs font-bold">{node.name}</span>
                </Tooltip>
                <Popup>
                  <div className="space-y-1 text-sm bg-surface p-1">
                    <div className="font-bold text-lg text-primary">{node.name}</div>
                    <div className="text-xs font-mono bg-on-surface/5 p-1 rounded inline-block">{node.labels.join(', ')}</div>
                    {node.country && <div className="text-xs mt-1">🌍 {node.country}</div>}
                    {isCompany && <div className="text-xs mt-1 text-tertiary">🏢 Entity</div>}
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}

          {/* ── Disruption Events (linked to location coords) ── */}
          {events.map(event => {
            // Find a node matching one of this event's locations
            const matchNode = geoNodes.find(n =>
              event.locations.some(loc => loc.toLowerCase().includes(n.name.toLowerCase()) || n.name.toLowerCase().includes(loc.toLowerCase()))
            );
            if (!matchNode) return null;
            return (
              <CircleMarker
                key={event.id}
                center={[matchNode.lat!, matchNode.lon!]}
                radius={event.type === 'critical' ? 22 : event.type === 'warning' ? 16 : 10}
                fillColor={SEVERITY_COLOR(event.type)}
                color="transparent"
                fillOpacity={0.35}
              >
                <CircleMarker
                  center={[matchNode.lat!, matchNode.lon!]}
                  radius={5}
                  fillColor={SEVERITY_COLOR(event.type)}
                  color="transparent"
                  fillOpacity={0.9}
                >
                  <Popup>
                    <div className="space-y-1 min-w-[200px]">
                      <div className="font-bold text-sm">{event.title}</div>
                      <div className="text-xs text-gray-500">{event.category}</div>
                      <div className="text-xs">Severity: <strong>{(event.severity * 100).toFixed(0)}%</strong></div>
                      <div className="text-xs text-gray-500">{event.description}</div>
                    </div>
                  </Popup>
                </CircleMarker>
              </CircleMarker>
            );
          })}
        </MapContainer>

        {!loading && geoNodes.length === 0 && (
          <div className="absolute inset-0 z-[900] flex items-center justify-center bg-background/55 backdrop-blur-sm">
            <div className="max-w-md rounded-2xl border border-white/10 bg-surface/90 p-5 text-center">
              <p className="text-lg font-semibold text-on-surface">No live graph data available</p>
              <p className="mt-2 text-sm text-on-surface-variant">
                Import real supply chain routes into Neo4j to populate the global map with nodes and disruption overlays.
              </p>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="absolute bottom-6 right-6 z-[1000] glass p-4 rounded-xl border border-white/10 shadow-2xl space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-2">Legend</h4>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#c084fc]/90 border border-[#c084fc]" /><span className="text-xs text-on-surface">Company Node</span></div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#7dd3fc]/50 border border-[#7dd3fc]" /><span className="text-xs text-on-surface">Location Node</span></div>
          <div className="flex items-center gap-2">
            <div className="w-3 border-t-2 border-[#7dd3fc]/40" /><span className="text-xs text-on-surface">Trade Route</span>
          </div>
          <div className="h-[1px] w-full bg-white/10 my-1"></div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#ff3366]/70" /><span className="text-xs text-on-surface">Critical Disruption</span></div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#ffaa00]/70" /><span className="text-xs text-on-surface">Warning</span></div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#00dd99]/70" /><span className="text-xs text-on-surface">Low Impact</span></div>
        </div>
      </div>
    </div>
  );
};
