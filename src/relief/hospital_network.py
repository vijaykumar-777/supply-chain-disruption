"""
Hospital network service for Karnataka emergency supply routing.

The service owns three linked concerns:
- loading the synthetic hospital roster
- maintaining a connected hospital-to-hospital route graph
- recalculating route risk whenever active disaster alerts are present
"""
import csv
import heapq
import json
import logging
import math
import pickle
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
HOSPITALS_PATH = DATA_DIR / "hospitals.csv"
GRAPH_PATH = DATA_DIR / "hospital_graph.pkl"
ALERTS_PATH = DATA_DIR / "disaster_alerts.json"


class HospitalNetworkService:
    """Hospital network operations and route optimization."""

    def __init__(self):
        self.base_graph: Optional[nx.Graph] = None
        self.graph: Optional[nx.Graph] = None
        self.hospitals: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        """Load hospitals, graph, and alerts from disk."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.hospitals = self._load_hospitals()
        self.alerts = self._load_alerts()
        self.base_graph = self._load_or_build_graph()
        self.recalculate_route_impacts(persist=False)

    def _load_hospitals(self) -> List[Dict[str, Any]]:
        if not HOSPITALS_PATH.exists():
            logger.warning("Hospital data file is missing: %s", HOSPITALS_PATH)
            return []

        hospitals = []
        with HOSPITALS_PATH.open("r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                hospitals.append(
                    {
                        "hospital_id": row["hospital_id"],
                        "hospital_name": row["hospital_name"],
                        "district": row["district"],
                        "latitude": float(row["latitude"]),
                        "longitude": float(row["longitude"]),
                        "capacity": int(row["capacity"]),
                        "available_beds": int(row["available_beds"]),
                        "trauma_level": row["trauma_level"],
                        "oxygen_available": str(row["oxygen_available"]).lower() in {"yes", "true", "1"},
                        "emergency_contact": row["emergency_contact"],
                    }
                )

        logger.info("Loaded %s hospitals", len(hospitals))
        return hospitals

    def _load_alerts(self) -> List[Dict[str, Any]]:
        if not ALERTS_PATH.exists():
            logger.info("No disaster alert file found at %s", ALERTS_PATH)
            return []

        try:
            with ALERTS_PATH.open("r") as f:
                alerts = json.load(f)
            logger.info("Loaded %s disaster alerts", len(alerts))
            return alerts
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load disaster alerts: %s", exc)
            return []

    def _load_or_build_graph(self) -> nx.Graph:
        graph = None

        if GRAPH_PATH.exists():
            try:
                with GRAPH_PATH.open("rb") as f:
                    graph = pickle.load(f)
                logger.info(
                    "Loaded graph with %s nodes and %s edges",
                    graph.number_of_nodes(),
                    graph.number_of_edges(),
                )
            except (OSError, pickle.PickleError, AttributeError, EOFError) as exc:
                logger.warning("Failed to load hospital graph; rebuilding: %s", exc)

        if not self._graph_is_usable(graph):
            graph = self.build_connected_graph(self.hospitals)
            self._save_graph(graph)

        return graph

    def _graph_is_usable(self, graph: Optional[nx.Graph]) -> bool:
        if graph is None or not self.hospitals:
            return False

        hospital_ids = {h["hospital_id"] for h in self.hospitals}
        if set(graph.nodes()) != hospital_ids:
            logger.info("Hospital graph nodes do not match hospital roster; rebuilding")
            return False

        if graph.number_of_edges() == 0:
            return False

        if not nx.is_connected(graph):
            logger.info("Hospital graph is disconnected; rebuilding")
            return False

        required_edge_attrs = {"distance_km", "estimated_time", "road_status", "risk_score"}
        for _, _, data in graph.edges(data=True):
            if not required_edge_attrs.issubset(data.keys()):
                logger.info("Hospital graph edge attributes are incomplete; rebuilding")
                return False

        return True

    def _save_graph(self, graph: nx.Graph):
        with GRAPH_PATH.open("wb") as f:
            pickle.dump(graph, f)
        logger.info("Saved hospital graph to %s", GRAPH_PATH)

    def build_connected_graph(self, hospitals: List[Dict[str, Any]], nearest_neighbors: int = 4) -> nx.Graph:
        """Build a connected graph using nearest neighbors plus component bridges."""
        graph = nx.Graph()
        for hospital in hospitals:
            graph.add_node(hospital["hospital_id"], **hospital)

        if len(hospitals) < 2:
            return graph

        distances: Dict[Tuple[str, str], float] = {}
        for idx, first in enumerate(hospitals):
            ranked = []
            for second in hospitals:
                if first["hospital_id"] == second["hospital_id"]:
                    continue
                distance = self.haversine_distance(
                    first["latitude"],
                    first["longitude"],
                    second["latitude"],
                    second["longitude"],
                )
                key = tuple(sorted((first["hospital_id"], second["hospital_id"])))
                distances[key] = distance
                ranked.append((distance, second))

            for distance, second in sorted(ranked, key=lambda item: item[0])[:nearest_neighbors]:
                self._add_route_edge(graph, first, second, distance)

        while graph.number_of_nodes() > 0 and not nx.is_connected(graph):
            components = [set(component) for component in nx.connected_components(graph)]
            first_component = components[0]
            best_pair = None
            best_distance = math.inf

            for source_id in first_component:
                for component in components[1:]:
                    for target_id in component:
                        key = tuple(sorted((source_id, target_id)))
                        distance = distances.get(key, math.inf)
                        if distance < best_distance:
                            best_distance = distance
                            best_pair = (source_id, target_id)

            if not best_pair:
                break

            source = graph.nodes[best_pair[0]]
            target = graph.nodes[best_pair[1]]
            self._add_route_edge(graph, source, target, best_distance, connector=True)

        return graph

    def _add_route_edge(
        self,
        graph: nx.Graph,
        source: Dict[str, Any],
        target: Dict[str, Any],
        distance_km: float,
        connector: bool = False,
    ):
        road_status = self._road_status(distance_km, connector)
        graph.add_edge(
            source["hospital_id"],
            target["hospital_id"],
            distance_km=round(distance_km, 2),
            estimated_time=self._estimate_travel_time(distance_km, road_status),
            road_status=road_status,
            risk_score=self._risk_score(distance_km, road_status),
            blocked=False,
            danger_level=0.0,
            affected_by=[],
            route_type="district_connector" if connector else "hospital_link",
        )

    @staticmethod
    def _road_status(distance_km: float, connector: bool = False) -> str:
        if connector and distance_km > 120:
            return "poor"
        if distance_km < 25:
            return "excellent"
        if distance_km < 55:
            return "good"
        if distance_km < 100:
            return "fair"
        return "poor"

    @staticmethod
    def _estimate_travel_time(distance_km: float, road_status: str) -> int:
        speed_by_status = {
            "excellent": 58,
            "good": 48,
            "fair": 38,
            "poor": 28,
        }
        speed = speed_by_status.get(road_status, 38)
        return max(1, round((distance_km / speed) * 60 * 1.15))

    @staticmethod
    def _risk_score(distance_km: float, road_status: str) -> float:
        status_penalty = {
            "excellent": 0.04,
            "good": 0.12,
            "fair": 0.28,
            "poor": 0.48,
        }
        return round(min((distance_km / 180) + status_penalty.get(road_status, 0.25), 1.0), 3)

    def refresh(self):
        """Reload alerts and recalculate route impacts."""
        self.alerts = self._load_alerts()
        return self.recalculate_route_impacts(persist=False)

    def recalculate_route_impacts(self, persist: bool = False) -> Dict[str, Any]:
        """Apply active disaster alerts to a fresh copy of the base graph."""
        if self.base_graph is None:
            self.graph = nx.Graph()
            return {"total_routes": 0, "blocked_routes": 0, "affected_routes": 0}

        graph = deepcopy(self.base_graph)

        for _, _, data in graph.edges(data=True):
            data["blocked"] = False
            data["danger_level"] = 0.0
            data["affected_by"] = []

        active_alerts = [alert for alert in self.alerts if alert.get("is_active", False)]
        affected_edges = 0

        for alert in active_alerts:
            for source_id, target_id, data in graph.edges(data=True):
                danger = self._edge_danger_level(graph, source_id, target_id, alert)
                if danger <= 0:
                    continue

                affected_edges += 1
                data["danger_level"] = round(max(data.get("danger_level", 0.0), danger), 3)
                data["risk_score"] = round(min(1.0, data.get("risk_score", 0.0) + danger * 0.35), 3)
                data["affected_by"].append(
                    {
                        "alert_id": alert.get("alert_id"),
                        "disaster_type": alert.get("disaster_type"),
                        "severity": alert.get("severity", 0),
                        "radius_km": alert.get("affected_radius_km", 0),
                        "location": alert.get("location_name", "Unknown"),
                    }
                )

                if self._should_block_edge(alert, danger):
                    data["blocked"] = True
                    data["road_status"] = "blocked"

        self.graph = graph
        summary = {
            "total_routes": graph.number_of_edges(),
            "blocked_routes": sum(1 for _, _, d in graph.edges(data=True) if d.get("blocked", False)),
            "affected_routes": affected_edges,
            "active_alerts": len(active_alerts),
        }

        if persist:
            self._save_graph(graph)

        return summary

    def _edge_danger_level(self, graph: nx.Graph, source_id: str, target_id: str, alert: Dict[str, Any]) -> float:
        try:
            source = graph.nodes[source_id]
            target = graph.nodes[target_id]
            distance = self.distance_point_to_route_km(
                alert["latitude"],
                alert["longitude"],
                source["latitude"],
                source["longitude"],
                target["latitude"],
                target["longitude"],
            )
            radius = float(alert.get("affected_radius_km", 0))
            severity = float(alert.get("severity", 0))
        except (KeyError, TypeError, ValueError):
            return 0.0

        if radius <= 0 or distance > radius:
            return 0.0

        proximity = 1 - (distance / radius)
        return round(min(1.0, proximity * (0.35 + severity * 0.65)), 3)

    @staticmethod
    def _should_block_edge(alert: Dict[str, Any], danger: float) -> bool:
        disaster_type = alert.get("disaster_type")
        severity = float(alert.get("severity", 0))
        if disaster_type == "bridge_collapse" and danger >= 0.2:
            return True
        if disaster_type == "landslide" and severity >= 0.65 and danger >= 0.35:
            return True
        if disaster_type == "flood" and severity >= 0.7 and danger >= 0.45:
            return True
        if disaster_type == "fire" and severity >= 0.8 and danger >= 0.5:
            return True
        return danger >= 0.72

    def get_hospitals(self, district: Optional[str] = None, min_beds: Optional[int] = None) -> List[Dict[str, Any]]:
        hospitals = self.hospitals

        if district:
            hospitals = [h for h in hospitals if h["district"].lower() == district.lower()]

        if min_beds is not None:
            hospitals = [h for h in hospitals if h["available_beds"] >= min_beds]

        return hospitals

    def get_hospital_by_id(self, hospital_id: str) -> Optional[Dict[str, Any]]:
        return next((h for h in self.hospitals if h["hospital_id"] == hospital_id), None)

    def get_alerts(self, active_only: bool = True) -> List[Dict[str, Any]]:
        self.alerts = self._load_alerts()
        if active_only:
            return [a for a in self.alerts if a.get("is_active", False)]
        return self.alerts

    def get_routes(self, hospital_id: Optional[str] = None, recalculate: bool = True) -> List[Dict[str, Any]]:
        if recalculate:
            self.refresh()

        if not self.graph:
            return []

        routes = []
        for source_id, target_id, data in self.graph.edges(data=True):
            if hospital_id and source_id != hospital_id and target_id != hospital_id:
                continue

            source = self.get_hospital_by_id(source_id)
            target = self.get_hospital_by_id(target_id)
            routes.append(
                {
                    "source_id": source_id,
                    "source_name": source["hospital_name"] if source else source_id,
                    "source_district": source["district"] if source else "",
                    "target_id": target_id,
                    "target_name": target["hospital_name"] if target else target_id,
                    "target_district": target["district"] if target else "",
                    "distance_km": data.get("distance_km", 0),
                    "estimated_time": data.get("estimated_time", 0),
                    "road_status": data.get("road_status", "unknown"),
                    "risk_score": data.get("risk_score", 0),
                    "blocked": data.get("blocked", False),
                    "danger_level": data.get("danger_level", 0),
                    "route_type": data.get("route_type", "hospital_link"),
                    "affected_by": data.get("affected_by", []),
                }
            )

        return sorted(routes, key=lambda route: (route["blocked"], -route["danger_level"], route["distance_km"]))

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2) -> float:
        """Calculate distance in km between two coordinates."""
        radius_km = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def distance_point_to_route_km(
        self,
        point_lat: float,
        point_lon: float,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
    ) -> float:
        """Approximate point-to-segment distance with local planar projection."""
        mean_lat = math.radians((point_lat + start_lat + end_lat) / 3)

        def project(lat: float, lon: float) -> Tuple[float, float]:
            return (lon * 111.32 * math.cos(mean_lat), lat * 110.57)

        px, py = project(point_lat, point_lon)
        ax, ay = project(start_lat, start_lon)
        bx, by = project(end_lat, end_lon)
        dx, dy = bx - ax, by - ay

        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)

        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        closest_x = ax + t * dx
        closest_y = ay + t * dy
        return math.hypot(px - closest_x, py - closest_y)

    def _edge_cost(self, edge_data: Dict[str, Any], strategy: str, avoid_blocked: bool) -> Optional[float]:
        if avoid_blocked and edge_data.get("blocked", False):
            return None

        distance = float(edge_data.get("distance_km", 1))
        minutes = float(edge_data.get("estimated_time", distance))
        danger = float(edge_data.get("danger_level", 0))
        risk = float(edge_data.get("risk_score", 0))
        blocked_penalty = 10000 if edge_data.get("blocked", False) else 0

        if strategy == "fastest":
            return minutes + (danger * 90) + blocked_penalty
        if strategy == "safest":
            return distance * (1 + risk) + (danger * 150) + blocked_penalty
        return distance + (danger * 30) + blocked_penalty

    def dijkstra_path(
        self,
        source: str,
        target: str,
        strategy: str = "shortest",
        avoid_blocked: bool = True,
    ) -> Tuple[Optional[List[str]], Dict[str, Any]]:
        """Find a route using Dijkstra's algorithm and the requested cost strategy."""
        if not self.graph or source not in self.graph or target not in self.graph:
            return None, {"error": "Invalid source or target hospital"}

        queue = [(0.0, source, [source])]
        best_costs = {source: 0.0}

        while queue:
            cost, node, path = heapq.heappop(queue)
            if cost > best_costs.get(node, math.inf):
                continue

            if node == target:
                return path, {"route_cost": round(cost, 2), "hops": len(path) - 1}

            for neighbor in self.graph.neighbors(node):
                edge_data = self.graph[node][neighbor]
                edge_cost = self._edge_cost(edge_data, strategy, avoid_blocked)
                if edge_cost is None:
                    continue

                new_cost = cost + edge_cost
                if new_cost < best_costs.get(neighbor, math.inf):
                    best_costs[neighbor] = new_cost
                    heapq.heappush(queue, (new_cost, neighbor, path + [neighbor]))

        return None, {"error": "No path found"}

    def dijkstra_shortest_path(self, source: str, target: str, avoid_blocked: bool = True):
        return self.dijkstra_path(source, target, strategy="shortest", avoid_blocked=avoid_blocked)

    def dijkstra_fastest_path(self, source: str, target: str, avoid_blocked: bool = True):
        return self.dijkstra_path(source, target, strategy="fastest", avoid_blocked=avoid_blocked)

    def dijkstra_safest_path(self, source: str, target: str, avoid_blocked: bool = True):
        return self.dijkstra_path(source, target, strategy="safest", avoid_blocked=avoid_blocked)

    def optimize_route(
        self,
        source: str,
        target: str,
        strategy: str = "shortest",
        priority_hospital_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Optimize a route between two hospitals."""
        self.refresh()

        if source == target:
            return {"error": "Source and target hospitals must be different", "source": source, "target": target}

        strategies = {
            "shortest": self.dijkstra_shortest_path,
            "fastest": self.dijkstra_fastest_path,
            "safest": self.dijkstra_safest_path,
        }

        if strategy not in strategies:
            return {"error": f"Unknown strategy: {strategy}. Use shortest, fastest, or safest"}

        path, info = strategies[strategy](source, target, avoid_blocked=True)

        if not path:
            path, info = strategies[strategy](source, target, avoid_blocked=False)
            if path:
                info["fallback"] = "Used disaster-affected routes because no fully open path is available"
                info["warning"] = "Route passes through one or more blocked or high-risk road segments"

        if not path:
            return {"error": "No route found", "source": source, "target": target}

        return self._format_route(path, strategy, info, priority_hospital_id)

    def _format_route(
        self,
        path: List[str],
        strategy: str,
        info: Dict[str, Any],
        priority_hospital_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        path_details = []
        segments = []
        total_distance = 0.0
        total_time = 0
        max_danger = 0.0
        blocked_segments = 0

        for idx, hospital_id in enumerate(path):
            hospital = self.get_hospital_by_id(hospital_id)
            path_details.append(
                {
                    "hospital_id": hospital_id,
                    "hospital_name": hospital["hospital_name"] if hospital else hospital_id,
                    "district": hospital["district"] if hospital else "",
                    "available_beds": hospital["available_beds"] if hospital else 0,
                    "oxygen_available": hospital.get("oxygen_available", False) if hospital else False,
                    "is_priority": hospital_id == priority_hospital_id,
                }
            )

            if idx == 0:
                continue

            previous_id = path[idx - 1]
            if self.graph and previous_id in self.graph and hospital_id in self.graph[previous_id]:
                edge = self.graph[previous_id][hospital_id]
                total_distance += float(edge.get("distance_km", 0))
                total_time += int(edge.get("estimated_time", 0))
                max_danger = max(max_danger, float(edge.get("danger_level", 0)))
                if edge.get("blocked", False):
                    blocked_segments += 1
                segments.append(
                    {
                        "source_id": previous_id,
                        "target_id": hospital_id,
                        "distance_km": edge.get("distance_km", 0),
                        "estimated_time": edge.get("estimated_time", 0),
                        "road_status": edge.get("road_status", "unknown"),
                        "risk_score": edge.get("risk_score", 0),
                        "blocked": edge.get("blocked", False),
                        "danger_level": edge.get("danger_level", 0),
                        "affected_by": edge.get("affected_by", []),
                    }
                )

        return {
            "path": path,
            "path_details": path_details,
            "segments": segments,
            "strategy": strategy,
            "total_distance_km": round(total_distance, 2),
            "total_time_minutes": total_time,
            "max_danger_level": round(max_danger, 3),
            "blocked_segments": blocked_segments,
            "num_hops": len(path) - 1,
            **info,
        }

    def get_alternative_routes(self, source: str, target: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Return distinct route alternatives across supported strategies."""
        alternatives = []
        seen_paths = set()

        for strategy in ("safest", "fastest", "shortest"):
            route = self.optimize_route(source, target, strategy=strategy)
            route_key = tuple(route.get("path", []))
            if "error" not in route and route_key and route_key not in seen_paths:
                alternatives.append(route)
                seen_paths.add(route_key)

        if self.graph and source in self.graph and target in self.graph:
            temp_graph = self.graph.copy()
            for route in list(alternatives):
                for segment in route.get("segments", []):
                    if temp_graph.has_edge(segment["source_id"], segment["target_id"]):
                        temp_graph.remove_edge(segment["source_id"], segment["target_id"])
                        break

                original_graph = self.graph
                self.graph = temp_graph
                path, info = self.dijkstra_safest_path(source, target, avoid_blocked=True)
                self.graph = original_graph
                route_key = tuple(path or [])
                if path and route_key not in seen_paths:
                    alternatives.append(self._format_route(path, "safest", info))
                    seen_paths.add(route_key)
                if len(alternatives) >= limit:
                    break

        return alternatives[:limit]

    def get_nearby_hospitals(self, hospital_id: str, max_distance_km: float = 100) -> List[Dict[str, Any]]:
        hospital = self.get_hospital_by_id(hospital_id)
        if not hospital:
            return []

        nearby = []
        for candidate in self.hospitals:
            if candidate["hospital_id"] == hospital_id:
                continue

            distance = self.haversine_distance(
                hospital["latitude"],
                hospital["longitude"],
                candidate["latitude"],
                candidate["longitude"],
            )

            if distance <= max_distance_km:
                nearby.append(
                    {
                        "hospital_id": candidate["hospital_id"],
                        "hospital_name": candidate["hospital_name"],
                        "district": candidate["district"],
                        "distance_km": round(distance, 2),
                        "available_beds": candidate["available_beds"],
                        "oxygen_available": candidate["oxygen_available"],
                    }
                )

        return sorted(nearby, key=lambda item: item["distance_km"])


hospital_network_service = HospitalNetworkService()
