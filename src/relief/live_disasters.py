import datetime as dt
import csv
import io
import re
import urllib.parse
import uuid
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Iterable, List, Tuple

import requests

from src.config import (
    BING_NEWS_RSS_ENABLED,
    CWC_API_KEY,
    CWC_FLOODWATCH_FEED_URL,
    FREENEWSAPI_BASE_URL,
    FREENEWSAPI_KEY,
    GNEWS_API_KEY,
    GNEWS_BASE_URL,
    GOOGLE_NEWS_RSS_ENABLED,
    GUARDIAN_API_KEY,
    GUARDIAN_BASE_URL,
    IMD_ALERT_FEED_URL,
    IMD_API_KEY,
    KSDMA_API_KEY,
    KSDMA_BULLETIN_FEED_URL,
    KSNDMC_API_KEY,
    KSNDMC_RAINFALL_FEED_URL,
    MEDIASTACK_API_KEY,
    MEDIASTACK_BASE_URL,
    NEWSDATA_API_KEY,
    NEWSDATA_BASE_URL,
    NEWS_LOOKBACK_DAYS,
    NEWSAPI_BASE_URL,
    NEWSAPI_KEY,
    OPENWEATHERMAP_API_KEY,
    PIB_RSS_URL,
    THENEWSAPI_BASE_URL,
    THENEWSAPI_TOKEN,
    WORLDNEWSAPI_BASE_URL,
    WORLDNEWSAPI_KEY,
)
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

KARNATAKA_NEWS_QUERY_PLACES = [
    "Karnataka",
    "Bengaluru",
    "Kodagu",
    "Dakshina Kannada",
    "Mangaluru",
    "Udupi",
    "Uttara Kannada",
    "Karwar",
    "Shivamogga",
    "Chikkamagaluru",
    "Hassan",
    "Shiradi Ghat",
    "Belagavi",
    "Raichur",
    "Yadgir",
]

NEWS_SIGNAL_TERMS = [
    *DISASTER_TERMS,
    "rainfall",
    "yellow alert",
    "nowcast",
    "thunderstorm",
    "lightning",
    "cloudburst",
    "river overflow",
    "water level",
    "reservoir",
    "dam discharge",
    "bridge washed",
    "road closure",
    "traffic diversion",
    "tree fall",
    "power outage",
    "school holiday",
    "relief camp",
    "NDRF",
    "SDRF",
    "fire service",
]

CORE_NEWS_TERMS = {
    "flood",
    "flooding",
    "landslide",
    "mudslide",
    "heavy rain",
    "rainfall",
    "red alert",
    "orange alert",
    "yellow alert",
    "nowcast",
    "thunderstorm",
    "lightning",
    "cloudburst",
    "waterlogging",
    "river overflow",
    "water level",
    "reservoir",
    "dam release",
    "dam discharge",
    "road blocked",
    "road closure",
    "traffic diversion",
    "bridge collapse",
    "bridge washed",
    "tree fall",
    "power outage",
    "relief camp",
    "ndrf",
    "sdrf",
}
GENERIC_EMERGENCY_TERMS = {"evacuation", "rescue", "fire service", "school holiday"}
NOISE_PHRASES = {
    "energy evacuation",
    "power evacuation",
    "renewable energy evacuation",
    "custody",
    "prostitution",
    "stranded in west asia",
    "wayanad",
    "meppadi",
}

CRITICAL_TERMS = {"red alert", "landslide", "bridge collapse", "evacuation", "road blocked", "dam release", "cloudburst", "bridge washed"}
WARNING_TERMS = {"orange alert", "yellow alert", "heavy rain", "rainfall", "flood", "waterlogging", "storm", "rescue", "traffic diversion"}
STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _strip_html(value: Any) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def _status(enabled: bool, error: str | None = None) -> Dict[str, Any]:
    return {"enabled": enabled, "live": False, "queries": 0, "returned": 0, "error": error}


def _token_set(value: Any) -> set[str]:
    headline = re.split(r"\s[-|]\s", _strip_html(value), maxsplit=1)[0]
    words = re.findall(r"[a-z0-9]+", _norm(headline))
    return {word for word in words if len(word) > 2 and word not in STOPWORDS}


def _canonical_url(url: Any) -> str:
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(str(url).strip())
        host = parsed.netloc.lower().removeprefix("www.")
        path = re.sub(r"/+$", "", parsed.path)
        return f"{host}{path}".lower()
    except Exception:
        return str(url).strip().lower()


def _parse_timestamp(value: Any) -> dt.datetime:
    if isinstance(value, dt.datetime):
        return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)
    text = str(value or "").strip()
    if not text:
        return dt.datetime.fromtimestamp(0, tz=dt.timezone.utc)
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        pass
    try:
        parsed = parsedate_to_datetime(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
    except Exception:
        return dt.datetime.fromtimestamp(0, tz=dt.timezone.utc)


def _sort_key(alert: Dict[str, Any]) -> Tuple[float, dt.datetime]:
    return float(alert.get("severity", 0) or 0), _parse_timestamp(alert.get("timestamp"))


def _within_news_lookback(value: Any) -> bool:
    parsed = _parse_timestamp(value)
    if parsed.timestamp() <= 0:
        return True
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=NEWS_LOOKBACK_DAYS)
    return parsed >= cutoff


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


def _provider_query() -> str:
    place_query = " OR ".join(f'"{place}"' for place in KARNATAKA_NEWS_QUERY_PLACES[:10])
    signal_query = " OR ".join(f'"{term}"' for term in NEWS_SIGNAL_TERMS[:18])
    return f"({place_query}) AND ({signal_query})"


def _rss_query_variants() -> List[str]:
    return [
        'Karnataka (flood OR landslide OR "heavy rain" OR waterlogging OR "road blocked" OR evacuation OR rescue)',
        '("Kodagu" OR "Dakshina Kannada" OR Udupi OR "Uttara Kannada" OR Mangaluru OR Karwar) (rainfall OR flood OR landslide OR waterlogging)',
        '("Western Ghats" OR "Shiradi Ghat" OR Sakleshpur OR Chikkamagaluru OR Shivamogga) (landslide OR "road closure" OR "heavy rain")',
        '(Belagavi OR Raichur OR Yadgir OR Bagalkot OR Vijayapura) (flood OR "dam release" OR "river overflow" OR rainfall)',
    ]


def _karnataka_relevant(text: str, places: List[str]) -> bool:
    lowered = _norm(text)
    if "karnataka" in lowered:
        return True
    place_hits = _locations_from_text(text, places)
    return bool(place_hits)


def _disaster_relevant(text: str) -> bool:
    lowered = _norm(text)
    if any(phrase in lowered for phrase in NOISE_PHRASES):
        return False
    if any(term in lowered for term in CORE_NEWS_TERMS):
        return True
    return any(term in lowered for term in GENERIC_EMERGENCY_TERMS) and any(
        context in lowered for context in ("disaster", "flood", "landslide", "rain", "storm", "ndrf", "sdrf", "relief")
    )


def _news_relevant(item: Dict[str, Any], places: List[str]) -> bool:
    text = " ".join(str(value or "") for value in item.values())
    return _karnataka_relevant(text, places) and _disaster_relevant(text)


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


def _first_text(item: Dict[str, Any], keys: Tuple[str, ...], default: str = "") -> str:
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            value = ", ".join(str(part) for part in value if part)
        cleaned = str(value).strip()
        if cleaned:
            return cleaned
    return default


def _feed_items(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = []
        for key in ("alerts", "warnings", "bulletins", "incidents", "articles", "items", "features", "data", "records", "results"):
            candidate = payload.get(key)
            if isinstance(candidate, list):
                items = candidate
                break
        if not items:
            items = [payload]
    else:
        return []

    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("properties"), dict):
            merged = {**item["properties"], "geometry": item.get("geometry")}
            normalized.append(merged)
        else:
            normalized.append(item)
    return normalized


def _xml_child_text(parent: ET.Element, names: Tuple[str, ...]) -> str:
    wanted = {name.lower() for name in names}
    for child in list(parent):
        tag = child.tag.split("}", 1)[-1].lower()
        if tag in wanted:
            if tag == "link" and child.attrib.get("href"):
                return child.attrib["href"].strip()
            return "".join(child.itertext()).strip()
    return ""


def _parse_rss_items(xml_text: str) -> List[Dict[str, Any]]:
    root = ET.fromstring(xml_text)
    items = []
    for element in root.iter():
        tag = element.tag.split("}", 1)[-1].lower()
        if tag not in {"item", "entry"}:
            continue
        source = _xml_child_text(element, ("source",))
        item = {
            "title": _strip_html(_xml_child_text(element, ("title",))),
            "description": _strip_html(_xml_child_text(element, ("description", "summary", "content", "encoded"))),
            "url": _xml_child_text(element, ("link", "guid", "id")),
            "published_at": _xml_child_text(element, ("pubDate", "published", "updated", "dc:date")),
            "source": source,
        }
        if item["title"]:
            items.append(item)
    return items


def _parse_csv_items(text: str) -> List[Dict[str, Any]]:
    rows = list(csv.DictReader(io.StringIO(text)))
    return [dict(row) for row in rows]


def _parse_feed_response(response: requests.Response) -> List[Dict[str, Any]]:
    content_type = response.headers.get("content-type", "").lower()
    text = response.content.decode("utf-8-sig", errors="replace")
    if "json" in content_type:
        return _feed_items(response.json())
    if "csv" in content_type or text.lstrip().lower().startswith(("district,", "date,", "timestamp,", "title,")):
        return _parse_csv_items(text)
    if "xml" in content_type or "<rss" in text[:500].lower() or "<feed" in text[:500].lower():
        return _parse_rss_items(text)
    try:
        return _feed_items(response.json())
    except ValueError:
        pass
    try:
        return _parse_rss_items(text)
    except Exception:
        return [{"title": "Official disaster bulletin", "description": text[:700], "published_at": _utc_now()}]


def _news_alert_from_item(source: str, item: Dict[str, Any], places: List[str], confidence: float) -> Dict[str, Any] | None:
    if not _news_relevant(item, places):
        return None
    alert = _alert_from_feed_item(source, item, places, confidence)
    if not _within_news_lookback(alert.get("timestamp")):
        return None
    alert["sources"] = [source]
    alert["duplicate_count"] = 1
    return alert


def _request_json(source: str, url: str, status: Dict[str, Any], **kwargs: Any) -> Any:
    status["queries"] += 1
    response = requests.get(url, timeout=10, **kwargs)
    response.raise_for_status()
    return response.json()


def _location_values(item: Dict[str, Any], places: List[str]) -> List[str]:
    raw_values = []
    for key in ("locations", "location", "district", "district_name", "area", "place", "village", "taluk", "road_name", "river", "station"):
        value = item.get(key)
        if isinstance(value, list):
            raw_values.extend(str(part) for part in value if part)
        elif value:
            raw_values.append(str(value))

    blob = " ".join(raw_values + [str(item)])
    matched = _locations_from_text(blob, places)
    return list(dict.fromkeys([*raw_values, *matched]))[:8] or ["Karnataka"]


def _severity_from_item(item: Dict[str, Any], text: str) -> float:
    value = item.get("severity") or item.get("risk") or item.get("level") or item.get("alert_level")
    if isinstance(value, (int, float)):
        return max(0.0, min(float(value), 1.0))
    normalized = _norm(value)
    if any(term in normalized for term in ("red", "critical", "severe", "extreme", "danger", "closed", "blocked")):
        return 0.86
    if any(term in normalized for term in ("orange", "high", "warning", "watch")):
        return 0.64
    if any(term in normalized for term in ("yellow", "moderate", "advisory")):
        return 0.46
    return _severity(text)


def _alert_from_feed_item(source: str, item: Dict[str, Any], places: List[str], confidence: float) -> Dict[str, Any]:
    title = _first_text(
        item,
        ("title", "headline", "event", "warning", "alert", "subject", "name", "road_name", "webTitle"),
        "Official disaster signal",
    )
    description = _first_text(
        item,
        ("description", "summary", "snippet", "subtitle", "message", "text", "details", "reason", "body", "content", "main_text"),
        source,
    )
    blob = f"{title} {description} {item}"
    severity = _severity_from_item(item, blob)
    return {
        "id": f"{source}-{uuid.uuid4()}",
        "title": title,
        "description": description,
        "category": _category(blob),
        "severity": severity,
        "type": _type(severity),
        "locations": _location_values(item, places),
        "timestamp": _first_text(
            item,
            ("timestamp", "reported_at", "publishedAt", "published_at", "published_date", "published_on", "pubDate", "issue_time", "issued_at", "time", "date", "webPublicationDate"),
            _utc_now(),
        ),
        "source": source,
        "url": _first_text(item, ("url", "link", "source_url", "web_url", "webUrl", "uri", "article_url"), None),
        "confidence": confidence,
    }


def _configured_json_feed_alerts(
    source: str,
    feed_url: str | None,
    api_key: str | None,
    places: List[str],
    confidence: float,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    status = {"enabled": bool(feed_url), "live": False, "queries": 0, "returned": 0, "error": None}
    if not feed_url:
        status["error"] = f"{source.upper()} feed URL is not set"
        return [], status

    headers = {"Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        status["queries"] = 1
        response = requests.get(feed_url, headers=headers, timeout=10)
        response.raise_for_status()
        alerts = []
        for item in _parse_feed_response(response):
            alert = _alert_from_feed_item(source, item, places, confidence)
            if _karnataka_relevant(f"{alert['title']} {alert['description']} {' '.join(alert.get('locations', []))}", places):
                alerts.append(alert)
        status["returned"] = len(alerts)
        status["live"] = True
        return alerts, status
    except Exception as exc:
        status["error"] = str(exc)
        return [], status


def _newsapi_alerts(places: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    status = _status(bool(NEWSAPI_KEY))
    if not NEWSAPI_KEY:
        status["error"] = "NEWSAPI_KEY is not set"
        return [], status

    query = _provider_query()
    try:
        payload = _request_json(
            "newsapi",
            NEWSAPI_BASE_URL,
            status,
            params={
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 100,
                "apiKey": NEWSAPI_KEY,
            },
        )
        alerts = [
            alert
            for article in payload.get("articles", [])
            if isinstance(article, dict)
            for alert in [_news_alert_from_item("newsapi", article, places, 0.6)]
            if alert
        ]
        status["returned"] = len(alerts)
        status["live"] = True
        return alerts, status
    except Exception as exc:
        status["error"] = str(exc)
        return [], status


def _newsdata_alerts(places: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    status = _status(bool(NEWSDATA_API_KEY))
    if not NEWSDATA_API_KEY:
        status["error"] = "NEWSDATA_API_KEY is not set"
        return [], status

    try:
        payload = _request_json(
            "newsdata",
            NEWSDATA_BASE_URL,
            status,
            params={
                "apikey": NEWSDATA_API_KEY,
                "q": _provider_query(),
                "country": "in",
                "language": "en,kn",
            },
        )
        alerts = [
            alert
            for article in payload.get("results", [])
            if isinstance(article, dict)
            for alert in [_news_alert_from_item("newsdata", article, places, 0.62)]
            if alert
        ]
        status["returned"] = len(alerts)
        status["live"] = True
        return alerts, status
    except Exception as exc:
        status["error"] = str(exc)
        return [], status


def _thenewsapi_alerts(places: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    status = _status(bool(THENEWSAPI_TOKEN))
    if not THENEWSAPI_TOKEN:
        status["error"] = "THENEWSAPI_TOKEN is not set"
        return [], status

    try:
        payload = _request_json(
            "thenewsapi",
            THENEWSAPI_BASE_URL,
            status,
            params={
                "api_token": THENEWSAPI_TOKEN,
                "search": _provider_query(),
                "search_fields": "title,description,keywords,main_text",
                "locale": "in",
                "language": "en",
                "limit": 50,
                "sort": "published_at",
            },
        )
        alerts = [
            alert
            for article in payload.get("data", [])
            if isinstance(article, dict)
            for alert in [_news_alert_from_item("thenewsapi", article, places, 0.62)]
            if alert
        ]
        status["returned"] = len(alerts)
        status["live"] = True
        return alerts, status
    except Exception as exc:
        status["error"] = str(exc)
        return [], status


def _mediastack_alerts(places: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    status = _status(bool(MEDIASTACK_API_KEY))
    if not MEDIASTACK_API_KEY:
        status["error"] = "MEDIASTACK_API_KEY is not set"
        return [], status

    try:
        payload = _request_json(
            "mediastack",
            MEDIASTACK_BASE_URL,
            status,
            params={
                "access_key": MEDIASTACK_API_KEY,
                "keywords": "Karnataka flood landslide rainfall waterlogging road blocked rescue",
                "countries": "in",
                "languages": "en",
                "limit": 100,
                "sort": "published_desc",
            },
        )
        alerts = [
            alert
            for article in payload.get("data", [])
            if isinstance(article, dict)
            for alert in [_news_alert_from_item("mediastack", article, places, 0.58)]
            if alert
        ]
        status["returned"] = len(alerts)
        status["live"] = True
        return alerts, status
    except Exception as exc:
        status["error"] = str(exc)
        return [], status


def _gnews_alerts(places: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    status = _status(bool(GNEWS_API_KEY))
    if not GNEWS_API_KEY:
        status["error"] = "GNEWS_API_KEY is not set"
        return [], status

    try:
        payload = _request_json(
            "gnews",
            GNEWS_BASE_URL,
            status,
            params={
                "q": _provider_query(),
                "lang": "en",
                "country": "in",
                "max": 10,
                "apikey": GNEWS_API_KEY,
            },
        )
        alerts = [
            alert
            for article in payload.get("articles", [])
            if isinstance(article, dict)
            for alert in [_news_alert_from_item("gnews", article, places, 0.58)]
            if alert
        ]
        status["returned"] = len(alerts)
        status["live"] = True
        return alerts, status
    except Exception as exc:
        status["error"] = str(exc)
        return [], status


def _worldnewsapi_alerts(places: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    status = _status(bool(WORLDNEWSAPI_KEY))
    if not WORLDNEWSAPI_KEY:
        status["error"] = "WORLDNEWSAPI_KEY is not set"
        return [], status

    try:
        payload = _request_json(
            "worldnewsapi",
            WORLDNEWSAPI_BASE_URL,
            status,
            params={
                "api-key": WORLDNEWSAPI_KEY,
                "text": _provider_query(),
                "source-countries": "in",
                "language": "en",
                "number": 50,
                "sort": "publish-time",
                "sort-direction": "DESC",
            },
        )
        rows = payload.get("news") or payload.get("articles") or []
        alerts = [
            alert
            for article in rows
            if isinstance(article, dict)
            for alert in [_news_alert_from_item("worldnewsapi", article, places, 0.58)]
            if alert
        ]
        status["returned"] = len(alerts)
        status["live"] = True
        return alerts, status
    except Exception as exc:
        status["error"] = str(exc)
        return [], status


def _freenewsapi_alerts(places: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    status = _status(bool(FREENEWSAPI_KEY))
    if not FREENEWSAPI_KEY:
        status["error"] = "FREENEWSAPI_KEY is not set"
        return [], status

    try:
        payload = _request_json(
            "freenewsapi",
            FREENEWSAPI_BASE_URL,
            status,
            headers={"Authorization": f"Bearer {FREENEWSAPI_KEY}"},
            params={
                "api_key": FREENEWSAPI_KEY,
                "language": "en",
                "country": "in",
                "q": "Karnataka flood landslide rainfall waterlogging road blocked rescue",
                "page_size": 50,
            },
        )
        rows = payload.get("data") or payload.get("results") or payload.get("articles") or []
        alerts = [
            alert
            for article in rows
            if isinstance(article, dict)
            for alert in [_news_alert_from_item("freenewsapi", article, places, 0.58)]
            if alert
        ]
        status["returned"] = len(alerts)
        status["live"] = True
        return alerts, status
    except Exception as exc:
        status["error"] = str(exc)
        return [], status


def _guardian_alerts(places: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    status = _status(bool(GUARDIAN_API_KEY))
    if not GUARDIAN_API_KEY:
        status["error"] = "GUARDIAN_API_KEY is not set"
        return [], status

    try:
        payload = _request_json(
            "guardian",
            GUARDIAN_BASE_URL,
            status,
            params={
                "api-key": GUARDIAN_API_KEY,
                "q": _provider_query(),
                "order-by": "newest",
                "page-size": 50,
                "show-fields": "trailText,bodyText",
            },
        )
        rows = payload.get("response", {}).get("results", [])
        normalized_rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
            normalized_rows.append({**row, "description": fields.get("trailText") or fields.get("bodyText")})
        alerts = [
            alert
            for article in normalized_rows
            for alert in [_news_alert_from_item("guardian", article, places, 0.56)]
            if alert
        ]
        status["returned"] = len(alerts)
        status["live"] = True
        return alerts, status
    except Exception as exc:
        status["error"] = str(exc)
        return [], status


def _rss_alerts(source: str, urls: List[str], places: List[str], confidence: float) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    status = _status(bool(urls))
    if not urls:
        status["error"] = f"{source} RSS feed is not configured"
        return [], status

    alerts: List[Dict[str, Any]] = []
    errors = []
    for url in urls:
        try:
            status["queries"] += 1
            response = requests.get(
                url,
                headers={"User-Agent": "reliefroute-karnataka/1.0 news-risk-monitor"},
                timeout=10,
            )
            response.raise_for_status()
            xml_text = response.content.decode("utf-8-sig", errors="replace")
            for item in _parse_rss_items(xml_text):
                alert = _news_alert_from_item(source, item, places, confidence)
                if alert:
                    alerts.append(alert)
            status["live"] = True
        except Exception as exc:
            errors.append(str(exc))

    status["returned"] = len(alerts)
    if errors and not status["live"]:
        status["error"] = "; ".join(errors[:2])
    elif errors:
        status["error"] = f"Partial coverage: {errors[0]}"
    return alerts, status


def _google_news_rss_alerts(places: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not GOOGLE_NEWS_RSS_ENABLED:
        return [], _status(False, "GOOGLE_NEWS_RSS_ENABLED=false")
    urls = [
        "https://news.google.com/rss/search?"
        + urllib.parse.urlencode({"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})
        for query in _rss_query_variants()
    ]
    return _rss_alerts("google_news_rss", urls, places, 0.55)


def _bing_news_rss_alerts(places: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not BING_NEWS_RSS_ENABLED:
        return [], _status(False, "BING_NEWS_RSS_ENABLED=false")
    urls = [
        "https://www.bing.com/news/search?"
        + urllib.parse.urlencode({"q": query, "format": "rss", "cc": "IN", "setlang": "en-IN"})
        for query in _rss_query_variants()
    ]
    return _rss_alerts("bing_news_rss", urls, places, 0.52)


def _pib_rss_alerts(places: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not PIB_RSS_URL:
        return [], _status(False, "PIB_RSS_URL is not set")
    return _rss_alerts("pib_rss", [PIB_RSS_URL], places, 0.68)


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
            status["live"] = True
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
        except Exception as exc:
            errors.append(str(exc))
    if errors and not status["live"]:
        status["error"] = "; ".join(errors[:2])
    elif errors:
        status["error"] = f"Partial coverage: {errors[0]}"
    return alerts, status


def _is_duplicate(existing: Dict[str, Any], incoming: Dict[str, Any]) -> bool:
    existing_url = _canonical_url(existing.get("url"))
    incoming_url = _canonical_url(incoming.get("url"))
    if existing_url and incoming_url and existing_url == incoming_url:
        return True

    existing_tokens = _token_set(existing.get("title"))
    incoming_tokens = _token_set(incoming.get("title"))
    if not existing_tokens or not incoming_tokens:
        return False
    overlap = len(existing_tokens & incoming_tokens) / max(len(existing_tokens | incoming_tokens), 1)
    existing_locations = {_norm(location) for location in existing.get("locations", [])}
    incoming_locations = {_norm(location) for location in incoming.get("locations", [])}
    location_overlap = not existing_locations or not incoming_locations or bool(existing_locations & incoming_locations)
    if overlap >= 0.78:
        return location_overlap

    same_category = existing.get("category") == incoming.get("category")
    days_apart = abs((_parse_timestamp(existing.get("timestamp")) - _parse_timestamp(incoming.get("timestamp"))).days)
    return overlap >= 0.35 and same_category and location_overlap and days_apart <= 7


def _merge_duplicate(existing: Dict[str, Any], incoming: Dict[str, Any]) -> None:
    sources = list(dict.fromkeys([*(existing.get("sources") or [existing.get("source")]), *(incoming.get("sources") or [incoming.get("source")])]))
    existing["sources"] = [source for source in sources if source]
    existing["duplicate_count"] = len(existing["sources"])
    existing["locations"] = list(dict.fromkeys([*existing.get("locations", []), *incoming.get("locations", [])]))[:10]
    existing["confidence"] = max(float(existing.get("confidence", 0) or 0), float(incoming.get("confidence", 0) or 0))
    if float(incoming.get("severity", 0) or 0) > float(existing.get("severity", 0) or 0):
        existing["severity"] = incoming["severity"]
        existing["type"] = incoming["type"]
    evidence_urls = list(dict.fromkeys([*(existing.get("evidence_urls") or []), existing.get("url"), incoming.get("url")]))
    existing["evidence_urls"] = [url for url in evidence_urls if url][:6]


def _dedupe_alerts(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: List[Dict[str, Any]] = []
    for alert in sorted(alerts, key=_sort_key, reverse=True):
        alert.setdefault("sources", [alert.get("source")])
        alert.setdefault("duplicate_count", 1)
        match = next((existing for existing in deduped if _is_duplicate(existing, alert)), None)
        if match:
            _merge_duplicate(match, alert)
            continue
        deduped.append(alert)
    return deduped


def collect_live_disasters() -> Dict[str, Any]:
    reference = load_reference_data()
    village_places = [row["name"] for row in reference["datasets"].get("villages_at_risk", []) if row.get("name")]
    road_places = []
    for row in reference["datasets"].get("road_network", []):
        road_places.extend([row.get("from", ""), row.get("to", "")])
        road_name = str(row.get("road_name", "")).strip()
        if len(road_name) >= 4 and road_name.lower() not in {"road", "route"}:
            road_places.append(road_name)
    places = list(dict.fromkeys([*KARNATAKA_COVERAGE_PLACES, *village_places, *road_places]))

    gdelt_alerts, gdelt_status = _gdelt_alerts(places)
    google_alerts, google_status = _google_news_rss_alerts(places)
    bing_alerts, bing_status = _bing_news_rss_alerts(places)
    pib_alerts, pib_status = _pib_rss_alerts(places)
    weather_alerts, weather_status = _weather_alerts(reference)
    imd_alerts, imd_status = _configured_json_feed_alerts("imd", IMD_ALERT_FEED_URL, IMD_API_KEY, places, 0.82)
    ksndmc_alerts, ksndmc_status = _configured_json_feed_alerts(
        "ksndmc",
        KSNDMC_RAINFALL_FEED_URL,
        KSNDMC_API_KEY,
        places,
        0.85,
    )
    ksdma_alerts, ksdma_status = _configured_json_feed_alerts(
        "ksdma",
        KSDMA_BULLETIN_FEED_URL,
        KSDMA_API_KEY,
        places,
        0.88,
    )
    cwc_alerts, cwc_status = _configured_json_feed_alerts(
        "cwc",
        CWC_FLOODWATCH_FEED_URL,
        CWC_API_KEY,
        places,
        0.8,
    )
    newsapi_alerts, newsapi_status = _newsapi_alerts(places)
    newsdata_alerts, newsdata_status = _newsdata_alerts(places)
    thenewsapi_alerts, thenewsapi_status = _thenewsapi_alerts(places)
    mediastack_alerts, mediastack_status = _mediastack_alerts(places)
    gnews_alerts, gnews_status = _gnews_alerts(places)
    worldnewsapi_alerts, worldnewsapi_status = _worldnewsapi_alerts(places)
    freenewsapi_alerts, freenewsapi_status = _freenewsapi_alerts(places)
    guardian_alerts, guardian_status = _guardian_alerts(places)

    all_alerts = [
        *ksdma_alerts,
        *ksndmc_alerts,
        *imd_alerts,
        *cwc_alerts,
        *weather_alerts,
        *gdelt_alerts,
        *google_alerts,
        *bing_alerts,
        *pib_alerts,
        *newsapi_alerts,
        *newsdata_alerts,
        *thenewsapi_alerts,
        *mediastack_alerts,
        *gnews_alerts,
        *worldnewsapi_alerts,
        *freenewsapi_alerts,
        *guardian_alerts,
    ]
    deduped = _dedupe_alerts(all_alerts)

    return {
        "alerts": deduped[:120],
        "count": len(deduped[:120]),
        "raw_count": len(all_alerts),
        "duplicate_count": max(len(all_alerts) - len(deduped), 0),
        "source_status": {
            "ksdma": ksdma_status,
            "ksndmc": ksndmc_status,
            "imd": imd_status,
            "cwc": cwc_status,
            "gdelt": gdelt_status,
            "google_news_rss": google_status,
            "bing_news_rss": bing_status,
            "pib_rss": pib_status,
            "openweather": weather_status,
            "newsapi": newsapi_status,
            "newsdata": newsdata_status,
            "thenewsapi": thenewsapi_status,
            "mediastack": mediastack_status,
            "gnews": gnews_status,
            "worldnewsapi": worldnewsapi_status,
            "freenewsapi": freenewsapi_status,
            "guardian": guardian_status,
        },
        "coverage": {
            "places_tracked": len(places),
            "places_sample": places[:30],
            "disaster_terms": DISASTER_TERMS,
            "news_lookback_days": NEWS_LOOKBACK_DAYS,
            "news_sources": [
                "GDELT",
                "Google News RSS",
                "Bing News RSS",
                "PIB RSS",
                "NewsAPI",
                "NewsData.io",
                "TheNewsAPI",
                "Mediastack",
                "GNews",
                "World News API",
                "FreeNewsApi.io",
                "The Guardian Open Platform",
            ],
            "deduplication_policy": "Articles are matched by canonical URL first, then by normalized title token overlap and overlapping Karnataka locations.",
            "policy": "Karnataka-first disaster scan across official feeds, weather, public news aggregators, RSS search feeds, state/district terms, road names, and village names. Simulated operational CSVs are never merged into live alert results.",
        },
    }
