import csv
import datetime as dt
import io
import json
import logging
import math
import os
import re
import uuid
from collections import defaultdict, deque
from typing import Any, Dict, Iterable, List, Optional, Tuple

import networkx as nx
import requests

from src.config import NOMINATIM_USER_AGENT, OPENWEATHERMAP_API_KEY, RAW_DATA_DIR

logger = logging.getLogger(__name__)

SUPPLY_CHAIN_DATA_DIR = os.path.join(os.path.dirname(RAW_DATA_DIR), "supply_chain_uploads")
os.makedirs(SUPPLY_CHAIN_DATA_DIR, exist_ok=True)

LOCATION_COORDINATES = {
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "mangaluru": (12.9141, 74.8560),
    "mangalore": (12.9141, 74.8560),
    "mysuru": (12.2958, 76.6394),
    "mysore": (12.2958, 76.6394),
    "hubballi": (15.3647, 75.1240),
    "shivamogga": (13.9299, 75.5681),
    "madikeri": (12.4244, 75.7382),
    "kodagu": (12.3375, 75.8069),
    "sakleshpur": (12.9442, 75.7848),
    "virajpet": (12.1964, 75.8051),
    "kushalnagar": (12.4575, 75.9590),
    "hassan": (13.0068, 76.1004),
    "shiradi ghat": (12.9061, 75.6688),
    "chikkamagaluru": (13.3161, 75.7720),
    "karwar": (14.8185, 74.1416),
    "honnavar": (14.2799, 74.4439),
    "kumta": (14.4283, 74.4189),
    "ankola": (14.6605, 74.3047),
    "udupi": (13.3409, 74.7421),
    "kundapura": (13.6255, 74.6914),
    "kollur": (13.8667, 74.8167),
    "bhagamandala": (12.3861, 75.5291),
    "sagara": (14.1670, 75.0403),
    "siddapura": (14.3432, 74.8940),
    "sirsi": (14.6192, 74.8354),
    "dharwad": (15.4589, 75.0078),
    "belagavi": (15.8497, 74.4977),
    "vijayapura": (16.8302, 75.7100),
    "bagalkot": (16.1691, 75.6615),
    "gadag": (15.4319, 75.6355),
    "raichur": (16.2120, 77.3566),
    "koppal": (15.3505, 76.1567),
    "kalburgi": (17.3297, 76.8343),
    "yadgir": (16.7626, 77.1446),
    "chamarajanagara": (11.9261, 76.9437),
    "goa border": (14.9048, 74.0842),
    "goa_border": (14.9048, 74.0842),
    "haveri": (14.7951, 75.3991),
    "davanagere": (14.4644, 75.9218),
    "tumakuru": (13.3379, 77.1173),
    "mandya": (12.5218, 76.8951),
    "chikkaballapur": (13.4355, 77.7315),
    "kolar": (13.1367, 78.1295),
    "ballari": (15.1394, 76.9214),
    "bidar": (17.9133, 77.5301),
    "gonikoppal": (12.1838, 75.9323),
    "ponnampet": (12.1446, 75.9453),
    "kerala border": (12.0605, 75.7985),
    "kerala_border": (12.0605, 75.7985),
    "jog falls": (14.2298, 74.8120),
    "jog_falls": (14.2298, 74.8120),
    "shanghai": (31.2304, 121.4737),
    "singapore": (1.2903, 103.8519),
    "rotterdam": (51.9244, 4.4777),
    "hamburg": (53.5511, 9.9937),
    "mumbai": (19.0760, 72.8777),
    "chennai": (13.0827, 80.2707),
    "los angeles": (34.0522, -118.2437),
    "long beach": (33.7701, -118.1937),
    "suez canal": (30.5852, 32.2654),
    "port said": (31.2653, 32.3019),
    "hong kong": (22.3193, 114.1694),
    "shenzhen": (22.5431, 114.0579),
    "dubai": (25.2048, 55.2708),
    "taichung": (24.1477, 120.6736),
    "kaohsiung": (22.6273, 120.3014),
    "tainan": (22.9999, 120.2270),
    "yangshan": (30.6238, 122.0597),
}

COLUMN_ALIASES = {
    "source_company": ["source_company", "source", "supplier", "from_company", "company_a", "from", "supplier_name", "from_settlement", "relief_hub", "origin_node", "source_node"],
    "target_company": ["target_company", "target", "customer", "to_company", "company_b", "to", "destination_company", "buyer", "customer_name", "to_settlement", "village", "target_node", "destination_node"],
    "relationship_type": ["relationship_type", "relationship", "relation", "link_type", "road_type", "access_type"],
    "material": ["material", "product", "raw_material", "commodity", "sku", "relief_payload", "aid_type", "cargo"],
    "origin": ["origin", "origin_port", "origin_location", "from_location", "route_from", "source_location", "source_country", "from_country", "road_from"],
    "destination": ["destination", "destination_port", "destination_location", "to_location", "route_to", "target_location", "destination_country", "to_country", "road_to"],
    "transport_mode": ["transport_mode", "mode", "shipment_mode", "logistics_mode", "route_mode", "vehicle_type"],
    "criticality": ["criticality", "priority", "importance", "tier", "risk_level", "relief_priority", "medical_priority"],
    "route_name": ["route", "route_name", "lane", "trade_route", "road_segment", "corridor", "access_route", "road_name"],
    "distance_km": ["distance_km", "distance", "km"],
    "travel_time_min": ["travel_time_min", "travel_minutes", "duration_min", "time_min"],
    "notes": ["notes", "remarks", "risk_notes"],
    "origin_lat": ["origin_lat", "from_lat", "source_lat"],
    "origin_lon": ["origin_lon", "from_lon", "source_lon"],
    "destination_lat": ["destination_lat", "to_lat", "target_lat"],
    "destination_lon": ["destination_lon", "to_lon", "target_lon"],
}

CRITICALITY_WEIGHTS = {"high": 1.0, "medium": 0.78, "low": 0.58}
TRANSPORT_KEYWORDS = {
    "sea": ["port", "vessel", "maritime", "shipping", "canal", "terminal"],
    "air": ["airport", "air cargo", "freight", "airline"],
    "road": ["truck", "highway", "road", "border crossing", "ghat", "bridge", "village access"],
    "rail": ["rail", "train", "intermodal"],
}

SEVERITY_KEYWORDS = {
    "critical": ["block", "blocked", "closure", "closed", "halt", "shutdown", "strike", "sanction", "suspended", "flood", "storm", "collision", "landslide", "washed out", "cut off"],
    "warning": ["delay", "slowdown", "congestion", "watch", "inspection", "shortage", "queue", "cyber", "waterlogging", "overflow", "heavy rain"],
}

CATEGORY_KEYWORDS = {
    "weather": ["storm", "typhoon", "cyclone", "rain", "flood", "wind", "weather"],
    "labor": ["labor", "union", "strike"],
    "logistics": ["port", "shipping", "logistics", "freight", "truck", "vessel", "canal"],
    "geopolitical": ["sanction", "tariff", "export control", "border", "conflict", "war"],
    "cyber": ["cyber", "outage", "system", "ransomware"],
    "supply": ["shortage", "factory", "supplier", "mine", "refinery", "production"],
    "landslide": ["landslide", "slope", "ghat", "mudslide", "rockfall"],
    "flood": ["flood", "waterlogging", "overflow", "inundation"],
}

GEOCODE_URL = "https://nominatim.openstreetmap.org/search"
SAFE_ROUTE_RISK_THRESHOLD = 0.45


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _slug(value: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return lowered or "item"


def _clean_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _norm_lookup(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _dedupe_preserve(values: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = _normalize_text(value)
        key = _norm_lookup(cleaned)
        if not cleaned or key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


class SupplyChainMonitor:
    def __init__(self, storage_dir: str = SUPPLY_CHAIN_DATA_DIR, weather_api_key: Optional[str] = None):
        self.storage_dir = storage_dir
        self.weather_api_key = weather_api_key or OPENWEATHERMAP_API_KEY
        self.geocode_cache_path = os.path.join(os.path.dirname(self.storage_dir), "geocode_cache.json")
        self.geocode_headers = {"User-Agent": NOMINATIM_USER_AGENT}
        os.makedirs(self.storage_dir, exist_ok=True)
        self.geocode_cache = self._load_geocode_cache()

    def parse_upload(self, filename: str, content: bytes) -> Dict[str, Any]:
        extension = os.path.splitext(filename or "")[1].lower()
        if extension not in {".csv", ".json"}:
            raise ValueError("Only .csv and .json uploads are supported right now.")

        if extension == ".csv":
            rows = self._parse_csv(content)
        else:
            rows = self._parse_json(content)

        routes = self._normalize_routes(rows)
        if not routes:
            raise ValueError("No valid relief road segments were found in the uploaded file.")

        snapshot_id = str(uuid.uuid4())
        snapshot = {
            "snapshot_id": snapshot_id,
            "file_name": filename,
            "uploaded_at": _utc_now(),
            "route_count": len(routes),
            "routes": routes,
            "nodes": self._build_nodes(routes),
            "watch_terms": self._extract_watch_terms(routes),
            "template_columns": sorted(COLUMN_ALIASES.keys()),
        }
        self._save_snapshot(snapshot)
        return snapshot

    def load_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        path = self._snapshot_path(snapshot_id)
        if not os.path.exists(path):
            raise FileNotFoundError(snapshot_id)
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def list_snapshots(self) -> List[Dict[str, Any]]:
        snapshots = []
        for entry in sorted(os.listdir(self.storage_dir), reverse=True):
            if not entry.endswith(".json"):
                continue
            path = os.path.join(self.storage_dir, entry)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    snapshot = json.load(handle)
                snapshots.append(
                    {
                        "snapshot_id": snapshot["snapshot_id"],
                        "file_name": snapshot["file_name"],
                        "uploaded_at": snapshot["uploaded_at"],
                        "route_count": snapshot.get("route_count", len(snapshot.get("routes", []))),
                        "last_checked_at": snapshot.get("last_checked_at"),
                    }
                )
            except Exception as exc:
                logger.warning("Failed to read snapshot %s: %s", path, exc)
        return snapshots[:20]

    def build_report(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        alerts, source_status = self._collect_alerts(snapshot)
        impacted_links, impacted_companies = self._score_routes(snapshot["routes"], alerts)

        metrics = {
            "total_routes": len(snapshot["routes"]),
            "blocked_routes": sum(1 for route in impacted_links if route["status"] == "blocked"),
            "at_risk_routes": sum(1 for route in impacted_links if route["status"] == "at_risk"),
            "healthy_routes": max(len(snapshot["routes"]) - len(impacted_links), 0),
            "monitored_companies": len([n for n in snapshot["nodes"] if n["type"] == "company"]),
            "watched_locations": len([n for n in snapshot["nodes"] if n["type"] == "location"]),
            "monitored_settlements": len([n for n in snapshot["nodes"] if n["type"] == "company"]),
            "watched_road_points": len([n for n in snapshot["nodes"] if n["type"] == "location"]),
            "active_alerts": len(alerts),
        }

        report = {
            "snapshot_id": snapshot["snapshot_id"],
            "file_name": snapshot["file_name"],
            "uploaded_at": snapshot["uploaded_at"],
            "last_checked_at": _utc_now(),
            "metrics": metrics,
            "alerts": alerts,
            "impacted_links": impacted_links,
            "impacted_companies": impacted_companies,
            "network": {
                "nodes": snapshot["nodes"],
                "links": snapshot["routes"],
            },
            "source_status": source_status,
            "watch_terms": snapshot["watch_terms"],
        }
        snapshot["last_checked_at"] = report["last_checked_at"]
        snapshot["latest_report"] = report
        self._save_snapshot(snapshot)
        return report

    def template(self) -> Dict[str, Any]:
        sample_rows = [
            {
                "source_company": "Bengaluru Relief Hub",
                "target_company": "Sakleshpur",
                "relationship_type": "relief_road",
                "material": "Food, water, medical kits",
                "origin": "Bengaluru",
                "destination": "Sakleshpur",
                "transport_mode": "truck",
                "criticality": "high",
                "route_name": "Bengaluru to Sakleshpur relief corridor",
            },
            {
                "source_company": "Sakleshpur",
                "target_company": "Mangaluru Coastal Hub",
                "relationship_type": "ghat_road",
                "material": "Rescue supplies",
                "origin": "Shiradi Ghat",
                "destination": "Mangaluru",
                "transport_mode": "truck",
                "criticality": "high",
                "route_name": "Shiradi Ghat emergency access",
            },
        ]
        return {"columns": list(COLUMN_ALIASES.keys()), "sample_rows": sample_rows}

    def _parse_csv(self, content: bytes) -> List[Dict[str, Any]]:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        return [dict(row) for row in reader]

    def _parse_json(self, content: bytes) -> List[Dict[str, Any]]:
        parsed = json.loads(content.decode("utf-8"))
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            for key in ("routes", "links", "edges", "data"):
                if isinstance(parsed.get(key), list):
                    return parsed[key]
        raise ValueError("JSON uploads must be a list of route objects or an object containing routes/links/edges/data.")

    def _normalize_routes(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        routes = []
        for index, row in enumerate(rows, start=1):
            normalized = {self._canonical_key(key): _normalize_text(value) for key, value in row.items()}
            source_company = normalized.get("source_company")
            target_company = normalized.get("target_company")
            if not source_company or not target_company:
                continue

            origin = normalized.get("origin") or source_company
            destination = normalized.get("destination") or target_company
            transport_mode = (normalized.get("transport_mode") or "truck").lower()
            criticality = (normalized.get("criticality") or "medium").lower()
            notes = normalized.get("notes", "").lower()
            if criticality == "medium":
                if "very high" in notes or "high" in notes:
                    criticality = "high"
                elif "safe" in notes or "low risk" in notes:
                    criticality = "low"
            if criticality not in CRITICALITY_WEIGHTS:
                criticality = "medium"

            route_name = normalized.get("route_name") or f"{origin} to {destination}"
            origin_lat, origin_lon = self._resolve_coordinates(origin, normalized.get("origin_lat"), normalized.get("origin_lon"))
            destination_lat, destination_lon = self._resolve_coordinates(destination, normalized.get("destination_lat"), normalized.get("destination_lon"))

            routes.append(
                {
                    "id": f"route-{index}-{_slug(source_company)}-{_slug(target_company)}",
                    "source_company": source_company,
                    "target_company": target_company,
                    "relationship_type": normalized.get("relationship_type") or "supplies",
                    "material": normalized.get("material") or "unspecified",
                    "origin": origin,
                    "destination": destination,
                    "transport_mode": transport_mode,
                    "criticality": criticality,
                    "route_name": route_name,
                    "distance_km": normalized.get("distance_km"),
                    "travel_time_min": normalized.get("travel_time_min"),
                    "notes": normalized.get("notes"),
                    "origin_lat": origin_lat,
                    "origin_lon": origin_lon,
                    "destination_lat": destination_lat,
                    "destination_lon": destination_lon,
                }
            )
        return routes

    def _canonical_key(self, key: str) -> str:
        cleaned = _clean_key(key)
        for canonical, aliases in COLUMN_ALIASES.items():
            if cleaned in {_clean_key(alias) for alias in aliases}:
                return canonical
        return cleaned

    def _resolve_coordinates(
        self,
        location: str,
        lat_value: Optional[str],
        lon_value: Optional[str],
    ) -> Tuple[Optional[float], Optional[float]]:
        try:
            if lat_value and lon_value:
                return float(lat_value), float(lon_value)
        except ValueError:
            pass

        coords = LOCATION_COORDINATES.get(_norm_lookup(location))
        if coords:
            return coords
        coords = self._geocode_location(location)
        if coords:
            return coords
        return None, None

    def _build_nodes(self, routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        company_nodes = {}
        location_nodes = {}
        for route in routes:
            for company in (route["source_company"], route["target_company"]):
                company_nodes[_norm_lookup(company)] = {
                    "id": f"company-{_slug(company)}",
                    "label": company,
                    "type": "company",
                }

            for prefix in ("origin", "destination"):
                location = route[prefix]
                lat = route.get(f"{prefix}_lat")
                lon = route.get(f"{prefix}_lon")
                location_nodes[_norm_lookup(location)] = {
                    "id": f"location-{_slug(location)}",
                    "label": location,
                    "type": "location",
                    "lat": lat,
                    "lon": lon,
                }

        return list(company_nodes.values()) + list(location_nodes.values())

    def _extract_watch_terms(self, routes: List[Dict[str, Any]]) -> List[str]:
        return _dedupe_preserve(
            [
                value
                for route in routes
                for value in (
                    route["source_company"],
                    route["target_company"],
                    route["origin"],
                    route["destination"],
                    route["material"],
                    route["route_name"],
                )
            ]
        )

    def _collect_alerts(self, snapshot: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        alerts = []
        source_status = {
            "gdelt": {"enabled": True, "live": False},
            "weather": {"enabled": bool(self.weather_api_key), "live": False},
        }

        try:
            gdelt_alerts = self._fetch_gdelt_alerts(snapshot)
            source_status["gdelt"]["live"] = True
            if gdelt_alerts:
                alerts.extend(gdelt_alerts)
        except Exception as exc:
            source_status["gdelt"]["error"] = str(exc)
            logger.warning("GDELT check failed: %s", exc)

        try:
            weather_alerts = self._fetch_weather_alerts(snapshot)
            if self.weather_api_key:
                source_status["weather"]["live"] = True
            if weather_alerts:
                alerts.extend(weather_alerts)
        except Exception as exc:
            source_status["weather"]["error"] = str(exc)
            logger.warning("Weather check failed: %s", exc)

        deduped = []
        seen = set()
        for alert in sorted(alerts, key=lambda item: item.get("severity", 0), reverse=True):
            key = (alert.get("title"), tuple(sorted(alert.get("locations", []))), alert.get("source"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(alert)
        return deduped[:25], source_status

    def _fetch_gdelt_alerts(self, snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        terms = [
            term
            for term in snapshot["watch_terms"]
            if len(term) >= 4 and _norm_lookup(term) not in {"high", "medium", "low", "unspecified"}
        ][:8]
        if not terms:
            return []

        query_terms = " OR ".join(f'"{term}"' for term in terms)
        query = f"({query_terms}) AND (flood OR rainfall OR landslide OR road OR bridge OR waterlogging OR rescue OR relief OR storm)"
        response = requests.get(
            "https://api.gdeltproject.org/api/v2/doc/doc",
            params={
                "query": query,
                "mode": "ArtList",
                "maxrecords": 12,
                "format": "json",
                "sort": "DateDesc",
                "timespan": "3days",
            },
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        articles = payload.get("articles", [])
        alerts = []
        for article in articles:
            title = _normalize_text(article.get("title")) or "External disruption signal"
            description = _normalize_text(article.get("seendate")) or _normalize_text(article.get("domain")) or "Live signal from GDELT"
            matched_terms = [term for term in terms if _norm_lookup(term) in _norm_lookup(f"{title} {description} {article.get('url', '')}")]
            text_blob = f"{title} {description}".lower()
            severity = self._keyword_severity(text_blob)
            alerts.append(
                {
                    "id": f"gdelt-{uuid.uuid4()}",
                    "title": title,
                    "description": description,
                    "category": self._keyword_category(text_blob),
                    "severity": severity,
                    "type": "critical" if severity >= 0.75 else "warning" if severity >= 0.45 else "info",
                    "locations": matched_terms,
                    "companies": matched_terms,
                    "timestamp": _normalize_text(article.get("seendate")) or _utc_now(),
                    "source": "gdelt",
                    "url": article.get("url"),
                }
            )
        return alerts

    def _fetch_weather_alerts(self, snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.weather_api_key:
            return []

        points = {}
        for route in snapshot["routes"]:
            for prefix in ("origin", "destination"):
                lat = route.get(f"{prefix}_lat")
                lon = route.get(f"{prefix}_lon")
                if lat is None or lon is None:
                    continue
                points[route[prefix]] = (lat, lon)

        alerts = []
        for location, (lat, lon) in list(points.items())[:10]:
            response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"lat": lat, "lon": lon, "appid": self.weather_api_key, "units": "metric"},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            weather = (payload.get("weather") or [{}])[0]
            wind_speed = float(payload.get("wind", {}).get("speed", 0) or 0)
            visibility = float(payload.get("visibility", 10000) or 10000)
            severity = 0.0
            description = _normalize_text(weather.get("description")) or "Current weather"
            if weather.get("main") in {"Thunderstorm", "Tornado", "Squall", "Ash"}:
                severity = 0.82
            elif wind_speed >= 14:
                severity = 0.7
            elif visibility <= 2000 or weather.get("main") in {"Snow", "Rain"}:
                severity = 0.5

            if severity < 0.45:
                continue

            alerts.append(
                {
                    "id": f"weather-{_slug(location)}",
                    "title": f"Weather disruption risk near {location}",
                    "description": f"{description}; wind {wind_speed:.1f} m/s; visibility {visibility:.0f}m.",
                    "category": "weather",
                    "severity": severity,
                    "type": "critical" if severity >= 0.75 else "warning",
                    "locations": [location],
                    "companies": [],
                    "timestamp": _utc_now(),
                    "source": "weather",
                }
            )
        return alerts

    def _keyword_severity(self, text_blob: str) -> float:
        severity = 0.28
        if any(keyword in text_blob for keyword in SEVERITY_KEYWORDS["warning"]):
            severity = max(severity, 0.52)
        if any(keyword in text_blob for keyword in SEVERITY_KEYWORDS["critical"]):
            severity = max(severity, 0.8)
        return severity

    def _keyword_category(self, text_blob: str) -> str:
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in text_blob for keyword in keywords):
                return category
        return "logistics"

    def _score_routes(
        self,
        routes: List[Dict[str, Any]],
        alerts: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        adjacency = defaultdict(list)
        for route in routes:
            adjacency[route["source_company"]].append(route["target_company"])

        route_signal_map = self._build_route_signal_map(routes, alerts)
        impacted_links = []
        company_scores: Dict[str, Dict[str, Any]] = {}
        for route in routes:
            signal = route_signal_map[route["id"]]
            matches = signal["matched_alerts"]
            if signal["risk_score"] < 0.38:
                continue

            top_risk = signal["risk_score"]
            status = signal["status"]
            downstream = self._downstream_companies(route["target_company"], adjacency)
            alternative_route = self._recommend_alternative_route(route, routes, route_signal_map)
            impacted_links.append(
                {
                    "route_id": route["id"],
                    "route_name": route["route_name"],
                    "source_company": route["source_company"],
                    "target_company": route["target_company"],
                    "material": route["material"],
                    "origin": route["origin"],
                    "destination": route["destination"],
                    "transport_mode": route["transport_mode"],
                    "criticality": route["criticality"],
                    "status": status,
                    "risk_score": top_risk,
                    "matched_alerts": matches[:3],
                    "downstream_companies": downstream,
                    "alternative_route": alternative_route,
                }
            )

            for company, direct in ((route["source_company"], True), (route["target_company"], True)):
                current = company_scores.setdefault(
                    company,
                    {
                        "company": company,
                        "status": status,
                        "risk_score": top_risk,
                        "direct_impacts": 0,
                        "downstream_exposure": [],
                    },
                )
                current["direct_impacts"] += 1
                current["risk_score"] = max(current["risk_score"], top_risk)
                current["status"] = "blocked" if current["risk_score"] >= 0.72 else "at_risk"

            for company in downstream:
                current = company_scores.setdefault(
                    company,
                    {
                        "company": company,
                        "status": "watch",
                        "risk_score": max(top_risk - 0.12, 0.2),
                        "direct_impacts": 0,
                        "downstream_exposure": [],
                    },
                )
                current["risk_score"] = max(current["risk_score"], top_risk - 0.12)
                if current["status"] != "blocked":
                    current["status"] = "at_risk" if current["risk_score"] >= 0.45 else "watch"
                current["downstream_exposure"] = _dedupe_preserve(current["downstream_exposure"] + [route["target_company"]])

        impacted_links.sort(key=lambda item: item["risk_score"], reverse=True)
        impacted_companies = sorted(company_scores.values(), key=lambda item: item["risk_score"], reverse=True)
        return impacted_links, impacted_companies

    def _build_route_signal_map(
        self,
        routes: List[Dict[str, Any]],
        alerts: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        route_signal_map: Dict[str, Dict[str, Any]] = {}
        for route in routes:
            matches = []
            for alert in alerts:
                score, reasons = self._route_alert_score(route, alert)
                if score < 0.38:
                    continue
                combined = min(1.0, score * alert["severity"] * (1.15 if route["criticality"] == "high" else 1.0))
                matches.append(
                    {
                        "alert_id": alert["id"],
                        "alert_title": alert["title"],
                        "alert_source": alert["source"],
                        "alert_type": alert["type"],
                        "category": alert["category"],
                        "severity": round(combined, 2),
                        "reasons": reasons,
                        "url": alert.get("url"),
                    }
                )
            matches.sort(key=lambda item: item["severity"], reverse=True)
            top_risk = matches[0]["severity"] if matches else 0.0
            status = "blocked" if top_risk >= 0.72 else "at_risk" if top_risk >= 0.38 else "healthy"
            route_signal_map[route["id"]] = {
                "risk_score": round(top_risk, 2),
                "status": status,
                "matched_alerts": matches,
            }
        return route_signal_map

    def _route_alert_score(self, route: Dict[str, Any], alert: Dict[str, Any]) -> Tuple[float, List[str]]:
        haystack = _norm_lookup(
            " ".join(
                [
                    alert.get("title", ""),
                    alert.get("description", ""),
                    *alert.get("locations", []),
                    *alert.get("companies", []),
                    alert.get("category", ""),
                ]
            )
        )
        score = 0.0
        reasons = []

        def bump(weight: float, label: str, value: str):
            nonlocal score
            if value and _norm_lookup(value) in haystack:
                score += weight
                reasons.append(f"{label}: {value}")

        bump(0.38, "origin match", route["origin"])
        bump(0.38, "destination match", route["destination"])
        bump(0.3, "supplier match", route["source_company"])
        bump(0.3, "buyer match", route["target_company"])
        bump(0.18, "material match", route["material"])

        mode_keywords = TRANSPORT_KEYWORDS.get(route["transport_mode"], [])
        if any(keyword in haystack for keyword in mode_keywords):
            score += 0.12
            reasons.append(f"transport mode signal: {route['transport_mode']}")

        return min(score, 1.0), reasons

    def _downstream_companies(self, company: str, adjacency: Dict[str, List[str]]) -> List[str]:
        queue = deque(adjacency.get(company, []))
        seen = set()
        downstream = []
        while queue:
            current = queue.popleft()
            if current in seen:
                continue
            seen.add(current)
            downstream.append(current)
            queue.extend(adjacency.get(current, []))
        return downstream

    def _recommend_alternative_route(
        self,
        route: Dict[str, Any],
        routes: List[Dict[str, Any]],
        route_signal_map: Dict[str, Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        current_risk = route_signal_map[route["id"]]["risk_score"]
        supplier_candidate = self._find_supplier_substitute(route, routes, route_signal_map)
        location_candidate = self._find_location_reroute(route, routes, route_signal_map)
        company_candidate = self._find_company_reroute(route, routes, route_signal_map)

        candidates = [candidate for candidate in (supplier_candidate, location_candidate, company_candidate) if candidate]
        if not candidates:
            return None

        best = min(
            candidates,
            key=lambda item: (
                item["estimated_risk_score"],
                len(item["route_ids"]),
                -item["risk_reduction"],
            ),
        )
        best["risk_reduction"] = round(max(current_risk - best["estimated_risk_score"], 0.0), 2)
        return best

    def _find_supplier_substitute(
        self,
        route: Dict[str, Any],
        routes: List[Dict[str, Any]],
        route_signal_map: Dict[str, Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        candidates = []
        for candidate in routes:
            if candidate["id"] == route["id"]:
                continue
            if _norm_lookup(candidate["target_company"]) != _norm_lookup(route["target_company"]):
                continue
            if not self._route_is_safe(candidate, route_signal_map):
                continue

            material_penalty = 0.0 if _norm_lookup(candidate["material"]) == _norm_lookup(route["material"]) else 0.12
            mode_penalty = 0.0 if candidate["transport_mode"] == route["transport_mode"] else 0.06
            distance_penalty = self._route_distance_penalty(route, candidate)
            estimated_risk = min(
                1.0,
                route_signal_map[candidate["id"]]["risk_score"] + material_penalty + mode_penalty + distance_penalty,
            )
            candidates.append((estimated_risk, candidate))

        if not candidates:
            return None

        estimated_risk, candidate = min(candidates, key=lambda item: item[0])
        same_material = _norm_lookup(candidate["material"]) == _norm_lookup(route["material"])
        reason = "same material and same buyer" if same_material else "same buyer with a safer inbound lane"
        return {
            "strategy": "supplier_substitution",
            "summary": f"Shift supply to {candidate['source_company']} -> {candidate['target_company']} via {candidate['route_name']}.",
            "reason": reason,
            "estimated_risk_score": round(estimated_risk, 2),
            "risk_reduction": 0.0,
            "route_ids": [candidate["id"]],
            "route_names": [candidate["route_name"]],
            "company_path": [candidate["source_company"], candidate["target_company"]],
            "location_path": [candidate["origin"], candidate["destination"]],
        }

    def _find_location_reroute(
        self,
        route: Dict[str, Any],
        routes: List[Dict[str, Any]],
        route_signal_map: Dict[str, Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        graph = nx.DiGraph()
        for candidate in routes:
            if candidate["id"] == route["id"] or not self._route_is_safe(candidate, route_signal_map):
                continue
            weight = 1.0 + route_signal_map[candidate["id"]]["risk_score"] * 4
            if graph.has_edge(candidate["origin"], candidate["destination"]) and graph[candidate["origin"]][candidate["destination"]]["weight"] <= weight:
                continue
            graph.add_edge(
                candidate["origin"],
                candidate["destination"],
                weight=weight,
                route_id=candidate["id"],
                route_name=candidate["route_name"],
                source_company=candidate["source_company"],
                target_company=candidate["target_company"],
            )

        try:
            location_path = nx.shortest_path(graph, route["origin"], route["destination"], weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

        if len(location_path) < 2:
            return None

        route_ids = []
        route_names = []
        company_path = []
        path_risks = []
        for index in range(len(location_path) - 1):
            edge = graph[location_path[index]][location_path[index + 1]]
            route_ids.append(edge["route_id"])
            route_names.append(edge["route_name"])
            path_risks.append(route_signal_map[edge["route_id"]]["risk_score"])
            if index == 0:
                company_path.append(edge["source_company"])
            company_path.append(edge["target_company"])

        waypoints = location_path[1:-1]
        reason = "reroutes around the disrupted lane inside your uploaded logistics network"
        if waypoints:
            reason = f"reroutes via {', '.join(waypoints)} to avoid the disrupted corridor"
        return {
            "strategy": "network_reroute",
            "summary": f"Reroute shipments from {route['origin']} to {route['destination']} using {' -> '.join(location_path)}.",
            "reason": reason,
            "estimated_risk_score": round(max(path_risks) if path_risks else 0.0, 2),
            "risk_reduction": 0.0,
            "route_ids": route_ids,
            "route_names": route_names,
            "company_path": company_path,
            "location_path": location_path,
        }

    def _find_company_reroute(
        self,
        route: Dict[str, Any],
        routes: List[Dict[str, Any]],
        route_signal_map: Dict[str, Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        graph = nx.DiGraph()
        route_lookup = {}
        for candidate in routes:
            if candidate["id"] == route["id"] or not self._route_is_safe(candidate, route_signal_map):
                continue
            weight = 1.0 + route_signal_map[candidate["id"]]["risk_score"] * 4
            edge_key = (candidate["source_company"], candidate["target_company"])
            existing_weight = graph[candidate["source_company"]][candidate["target_company"]]["weight"] if graph.has_edge(*edge_key) else None
            if existing_weight is not None and existing_weight <= weight:
                continue
            graph.add_edge(candidate["source_company"], candidate["target_company"], weight=weight)
            route_lookup[edge_key] = candidate

        try:
            company_path = nx.shortest_path(graph, route["source_company"], route["target_company"], weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

        if len(company_path) < 3:
            return None

        route_ids = []
        route_names = []
        location_path = []
        path_risks = []
        for index in range(len(company_path) - 1):
            candidate = route_lookup[(company_path[index], company_path[index + 1])]
            route_ids.append(candidate["id"])
            route_names.append(candidate["route_name"])
            path_risks.append(route_signal_map[candidate["id"]]["risk_score"])
            if index == 0:
                location_path.append(candidate["origin"])
            location_path.append(candidate["destination"])

        return {
            "strategy": "supplier_network_reroute",
            "summary": f"Move supply through {' -> '.join(company_path)} instead of the disrupted direct lane.",
            "reason": "uses an existing lower-risk supplier chain already present in the uploaded network",
            "estimated_risk_score": round(max(path_risks) if path_risks else 0.0, 2),
            "risk_reduction": 0.0,
            "route_ids": route_ids,
            "route_names": route_names,
            "company_path": company_path,
            "location_path": location_path,
        }

    def _route_is_safe(
        self,
        route: Dict[str, Any],
        route_signal_map: Dict[str, Dict[str, Any]],
    ) -> bool:
        return route_signal_map[route["id"]]["risk_score"] < SAFE_ROUTE_RISK_THRESHOLD

    def _route_distance_penalty(self, route: Dict[str, Any], candidate: Dict[str, Any]) -> float:
        current_distance = self._route_distance_km(route)
        candidate_distance = self._route_distance_km(candidate)
        if current_distance is None or candidate_distance is None or current_distance <= 0:
            return 0.0
        extra_distance_ratio = max(candidate_distance - current_distance, 0.0) / current_distance
        return min(extra_distance_ratio * 0.15, 0.15)

    def _route_distance_km(self, route: Dict[str, Any]) -> Optional[float]:
        coords = (
            route.get("origin_lat"),
            route.get("origin_lon"),
            route.get("destination_lat"),
            route.get("destination_lon"),
        )
        if any(value is None for value in coords):
            return None
        return self._haversine_km(coords[0], coords[1], coords[2], coords[3])

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius_km = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        return 2 * radius_km * math.asin(math.sqrt(a))

    def _load_geocode_cache(self) -> Dict[str, List[float]]:
        if not os.path.exists(self.geocode_cache_path):
            return {}
        try:
            with open(self.geocode_cache_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return {key: value for key, value in payload.items() if isinstance(value, list) and len(value) == 2}
        except Exception as exc:
            logger.warning("Failed to load geocode cache: %s", exc)
            return {}

    def _persist_geocode_cache(self) -> None:
        try:
            with open(self.geocode_cache_path, "w", encoding="utf-8") as handle:
                json.dump(self.geocode_cache, handle, indent=2)
        except Exception as exc:
            logger.warning("Failed to save geocode cache: %s", exc)

    def _geocode_location(self, location: str) -> Optional[Tuple[float, float]]:
        normalized = _norm_lookup(location)
        cached = self.geocode_cache.get(normalized)
        if cached:
            return float(cached[0]), float(cached[1])

        if not location.strip():
            return None

        try:
            response = requests.get(
                GEOCODE_URL,
                params={"q": location, "format": "jsonv2", "limit": 1},
                headers=self.geocode_headers,
                timeout=10,
            )
            response.raise_for_status()
            results = response.json()
        except Exception as exc:
            logger.info("Geocoding failed for %s: %s", location, exc)
            return None

        if not results:
            return None

        coords = (float(results[0]["lat"]), float(results[0]["lon"]))
        self.geocode_cache[normalized] = [coords[0], coords[1]]
        self._persist_geocode_cache()
        return coords

    def _snapshot_path(self, snapshot_id: str) -> str:
        return os.path.join(self.storage_dir, f"{snapshot_id}.json")

    def _save_snapshot(self, snapshot: Dict[str, Any]) -> None:
        with open(self._snapshot_path(snapshot["snapshot_id"]), "w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, indent=2)
