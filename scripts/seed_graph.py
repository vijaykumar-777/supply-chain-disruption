import sys
import os

# Add the project root to sys.path for absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph.neo4j_client import Neo4jClient
from src.graph.correlation_engine import CorrelationEngine
import uuid
import datetime

def seed_database():
    print("Connecting to Neo4j...")
    client = Neo4jClient()
    engine = CorrelationEngine()
    
    try:
        # 1. Initialize schema
        print("Initializing schema (indexes/constraints)...")
        client.load_schema()
        
        # 2. Add Supply Chain Nodes
        print("Seeding supply chain nodes...")
        
        # Suppliers (Asia)
        client.insert_node("Supplier", {"id": "S_CH_01", "name": "Shenzhen Components Co.", "country": "China", "type": "Microchips"})
        client.insert_node("Supplier", {"id": "S_VN_02", "name": "Hanoi Textiles", "country": "Vietnam", "type": "Raw Materials"})
        
        # Ports
        client.insert_node("Location", {"name": "Port of Shanghai", "type": "Port", "lat": 31.23, "lon": 121.47})
        client.insert_node("Location", {"name": "Port of Long Beach", "type": "Port", "lat": 33.77, "lon": -118.19})
        client.insert_node("Location", {"name": "Port of Rotterdam", "type": "Port", "lat": 51.92, "lon": 4.47})
        
        # Factories
        client.insert_node("Factory", {"id": "F_US_CA", "name": "Tesla Fremont Factory", "country": "USA", "region": "California"})
        client.insert_node("Factory", {"id": "F_DE_BW", "name": "Stuttgart Assembly", "country": "Germany", "region": "Bavaria"})
        
        # 3. Create Routes
        print("Creating supply chain routes...")
        client.insert_route("S_CH_01", "Port of Shanghai", {"mode": "Inland", "distance_km": 50})
        client.insert_route("Port of Shanghai", "Port of Long Beach", {"mode": "Ocean", "distance_km": 10500, "lead_time_days": 18})
        client.insert_route("Port of Long Beach", "F_US_CA", {"mode": "Truck", "distance_km": 650, "lead_time_days": 2})
        client.insert_route("Port of Shanghai", "Port of Rotterdam", {"mode": "Ocean", "distance_km": 19500, "lead_time_days": 35})
        client.insert_route("Port of Rotterdam", "F_DE_BW", {"mode": "Rail", "distance_km": 720, "lead_time_days": 3})
        
        # 4. Inject Mock Disruption Events
        print("Injecting initial disruption events...")
        event1 = {
            "id": str(uuid.uuid4()),
            "title": "Severe Coastal Storm - Shanghai Coastline",
            "category": "NATURAL_DISASTER",
            "timestamp": datetime.datetime.now().isoformat(),
            "locations": ["Port of Shanghai"]
        }
        event1["severity"] = engine.calculate_severity(event1)
        client.insert_event(event1)
        
        event2 = {
            "id": str(uuid.uuid4()),
            "title": "Port Labor Dispute - Long Beach",
            "category": "STRIKE",
            "timestamp": datetime.datetime.now().isoformat(),
            "locations": ["Port of Long Beach"]
        }
        event2["severity"] = engine.calculate_severity(event2)
        client.insert_event(event2)
        
        print("\nSUCCESS: Graph database seeded with nodes, routes, and events.")
        print("You can now see these disruptions on the dashboard map.")
        
    finally:
        client.close()

if __name__ == "__main__":
    seed_database()
