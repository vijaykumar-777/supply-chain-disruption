import csv
import os
from typing import Any, Dict, List


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REFERENCE_FILES = {
    "road_network": "01_road_network.csv",
    "relief_hubs": "02_relief_hubs.csv",
    "villages_at_risk": "03_villages_at_risk.csv",
    "historical_disaster_points": "04_historical_disaster_points.csv",
    "rainfall_thresholds": "05_rainfall_thresholds.csv",
    "vehicle_rules": "06_vehicle_rules.csv",
    "priority_logic": "07_priority_logic.csv",
    "hub_inventory_simulated": "08_hub_inventory_simulated.csv",
    "truck_fleet_simulated": "09_truck_fleet_simulated.csv",
    "blocked_roads_simulated": "10_blocked_roads_simulated.csv",
    "village_relief_demand_simulated": "11_village_relief_demand_simulated.csv",
    "field_reports_simulated": "12_field_reports_simulated.csv",
    "rescue_teams_simulated": "13_rescue_teams_simulated.csv",
    "road_passability_rules_simulated": "14_road_passability_rules_simulated.csv",
    "external_api_sources_placeholder": "15_external_api_sources_placeholder.csv",
}

DATA_PROVENANCE = {
    "road_network": "curated_reference",
    "relief_hubs": "curated_reference",
    "villages_at_risk": "curated_reference",
    "historical_disaster_points": "curated_reference",
    "rainfall_thresholds": "curated_reference",
    "vehicle_rules": "curated_reference",
    "priority_logic": "curated_reference",
    "hub_inventory_simulated": "simulated_operational",
    "truck_fleet_simulated": "simulated_operational",
    "blocked_roads_simulated": "simulated_operational",
    "village_relief_demand_simulated": "simulated_operational",
    "field_reports_simulated": "simulated_operational",
    "rescue_teams_simulated": "simulated_operational",
    "road_passability_rules_simulated": "simulated_operational",
    "external_api_sources_placeholder": "integration_placeholder",
}

REQUIRED_LIVE_INTEGRATIONS = [
    {
        "name": "OpenWeatherMap",
        "env_vars": ["OPENWEATHERMAP_API_KEY"],
        "purpose": "Current weather near villages and road endpoints.",
        "required_for_mvp": True,
    },
    {
        "name": "IMD Alerts",
        "env_vars": ["IMD_ALERT_FEED_URL", "IMD_API_KEY"],
        "purpose": "Official heavy-rain, red/orange alert, and cyclone bulletins.",
        "required_for_mvp": True,
    },
    {
        "name": "KSNDMC Rainfall",
        "env_vars": ["KSNDMC_RAINFALL_FEED_URL", "KSNDMC_API_KEY"],
        "purpose": "Karnataka station rainfall and district warning feeds.",
        "required_for_mvp": True,
    },
    {
        "name": "KSDMA Bulletins",
        "env_vars": ["KSDMA_BULLETIN_FEED_URL", "KSDMA_API_KEY"],
        "purpose": "Official state disaster-management bulletins and incident confirmations.",
        "required_for_mvp": True,
    },
    {
        "name": "CWC FloodWatch",
        "env_vars": ["CWC_FLOODWATCH_FEED_URL", "CWC_API_KEY"],
        "purpose": "River flood forecasts, reservoir releases, and dam-discharge alerts.",
        "required_for_mvp": False,
    },
    {
        "name": "NewsAPI",
        "env_vars": ["NEWSAPI_KEY"],
        "purpose": "Backup local-news scan when GDELT is rate-limited.",
        "required_for_mvp": False,
    },
    {
        "name": "NewsData.io",
        "env_vars": ["NEWSDATA_API_KEY"],
        "purpose": "India/Karnataka news search with country and language filters.",
        "required_for_mvp": False,
    },
    {
        "name": "TheNewsAPI",
        "env_vars": ["THENEWSAPI_TOKEN"],
        "purpose": "Worldwide news search with India locale filtering.",
        "required_for_mvp": False,
    },
    {
        "name": "Mediastack",
        "env_vars": ["MEDIASTACK_API_KEY"],
        "purpose": "Additional global news search layer with country/language filters.",
        "required_for_mvp": False,
    },
    {
        "name": "GNews",
        "env_vars": ["GNEWS_API_KEY"],
        "purpose": "Extra Google-News-style article search coverage.",
        "required_for_mvp": False,
    },
    {
        "name": "World News API",
        "env_vars": ["WORLDNEWSAPI_KEY"],
        "purpose": "Additional global news search with source-country filtering.",
        "required_for_mvp": False,
    },
    {
        "name": "FreeNewsApi.io",
        "env_vars": ["FREENEWSAPI_KEY"],
        "purpose": "High-quota free news source for country/language/text searches.",
        "required_for_mvp": False,
    },
    {
        "name": "The Guardian Open Platform",
        "env_vars": ["GUARDIAN_API_KEY"],
        "purpose": "International coverage for India/Karnataka disaster articles.",
        "required_for_mvp": False,
    },
    {
        "name": "OSRM",
        "env_vars": ["OSRM_BASE_URL"],
        "purpose": "Real road route geometry and ETA calculation.",
        "required_for_mvp": False,
    },
]

KARNATAKA_COVERAGE_PLACES = [
    "Karnataka",
    "Kodagu",
    "Madikeri",
    "Bhagamandala",
    "Napoklu",
    "Virajpet",
    "Ponnampet",
    "Dakshina Kannada",
    "Mangaluru",
    "Shiradi Ghat",
    "Udupi",
    "Kundapura",
    "Kollur",
    "Uttara Kannada",
    "Karwar",
    "Honnavar",
    "Kumta",
    "Ankola",
    "Shivamogga",
    "Sagara",
    "Agumbe",
    "Thirthahalli",
    "Chikkamagaluru",
    "Sakleshpur",
    "Hassan",
    "Belagavi",
    "Vijayapura",
    "Bagalkot",
    "Raichur",
    "Kalburgi",
    "Yadgir",
    "Mysuru",
    "Mandya",
]


def _path(filename: str) -> str:
    return os.path.join(PROJECT_ROOT, filename)


def read_csv_rows(filename: str) -> List[Dict[str, str]]:
    path = _path(filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_reference_data() -> Dict[str, Any]:
    datasets = {name: read_csv_rows(filename) for name, filename in REFERENCE_FILES.items()}
    return {
        "datasets": datasets,
        "counts": {name: len(rows) for name, rows in datasets.items()},
        "files": REFERENCE_FILES,
        "provenance": DATA_PROVENANCE,
        "required_live_integrations": REQUIRED_LIVE_INTEGRATIONS,
        "coverage_places": KARNATAKA_COVERAGE_PLACES,
    }


def road_network_bytes() -> bytes:
    path = _path(REFERENCE_FILES["road_network"])
    if not os.path.exists(path):
        raise FileNotFoundError(REFERENCE_FILES["road_network"])
    with open(path, "rb") as handle:
        return handle.read()
