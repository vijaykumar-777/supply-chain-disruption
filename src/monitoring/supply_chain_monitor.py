import csv
import datetime as dt
import io
import json
import logging
import os
import re
import uuid
from collections import defaultdict, deque
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

from src.config import OPENWEATHERMAP_API_KEY, RAW_DATA_DIR

logger = logging.getLogger(__name__)

SUPPLY_CHAIN_DATA_DIR = os.path.join(os.path.dirname(RAW_DATA_DIR), "supply_chain_uploads")
os.makedirs(SUPPLY_CHAIN_DATA_DIR, exist_ok=True)

DEFAULT_DISRUPTIONS = [
    {
        "id": "fallback-suez",
        "title": "Suez Canal vessel backlog",
        "description": "Logistics queue length has spiked and vessel transits are being delayed.",
        "category": "logistics",
        "severity": 0.86,
        "type": "critical",
        "locations": ["Suez Canal", "Port Said", "Egypt"],
        "companies": [],
        "timestamp": "2026-04-03T08:30:00Z",
        "source": "fallback",
    },
    {
        "id": "fallback-shanghai",
        "title": "Shanghai port labor dispute",
        "description": "Container throughput is reduced because of ongoing labor action at terminal operations.",
        "category": "labor",
        "severity": 0.74,
        "type": "critical",
        "locations": ["Shanghai", "Yangshan", "China"],
        "companies": [],
        "timestamp": "2026-04-02T14:00:00Z",
        "source": "fallback",
    },
    {
        "id": "fallback-singapore",
        "title": "Singapore port cyber disruption",
        "description": "Port systems are operating under contingency procedures after a cyber incident.",
        "category": "cyber",
        "severity": 0.58,
        "type": "warning",
        "locations": ["Singapore", "Jurong Port"],
        "companies": [],
        "timestamp": "2026-04-02T22:00:00Z",
        "source": "fallback",
    },
    {
        "id": "fallback-myanmar",
        "title": "Rare earth export controls tighten in Myanmar",
        "description": "Cross-border movement of rare earth materials has been interrupted by new export restrictions.",
        "category": "geopolitical",
        "severity": 0.81,
        "type": "critical",
        "locations": ["Myanmar", "Kunming"],
        "companies": [],
        "timestamp": "2026-04-03T03:00:00Z",
        "source": "fallback",
    },
    {
        "id": "fallback-south-china-sea",
        "title": "South China Sea typhoon watch",
        "description": "Severe weather may force shipping lanes to slow or reroute over the next 48 hours.",
        "category": "weather",
        "severity": 0.67,
        "type": "warning",
        "locations": ["South China Sea", "Hong Kong", "Shenzhen"],
        "companies": [],
        "timestamp": "2026-04-03T06:00:00Z",
        "source": "fallback",
    },
]

LOCATION_COORDINATES = {
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
    "source_company": ["source_company", "source", "supplier", "from_company", "company_a", "from"],
    "target_company": ["target_company", "target", "customer", "to_company", "company_b", "to"],
    "relationship_type": ["relationship_type", "relationship", "relation", "link_type"],
    "material": ["material", "product", "raw_material", "commodity", "sku"],
    "origin": ["origin", "origin_port", "origin_location", "from_location", "route_from", "source_location"],
    "destination": ["destination", "destination_port", "destination_location", "to_location", "route_to", "target_location"],
    "transport_mode": ["transport_mode", "mode", "shipment_mode", "logistics_mode"],
    "criticality": ["criticality", "priority", "importance", "tier"],
    "route_name": ["route", "route_name", "lane", "trade_route"],
    "origin_lat": ["origin_lat", "from_lat", "source_lat"],
    "origin_lon": ["origin_lon", "from_lon", "source_lon"],
    "destination_lat": ["destination_lat", "to_lat", "target_lat"],
    "destination_lon": ["destination_lon", "to_lon", "target_lon"],
}

CRITICALITY_WEIGHTS = {"high": 1.0, "medium": 0.78, "low": 0.58}
TRANSPORT_KEYWORDS = {
    "sea": ["port", "vessel", "maritime", "shipping", "canal", "terminal"],
    "air": ["airport", "air cargo", "freight", "airline"],
    "road": ["truck", "highway", "road", "border crossing"],
    "rail": ["rail", "train", "intermodal"],
}

SEVERITY_KEYWORDS = {
    "critical": ["block", "blocked", "closure", "closed", "halt", "shutdown", "strike", "sanction", "suspended", "flood", "storm", "collision"],
    "warning": ["delay", "slowdown", "congestion", "watch", "inspection", "shortage", "queue", "cyber"],
}

CATEGORY_KEYWORDS = {
    "weather": ["storm", "typhoon", "cyclone", "rain", "flood", "wind", "weather"],
    "labor": ["labor", "union", "strike"],
    "logistics": ["port", "shipping", "logistics", "freight", "truck", "vessel", "canal"],
    "geopolitical": ["sanction", "tariff", "export control", "border", "conflict", "war"],
    "cyber": ["cyber", "outage", "system", "ransomware"],
    "supply": ["shortage", "factory", "supplier", "mine", "refinery", "production"],
}


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
        os.makedirs(self.storage_dir, exist_ok=True)

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
            raise ValueError("No valid supply-chain routes were found in the uploaded file.")

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
                "source_company": "MineCo Chile",
                "target_company": "RefineCo China",
                "relationship_type": "supplies",
                "material": "Lithium Ore",
                "origin": "Chile",
                "destination": "Shanghai",
                "transport_mode": "sea",
                "criticality": "high",
                "route_name": "Chile to Shanghai lithium lane",
            },
            {
                "source_company": "RefineCo China",
                "target_company": "BatteryCo India",
                "relationship_type": "processes_for",
                "material": "Lithium Cells",
                "origin": "Shanghai",
                "destination": "Mumbai",
                "transport_mode": "sea",
                "criticality": "high",
                "route_name": "Shanghai to Mumbai battery cells",
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
            transport_mode = (normalized.get("transport_mode") or "sea").lower()
            criticality = (normalized.get("criticality") or "medium").lower()
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
                )
            ]
        )

    def _collect_alerts(self, snapshot: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        alerts = []
        source_status = {
            "fallback": {"enabled": True, "live": True},
            "gdelt": {"enabled": True, "live": False},
            "weather": {"enabled": bool(self.weather_api_key), "live": False},
        }

        fallback_alerts = self._filter_fallback_alerts(snapshot)
        alerts.extend(fallback_alerts)

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

    def _filter_fallback_alerts(self, snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        watch_terms = [_norm_lookup(term) for term in snapshot["watch_terms"]]
        relevant = []
        for alert in DEFAULT_DISRUPTIONS:
            haystack = " ".join([alert["title"], alert["description"], *alert.get("locations", [])]).lower()
            if any(term and term in haystack for term in watch_terms):
                relevant.append(dict(alert))
        return relevant if relevant else list(DEFAULT_DISRUPTIONS[:3])

    def _fetch_gdelt_alerts(self, snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        terms = [
            term
            for term in snapshot["watch_terms"]
            if len(term) >= 4 and _norm_lookup(term) not in {"high", "medium", "low", "unspecified"}
        ][:8]
        if not terms:
            return []

        query_terms = " OR ".join(f'"{term}"' for term in terms)
        query = f"({query_terms}) AND (port OR shipping OR logistics OR supplier OR factory OR strike OR storm OR export OR sanctions OR congestion)"
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

        impacted_links = []
        company_scores: Dict[str, Dict[str, Any]] = {}
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

            if not matches:
                continue

            matches.sort(key=lambda item: item["severity"], reverse=True)
            top_risk = matches[0]["severity"]
            status = "blocked" if top_risk >= 0.72 else "at_risk"
            downstream = self._downstream_companies(route["target_company"], adjacency)
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

    def _snapshot_path(self, snapshot_id: str) -> str:
        return os.path.join(self.storage_dir, f"{snapshot_id}.json")

    def _save_snapshot(self, snapshot: Dict[str, Any]) -> None:
        with open(self._snapshot_path(snapshot["snapshot_id"]), "w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, indent=2)
