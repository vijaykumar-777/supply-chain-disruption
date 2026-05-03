import datetime as dt
import uuid
from typing import Any, Dict, Iterable, List, Tuple

import requests

from src.config import OPENWEATHERMAP_API_KEY
from src.relief.reference_data import KARNATAKA_COVERAGE_PLACES, load_reference_data


DISASTER_TERMS = [
    "flood",
    "flooding",
    "landslide",
    "mudslide",
    "heavy rain",
    "red alert",
    "orange alert",
    "road blocked",
    "bridge collapse",
    "waterlogging",
    "dam release",
    "evacuation",
    "rescue",
    "cyclone",
    "storm",
]

CRITICAL_TERMS = {"red alert", "landslide", "bridge collapse", "evacuation", "road blocked", "dam release"}
WARNING_TERMS = {"orange alert", "heavy rain", "flood", "waterlogging", "storm", "rescue"}


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _severity(text: str) -> float:
    lowered = _norm(text)
    score = 0.34
    if any(term in lowered for term in WARNING_TERMS):
        score = max(score, 0.58)
    if any(term in lowered for term in CRITICAL_TERMS):
        score = max(score, 0.82)
    return score


def _category(text: str) -> str:
    lowered = _norm(text)
    if any(term in lowered for term in ("landslide", "mudslide", "slope")):
        return "landslide"
    if any(term in lowered for term in ("flood", "waterlogging", "dam release", "bridge")):
        return "flood"
    if any(term in lowered for term in ("rain", "red alert", "orange alert", "storm", "cyclone")):
        return "weather"
    if any(term in lowered for term in ("road blocked", "traffic", "closure")):
        return "road_access"
    return "disaster"


def _type(severity: float) -> str:
    return "critical" if severity >= 0.75 else "warning" if severity >= 0.45 else "info"


def _chunks(items: List[str], size: int) -> Iterable[List[str]]:
    for index in range(0, len(items), size):
        yield items[index:index + size]


def _locations_from_text(text: str, places: List[str]) -> List[str]:
    lowered = _norm(text)
    return [place for place in places if _norm(place) in lowered][:8]


def _query_gdelt(query: str, maxrecords: int = 20) -> List[Dict[str, Any]]:
    response = requests.get(
        "https://api.gdeltproject.org/api/v2/doc/doc",
        params={
            "query": query,
            "mode": "ArtList",
            "maxrecords": maxrecords,
            "format": "json",
            "sort": "DateDesc",
            "timespan": "7days",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get("articles", [])


def _gdelt_alerts(places: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    status = {"enabled": True, "live": False, "queries": 0, "error": None}
    disaster_query = "(" + " OR ".join(f'"{term}"' for term in DISASTER_TERMS) + ")"
    query_groups = [
        ["Karnataka"],
        ["Kodagu", "Dakshina Kannada", "Udupi", "Uttara Kannada", "Shivamogga", "Chikkamagaluru", "Hassan"],
    ]
    query_groups.extend(list(_chunks(places[:36], 8)))

    alerts: List[Dict[str, Any]] = []
    errors = []
    for group in query_groups[:6]:
        place_query = "(" + " OR ".join(f'"{place}"' for place in group) + ")"
        query = f"{place_query} AND {disaster_query}"
        try:
            status["queries"] += 1
            for article in _query_gdelt(query):
                title = str(article.get("title") or "Live disaster signal").strip()
                domain = str(article.get("domain") or "").strip()
                seen_date = str(article.get("seendate") or "").strip()
                url = article.get("url")
                blob = f"{title} {domain} {url or ''}"
                severity = _severity(blob)
                alerts.append(
                    {
                        "id": f"gdelt-{uuid.uuid4()}",
                        "title": title,
                        "description": f"{domain or 'GDELT'} signal captured {seen_date or _utc_now()}",
                        "category": _category(blob),
                        "severity": severity,
                        "type": _type(severity),
                        "locations": _locations_from_text(blob, places) or group,
                        "timestamp": seen_date or _utc_now(),
                        "source": "gdelt",
                        "url": url,
                        "confidence": 0.62,
                    }
                )
            status["live"] = True
        except Exception as exc:
            errors.append(str(exc))

    if errors and not status["live"]:
        status["error"] = "; ".join(errors[:2])
    elif errors:
        status["error"] = f"Partial coverage: {errors[0]}"
    return alerts, status


def _weather_alerts(reference: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    status = {"enabled": bool(OPENWEATHERMAP_API_KEY), "live": False, "error": None}
    if not OPENWEATHERMAP_API_KEY:
        status["error"] = "OPENWEATHERMAP_API_KEY is not set"
        return [], status

    rows = reference["datasets"].get("villages_at_risk", [])[:8]
    alerts: List[Dict[str, Any]] = []
    errors = []
    for row in rows:
        try:
            response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"lat": row["lat"], "lon": row["lon"], "appid": OPENWEATHERMAP_API_KEY, "units": "metric"},
                timeout=8,
            )
            response.raise_for_status()
            payload = response.json()
            weather = (payload.get("weather") or [{}])[0]
            main = weather.get("main")
            description = weather.get("description") or "current weather"
            wind_speed = float(payload.get("wind", {}).get("speed", 0) or 0)
            severity = 0.0
            if main in {"Thunderstorm", "Tornado", "Squall"}:
                severity = 0.82
            elif main in {"Rain", "Drizzle"} or wind_speed >= 12:
                severity = 0.56
            if severity < 0.45:
                continue
            alerts.append(
                {
                    "id": f"weather-{row['name']}",
                    "title": f"Weather risk near {row['name']}",
                    "description": f"{description}; wind {wind_speed:.1f} m/s",
                    "category": "weather",
                    "severity": severity,
                    "type": _type(severity),
                    "locations": [row["name"], row["district"]],
                    "timestamp": _utc_now(),
                    "source": "openweather",
                    "url": None,
                    "confidence": 0.7,
                }
            )
            status["live"] = True
        except Exception as exc:
            errors.append(str(exc))
    if errors and not status["live"]:
        status["error"] = "; ".join(errors[:2])
    elif errors:
        status["error"] = f"Partial coverage: {errors[0]}"
    return alerts, status


def collect_live_disasters() -> Dict[str, Any]:
    reference = load_reference_data()
    village_places = [row["name"] for row in reference["datasets"].get("villages_at_risk", []) if row.get("name")]
    road_places = []
    for row in reference["datasets"].get("road_network", []):
        road_places.extend([row.get("from", ""), row.get("to", ""), row.get("road_name", "")])
    places = list(dict.fromkeys([*KARNATAKA_COVERAGE_PLACES, *village_places, *road_places]))

    gdelt_alerts, gdelt_status = _gdelt_alerts(places)
    weather_alerts, weather_status = _weather_alerts(reference)

    deduped: List[Dict[str, Any]] = []
    seen = set()
    for alert in sorted([*gdelt_alerts, *weather_alerts], key=lambda item: (item["severity"], item["timestamp"]), reverse=True):
        key = (_norm(alert["title"]), tuple(sorted(alert.get("locations", []))), alert["source"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(alert)

    return {
        "alerts": deduped[:80],
        "count": len(deduped[:80]),
        "source_status": {
            "gdelt": gdelt_status,
            "openweather": weather_status,
        },
        "coverage": {
            "places_tracked": len(places),
            "places_sample": places[:30],
            "disaster_terms": DISASTER_TERMS,
            "policy": "Broad Karnataka disaster query across state, district, road, and village terms. This improves coverage but still depends on source availability and API limits.",
        },
    }
