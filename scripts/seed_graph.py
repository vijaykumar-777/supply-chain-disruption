"""
ATLAS AI — Real Supply Chain Graph Importer

Imports a user-provided CSV or JSON route file into Neo4j.

Usage:
  python3 scripts/seed_graph.py /absolute/path/to/routes.csv --clear
"""

import argparse
import os
import sys
import tempfile
from typing import Dict, Iterable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph.neo4j_client import Neo4jClient
from src.monitoring.supply_chain_monitor import SupplyChainMonitor


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-") or "item"


def _company_node(company: str) -> Dict[str, str]:
    return {
        "id": f"company-{_slug(company)}",
        "name": company,
        "node_type": "company",
    }


def _location_node(name: str, lat, lon) -> Dict[str, object]:
    return {
        "id": f"location-{_slug(name)}",
        "name": name,
        "node_type": "location",
        "lat": lat,
        "lon": lon,
    }


def _unique(values: Iterable[str]):
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        yield value


def import_routes(file_path: str, clear_existing: bool) -> None:
    with open(file_path, "rb") as handle:
        content = handle.read()

    monitor = SupplyChainMonitor(storage_dir=tempfile.mkdtemp(prefix="atlas-import-"))
    snapshot = monitor.parse_upload(os.path.basename(file_path), content)

    client = Neo4jClient()
    try:
        if clear_existing:
            with client.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")

        client.load_schema()

        for route in snapshot["routes"]:
            source_company = _company_node(route["source_company"])
            target_company = _company_node(route["target_company"])
            origin_location = _location_node(route["origin"], route.get("origin_lat"), route.get("origin_lon"))
            destination_location = _location_node(route["destination"], route.get("destination_lat"), route.get("destination_lon"))

            client.insert_node("Company", source_company)
            client.insert_node("Company", target_company)
            client.insert_node("Location", origin_location)
            client.insert_node("Location", destination_location)

            route_properties = {
                "route_id": route["id"],
                "route_name": route["route_name"],
                "relationship_type": route["relationship_type"],
                "material": route["material"],
                "transport_mode": route["transport_mode"],
                "criticality": route["criticality"],
                "origin": route["origin"],
                "destination": route["destination"],
                "lead_time_days": 1.0,
            }

            client.insert_route(source_company["id"], target_company["id"], route_properties)
            client.insert_route(origin_location["id"], destination_location["id"], route_properties)

        with client.driver.session() as session:
            node_count = session.run("MATCH (n) RETURN count(n) as c").single()["c"]
            edge_count = session.run("MATCH ()-[r:ROUTES_TO]->() RETURN count(r) as c").single()["c"]

        print(f"Imported {snapshot['route_count']} real routes from {os.path.basename(file_path)}")
        print(f"Neo4j now contains {node_count} nodes and {edge_count} ROUTES_TO relationships")
        print("Imported companies:", ", ".join(_unique(route["source_company"] for route in snapshot["routes"])))
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a real supply chain route file into Neo4j.")
    parser.add_argument("file_path", help="Path to a CSV or JSON route file")
    parser.add_argument("--clear", action="store_true", help="Clear the existing Neo4j graph before import")
    args = parser.parse_args()

    import_routes(os.path.abspath(args.file_path), clear_existing=args.clear)


if __name__ == "__main__":
    main()
