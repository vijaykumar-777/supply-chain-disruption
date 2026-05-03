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
}

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
        "coverage_places": KARNATAKA_COVERAGE_PLACES,
    }


def road_network_bytes() -> bytes:
    path = _path(REFERENCE_FILES["road_network"])
    if not os.path.exists(path):
        raise FileNotFoundError(REFERENCE_FILES["road_network"])
    with open(path, "rb") as handle:
        return handle.read()
