"""
Generate Disaster Alerts for Karnataka
"""
import json
import random
import uuid
import datetime
from pathlib import Path

RANDOM_SEED = 20260509

# District coordinates for disaster placement
DISTRICT_CENTERS = {
    "Bengaluru Urban": (12.9716, 77.5946),
    "Mysuru": (12.2958, 76.6394),
    "Hubballi": (15.3647, 75.1240),
    "Belagavi": (15.8497, 74.4977),
    "Mangaluru": (12.9141, 74.8560),
    "Shivamogga": (13.9299, 75.5681),
    "Ballari": (15.1394, 76.9214),
    "Davanagere": (14.4694, 75.9237),
    "Tumakuru": (13.3400, 77.1000),
    "Kalaburagi": (17.3356, 76.8386),
}

# Disaster types and their typical severity ranges
DISASTER_TYPES = {
    "flood": {
        "severity_range": (0.5, 0.95),
        "radius_range": (15, 50),
        "typical_areas": ["river banks", "low-lying areas", "coastal zones"]
    },
    "landslide": {
        "severity_range": (0.6, 0.9),
        "radius_range": (5, 25),
        "typical_areas": ["hilly terrain", "ghats", "mountain roads"]
    },
    "fire": {
        "severity_range": (0.3, 0.8),
        "radius_range": (2, 15),
        "typical_areas": ["industrial areas", "forest zones", "urban centers"]
    },
    "bridge_collapse": {
        "severity_range": (0.7, 1.0),
        "radius_range": (3, 10),
        "typical_areas": ["major highways", "river crossings", "old bridges"]
    }
}

# Specific location names for realism
LOCATIONS = {
    "Bengaluru Urban": ["Whitefield", "Electronic City", "M.G. Road", "Yeshwanthpur", "Hebbal", "JP Nagar", "Bannerghatta Road", "Mysore Road"],
    "Mysuru": ["Mysore City", "Nanjangud", "Hunsur", "KRS Dam", "Maddur", "Tirumakudal"],
    "Hubballi": ["Hubballi-Dharwad", "Kundur", "Gadag", "Koppal", "Hosdurga", "Navalgund"],
    "Belagavi": ["Belagavi City", "Khanapur", "Bailhongal", "Ramdurg", "Gokak", "Athni"],
    "Mangaluru": ["Mangalore City", "Bantwal", "Puttur", "Sullia", "Udupi", "Karkala", "Surathkal"],
    "Shivamogga": ["Shivamogga City", "Sagar", "Shikarpur", "Sorab", "Tirthahalli", "Kudremukh"],
    "Ballari": ["Ballari City", "Hospet", "Kudligi", "Sandur", "Kurugodu", "Kottur"],
    "Davanagere": ["Davanagere City", "Harapanahalli", "Jagalur", "Channagiri", "Honnali", "Harihar"],
    "Tumakuru": ["Tumakuru City", "Tiptur", "Kunigal", "Chiknayakanhalli", "Sira", "Madhugiri"],
    "Kalaburagi": ["Kalaburagi City", "Aland", "Chitapur", "Sedam", "Jevargi", "Chincholi"]
}

# Common road names that could be blocked
ROAD_NAMES = [
    "NH-48", "NH-52", "NH-69", "NH-73", "NH-234", "NH-276", "NH-371",
    "State Highway 1", "State Highway 3", "State Highway 7", "State Highway 12",
    "Mysore-Bangalore Road", "Mangalore-Hubballi Road", "Belgaum-Pune Road"
]

def generate_disaster_alerts():
    random.seed(RANDOM_SEED)
    alerts = []

    # Generate 8-12 disaster alerts
    num_alerts = random.randint(8, 12)

    used_combinations = set()

    while len(alerts) < num_alerts:
        disaster_type = random.choice(list(DISASTER_TYPES.keys()))
        district = random.choice(list(DISTRICT_CENTERS.keys()))
        location = random.choice(LOCATIONS[district])

        combo = (disaster_type, district, location)
        if combo in used_combinations:
            continue
        used_combinations.add(combo)

        config = DISASTER_TYPES[disaster_type]
        center_lat, center_lon = DISTRICT_CENTERS[district]

        # Add slight offset to the location
        lat_offset = random.uniform(-0.1, 0.1)
        lon_offset = random.uniform(-0.1, 0.1)
        lat = center_lat + lat_offset
        lon = center_lon + lon_offset

        severity = random.uniform(*config["severity_range"])
        radius = random.randint(*config["radius_range"])

        # Generate blocked routes (1-3)
        num_blocked = random.randint(1, 3)
        blocked_routes = []
        for _ in range(num_blocked):
            road = random.choice(ROAD_NAMES)
            if road not in blocked_routes:
                blocked_routes.append(f"{road} near {location}")

        alert = {
            "alert_id": f"ALERT_{uuid.uuid5(uuid.NAMESPACE_DNS, f'{disaster_type}-{district}-{location}-{len(alerts)}').hex[:8].upper()}",
            "disaster_type": disaster_type,
            "district": district,
            "location_name": location,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "severity": round(severity, 2),
            "affected_radius_km": radius,
            "blocked_routes": blocked_routes,
            "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=random.randint(0, 48))).isoformat(),
            "is_active": True,
            "description": generate_description(disaster_type, location, severity, radius)
        }

        alerts.append(alert)

    return alerts

def generate_description(disaster_type, location, severity, radius):
    """Generate a realistic disaster description"""
    severity_word = "severe" if severity > 0.75 else "moderate" if severity > 0.5 else "minor"

    descriptions = {
        "flood": f"{severity_word.capitalize()} flooding reported in {location}. Water levels affecting area within {radius}km radius. Emergency services on standby.",
        "landslide": f"{severity_word.capitalize()} landslide activity detected near {location}. Unstable slopes within {radius}km zone. Road clearance in progress.",
        "fire": f"{severity_word.capitalize()} fire incident at {location}. Fire spreading within {radius}km area. Multiple fire units deployed.",
        "bridge_collapse": f"Critical: Bridge collapse near {location}. Road blocked for {radius}km stretch. Diversion routes being arranged. Heavy vehicles advised to avoid."
    }

    return descriptions.get(disaster_type, f"{disaster_type.capitalize()} incident reported in {location}")

def save_alerts(alerts, filename="data/disaster_alerts.json"):
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, 'w') as f:
        json.dump(alerts, f, indent=2)
    print(f"Saved {len(alerts)} disaster alerts to {filename}")

def print_summary(alerts):
    print("\n=== Disaster Alerts Summary ===")
    print(f"Total alerts: {len(alerts)}")

    by_type = {}
    by_district = {}
    for a in alerts:
        t = a["disaster_type"]
        d = a["district"]
        by_type[t] = by_type.get(t, 0) + 1
        by_district[d] = by_district.get(d, 0) + 1

    print("\nBy Type:")
    for t, c in sorted(by_type.items()):
        print(f"  {t}: {c}")

    print("\nBy District:")
    for d, c in sorted(by_district.items()):
        print(f"  {d}: {c}")

    active = sum(1 for a in alerts if a["is_active"])
    avg_severity = sum(a["severity"] for a in alerts) / len(alerts)
    print(f"\nActive alerts: {active}")
    print(f"Average severity: {avg_severity:.2f}")

if __name__ == "__main__":
    alerts = generate_disaster_alerts()
    save_alerts(alerts)
    print_summary(alerts)
