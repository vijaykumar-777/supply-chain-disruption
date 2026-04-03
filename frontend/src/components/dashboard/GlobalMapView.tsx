import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { api, APIEvent, APINode, DataSource } from '../../services/api';

const SEVERITY_COLOR = (type: string) =>
  type === 'critical' ? '#ff3366' : type === 'warning' ? '#ffaa00' : '#00dd99';

export const GlobalMapView = () => {
  const [events, setEvents] = useState<APIEvent[]>([]);
  const [nodes, setNodes] = useState<APINode[]>([]);
  const [loading, setLoading] = useState(true);

  const [dataSource, setDataSource] = useState<DataSource | null>(null);  // Fix #10

  useEffect(() => {
    (async () => {
      try {
        const [evRes, nodeRes] = await Promise.all([api.getEvents(), api.getGraphNodes()]);
        setEvents(evRes.events);
        setNodes(nodeRes.nodes);
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
            {loading ? "Loading live data..." : `${nodes.length} nodes · ${events.length} active disruptions — ${dataSource === "live" ? "Live from Neo4j" : "Demo data — Neo4j unavailable"}`}
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

          {/* ── Supply Chain Nodes (real lat/lon) ── */}
          {geoNodes.map(node => (
            <CircleMarker
              key={node.id}
              center={[node.lat!, node.lon!]}
              radius={8}
              fillColor="#7dd3fc"
              color="#7dd3fc"
              fillOpacity={0.5}
              weight={1}
            >
              <Tooltip permanent={false} direction="top">
                <span className="text-xs font-bold">{node.name}</span>
              </Tooltip>
              <Popup>
                <div className="space-y-1 text-sm">
                  <div className="font-bold">{node.name}</div>
                  <div className="text-xs text-gray-500">{node.labels.join(', ')}</div>
                  {node.country && <div className="text-xs">🌍 {node.country}</div>}
                </div>
              </Popup>
            </CircleMarker>
          ))}

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

        {/* Legend */}
        <div className="absolute bottom-6 right-6 z-[1000] glass p-4 rounded-xl border border-white/10 shadow-2xl space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-2">Legend</h4>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#7dd3fc]/70" /><span className="text-xs text-on-surface">Supply Chain Node</span></div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#ff3366]/70" /><span className="text-xs text-on-surface">Critical Disruption</span></div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#ffaa00]/70" /><span className="text-xs text-on-surface">Warning</span></div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#00dd99]/70" /><span className="text-xs text-on-surface">Low Impact</span></div>
        </div>
      </div>
    </div>
  );
};
