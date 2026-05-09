"""
Generate fake Karnataka Hospital Dataset
"""
import csv
import random
import math
from pathlib import Path

RANDOM_SEED = 20260509

# District center coordinates (approximate)
DISTRICTS = {
    "Bengaluru Urban": {"lat": 12.9716, "lon": 77.5946, "count": 15},
    "Mysuru": {"lat": 12.2958, "lon": 76.6394, "count": 10},
    "Hubballi": {"lat": 15.3647, "lon": 75.1240, "count": 8},
    "Belagavi": {"lat": 15.8497, "lon": 74.4977, "count": 8},
    "Mangaluru": {"lat": 12.9141, "lon": 74.8560, "count": 7},
    "Shivamogga": {"lat": 13.9299, "lon": 75.5681, "count": 6},
    "Ballari": {"lat": 15.1394, "lon": 76.9214, "count": 6},
    "Davanagere": {"lat": 14.4694, "lon": 75.9237, "count": 5},
    "Tumakuru": {"lat": 13.3400, "lon": 77.1000, "count": 5},
    "Kalaburagi": {"lat": 17.3356, "lon": 76.8386, "count": 5},
}

# Hospital name templates
HOSPITAL_PREFIXES = [
    "Government", "District", "Medical College", "General Hospital",
    "Taluk Hospital", "Community Health Center", "Primary Health Center",
    "Private Hospital", "Mission Hospital", "Charitable Hospital"
]

HOSPITAL_NAMES = [
    "City Hospital", "Central Hospital", "Regional Hospital", "Memorial Hospital",
    "Multi-Specialty Hospital", "Emergency Care Center", "Trauma Center",
    "Women's Hospital", "Children's Hospital", "Cancer Center",
    "Heart Center", "Neurology Institute", "Orthopedic Center", "Eye Hospital",
    "Nephrology Center", "Diabetic Center", "Mental Health Center",
    "Infectious Disease Hospital", "Rehabilitation Center", "Geriatric Care",
    "Blood Bank Center", "Dialysis Center", "MRI Center", "Diagnostic Center",
    "Research Hospital", "Teaching Hospital", "Referral Hospital"
]

DISTRICT_TOWNS = {
    "Bengaluru Urban": ["Bengaluru", "Yelahanka", "Bangalore North", "Bangalore South", "Anekal", "Ramanagara"],
    "Mysuru": ["Mysuru", "Nanjangud", "Hunsur", "KRS", "Tirumakudal", "Narasanagara"],
    "Hubballi": ["Hubballi", "Dharwad", "Kundur", "Gadag", "Koppal", "Hosdurga"],
    "Belagavi": ["Belagavi", "Khanapur", "Bailhongal", "Ramdurg", "Gokak", "Athni"],
    "Mangaluru": ["Mangaluru", "Bantwal", "Puttur", "Sullia", "Udupi", "Karkala"],
    "Shivamogga": ["Shivamogga", "Sagar", "Shikarpur", "Sorab", "Tirthahalli", "Hosanagara"],
    "Ballari": ["Ballari", "Hospet", "Kudligi", "Sandur", "Kurugodu", "Kottur"],
    "Davanagere": ["Davanagere", "Harapanahalli", "Jagalur", "Channagiri", "Honnali"],
    "Tumakuru": ["Tumakuru", "Tiptur", "Kunigal", "Chiknayakanhalli", "Sira"],
    "Kalaburagi": ["Kalaburagi", "Aland", "Chitapur", "Sedam", "Jevargi"],
}

TRAUMA_LEVELS = ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5"]

def generate_phone():
    return f"+91 {random.randint(800, 999)} {random.randint(100, 999)} {random.randint(1000, 9999)}"

def generate_hospitals():
    random.seed(RANDOM_SEED)
    hospitals = []
    hospital_id = 1

    for district, info in DISTRICTS.items():
        town_list = DISTRICT_TOWNS[district]

        for i in range(info["count"]):
            # Add random offset from district center (roughly 0-30km)
            lat_offset = random.uniform(-0.25, 0.25)
            lon_offset = random.uniform(-0.25, 0.25)

            lat = info["lat"] + lat_offset
            lon = info["lon"] + lon_offset

            # Generate capacity between 50 and 500
            capacity = random.randint(50, 500)

            # Available beds is 30-90% of capacity
            available_beds = int(capacity * random.uniform(0.30, 0.90))

            # Larger hospitals in Bangalore get higher trauma levels
            if district == "Bengaluru Urban" and i < 5:
                trauma = "Level 1"
            elif district == "Bengaluru Urban" or "Mysuru" in district or "Mangaluru" in district:
                trauma = random.choice(["Level 1", "Level 2", "Level 3"])
            else:
                trauma = random.choice(TRAUMA_LEVELS)

            # Oxygen availability more likely in bigger hospitals
            oxygen_available = random.random() > 0.25

            # Pick a prefix and name
            prefix = random.choice(HOSPITAL_PREFIXES)
            name_suffix = random.choice(HOSPITAL_NAMES)
            town = random.choice(town_list)

            if "Government" in prefix or "District" in prefix or "Taluk" in prefix or "Primary" in prefix or "Community" in prefix:
                hospital_name = f"{prefix}, {town}"
            else:
                hospital_name = f"{prefix} {name_suffix}, {town}"

            hospitals.append({
                "hospital_id": f"HOSP_{str(hospital_id).zfill(3)}",
                "hospital_name": hospital_name,
                "district": district,
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "capacity": capacity,
                "available_beds": available_beds,
                "trauma_level": trauma,
                "oxygen_available": oxygen_available,
                "emergency_contact": generate_phone()
            })

            hospital_id += 1

    return hospitals

def save_hospitals_csv(hospitals, filename="data/hospitals.csv"):
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["hospital_id", "hospital_name", "district", "latitude", "longitude",
                  "capacity", "available_beds", "trauma_level", "oxygen_available", "emergency_contact"]

    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for hospital in hospitals:
            row = hospital.copy()
            row["oxygen_available"] = "Yes" if hospital["oxygen_available"] else "No"
            writer.writerow(row)

    print(f"Saved {len(hospitals)} hospitals to {filename}")

if __name__ == "__main__":
    hospitals = generate_hospitals()
    save_hospitals_csv(hospitals)

    # Print summary
    print("\n=== Hospital Dataset Summary ===")
    print(f"Total hospitals: {len(hospitals)}")

    by_district = {}
    for h in hospitals:
        d = h["district"]
        by_district[d] = by_district.get(d, 0) + 1

    for d, c in sorted(by_district.items()):
        print(f"  {d}: {c}")

    # Stats
    total_capacity = sum(h["capacity"] for h in hospitals)
    total_beds = sum(h["available_beds"] for h in hospitals)
    with_oxygen = sum(1 for h in hospitals if h["oxygen_available"])

    print(f"\nTotal capacity: {total_capacity}")
    print(f"Total available beds: {total_beds}")
    print(f"Hospitals with oxygen: {with_oxygen}")
