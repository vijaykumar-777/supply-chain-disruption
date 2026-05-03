import csv
import sys
import os
import json
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.graph.neo4j_client import Neo4jClient
from src.monitoring.supply_chain_monitor import SupplyChainMonitor

def hardcoded_geocodes(name: str):
    lookup = {
        "usa": (39.7837, -100.4458),
        "taiwan": (23.9739, 120.9820),
        "japan": (36.5748, 139.2394),
        "netherlands": (52.2434, 5.6343),
        "south korea": (36.6383, 127.6961),
        "germany": (51.0834, 10.4234),
        "india": (22.3511, 78.6677),
        "china": (35.8616, 104.1953),
        "malaysia": (4.1093, 109.4554),
        "switzerland": (46.7985, 8.2319),
        "united kingdom": (54.7023, -3.2765),
        "france": (46.6033, 1.8883),
        "sweden": (64.9631, 17.3069),
        "ireland": (53.4129, -8.2438),
        "south africa": (-30.5594, 22.9375),
        "brazil": (-14.2350, -51.9252),
        "canada": (56.1303, -106.3467),
        "italy": (41.8719, 12.5673),
        "spain": (40.4636, -3.7492),
        "singapore": (1.3520, 103.8198),
        "mexico": (23.6345, -102.5527),
        "australia": (-25.2743, 133.7751),
        "denmark": (56.2639, 9.5017),
        "belgium": (50.5038, 4.4699),
        "finland": (61.9241, 25.7481),
        "norway": (60.4720, 8.4689),
        "austria": (47.5162, 14.5500),
        "israel": (31.0460, 34.8516),
        "new zealand": (-40.9005, 174.8859),
        "argentina": (-38.4160, -63.6166),
    }
    return lookup.get(name.lower().strip())

def main():
    client = Neo4jClient()
    
    # 1. Clear existing
    print("Clearing Neo4j...", end="", flush=True)
    with client.driver.session() as s:
        s.run("MATCH (n) DETACH DELETE n")
    print(" Done.")
    
    # Load schema
    client.load_schema()

    # 2. Parse 300 Companies
    print("Importing companies...", end="", flush=True)
    slug = lambda x: "".join(c.lower() if c.isalnum() else "-" for c in x).strip("-") or "c"
    
    company_map = {} # name -> id
    with open("companies_300.csv", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            name = (row.get("company_name") or "").strip()
            if not name: continue
            
            cik = row.get("edgar_cik", "").strip().zfill(10) if row.get("edgar_cik", "").strip() else None
            cid = f"company:sec:{cik}" if cik else f"company-{slug(name)}"
            
            country = row.get("country", "").strip()
            
            props = {
                "id": cid,
                "name": name,
                "ticker": row.get("ticker", ""),
                "country": country,
                "node_type": "company",
                "sector": row.get("sector", ""),
                "industry": row.get("industry", ""),
            }
            client.insert_node("Company", props)
            company_map[name.lower()] = cid
            company_map[slug(name)] = cid
            
            # Map country to location too
            if country:
                coords = hardcoded_geocodes(country) or (0.0, 0.0)
                client.insert_node("Location", {
                    "id": f"location-{slug(country)}",
                    "name": country,
                    "node_type": "location",
                    "lat": coords[0],
                    "lon": coords[1]
                })

    print(f" Imported {len(company_map)//2} unique companies.")

    # 3. Parse 600 Routes
    print("Importing supplier routes...", end="", flush=True)
    imported_routes = 0
    with open("supplier_routes_600.csv", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            s_name = row.get("source_company", "").strip()
            t_name = row.get("destination_company", "").strip()
            if not s_name or not t_name: continue
            
            sid = company_map.get(s_name.lower()) or company_map.get(slug(s_name))
            tid = company_map.get(t_name.lower()) or company_map.get(slug(t_name))
            
            if not sid:
                sid = f"company-{slug(s_name)}"
                client.insert_node("Company", {"id": sid, "name": s_name, "node_type": "company"})
                company_map[s_name.lower()] = sid
            if not tid:
                tid = f"company-{slug(t_name)}"
                client.insert_node("Company", {"id": tid, "name": t_name, "node_type": "company"})
                company_map[t_name.lower()] = tid

            route_props = {
                "route_id": str(uuid.uuid4()),
                "relationship_type": row.get("relationship_type", "supplies"),
                "transport_mode": row.get("route_mode", "sea"),
                "criticality": row.get("risk_level", "medium"),
                "material": row.get("commodity", "goods"),
            }
            client.insert_route(sid, tid, route_props)
            imported_routes += 1
            
    print(f" Imported {imported_routes} routes.")
    client.close()
    print("Database seeding completed.")

if __name__ == "__main__":
    main()
