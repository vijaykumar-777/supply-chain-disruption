import os
import tempfile
from typing import Any, Dict

from src.monitoring.supply_chain_monitor import SupplyChainMonitor
from src.relief.reference_data import load_reference_data, road_network_bytes


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in str(value)).strip("-") or "item"


def _float_or_none(value: Any):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _node(name: str, node_type: str, **extra: Any) -> Dict[str, Any]:
    return {
        "id": f"{node_type}-{_slug(name)}",
        "name": name,
        "node_type": node_type,
        **{key: value for key, value in extra.items() if value not in (None, "")},
    }


def seed_reference_graph(client, clear_existing: bool = False) -> Dict[str, Any]:
    monitor = SupplyChainMonitor(storage_dir=tempfile.mkdtemp(prefix="reliefroute-seed-"))
    monitor._geocode_location = lambda *_args, **_kwargs: None
    snapshot = monitor.parse_upload("01_road_network.csv", road_network_bytes())
    reference = load_reference_data()

    with client.driver.session() as session:
        if clear_existing:
            session.run("MATCH (n) DETACH DELETE n")

    client.load_schema()

    node_count = 0
    route_count = 0
    for hub in reference["datasets"].get("relief_hubs", []):
        client.insert_node(
            "Company",
            _node(
                hub.get("name"),
                "relief_hub",
                district=hub.get("district"),
                facility_type=hub.get("type"),
                lat=_float_or_none(hub.get("lat")),
                lon=_float_or_none(hub.get("lon")),
                capacity_persons=_float_or_none(hub.get("capacity_persons")),
                available_trucks=_float_or_none(hub.get("available_trucks")),
                contact=hub.get("contact"),
                data_provenance="curated_reference",
            ),
        )
        node_count += 1

    for village in reference["datasets"].get("villages_at_risk", []):
        client.insert_node(
            "Company",
            _node(
                village.get("name"),
                "settlement",
                district=village.get("district"),
                taluk=village.get("taluk"),
                lat=_float_or_none(village.get("lat")),
                lon=_float_or_none(village.get("lon")),
                population=_float_or_none(village.get("population")),
                vulnerability=village.get("vulnerability"),
                priority=village.get("priority"),
                data_provenance="curated_reference",
            ),
        )
        node_count += 1

    for route in snapshot["routes"]:
        source = _node(route["source_company"], "settlement", lat=route.get("origin_lat"), lon=route.get("origin_lon"))
        target = _node(route["target_company"], "settlement", lat=route.get("destination_lat"), lon=route.get("destination_lon"))
        origin = _node(route["origin"], "location", lat=route.get("origin_lat"), lon=route.get("origin_lon"))
        destination = _node(route["destination"], "location", lat=route.get("destination_lat"), lon=route.get("destination_lon"))

        client.insert_node("Company", source)
        client.insert_node("Company", target)
        client.insert_node("Location", origin)
        client.insert_node("Location", destination)

        route_properties = {
            "route_id": route["id"],
            "route_name": route["route_name"],
            "relationship_type": route["relationship_type"],
            "material": route["material"],
            "transport_mode": route["transport_mode"],
            "criticality": route["criticality"],
            "origin": route["origin"],
            "destination": route["destination"],
            "distance_km": _float_or_none(route.get("distance_km")),
            "travel_time_min": _float_or_none(route.get("travel_time_min")),
            "lead_time_days": max((_float_or_none(route.get("travel_time_min")) or 120) / 1440, 0.05),
            "data_provenance": "curated_reference",
        }
        client.insert_route(source["id"], target["id"], route_properties)
        client.insert_route(origin["id"], destination["id"], route_properties)
        route_count += 2

    with client.driver.session() as session:
        db_node_count = session.run("MATCH (n) RETURN count(n) as c").single()["c"]
        db_route_count = session.run("MATCH ()-[r:ROUTES_TO]->() RETURN count(r) as c").single()["c"]

    return {
        "success": True,
        "seeded_reference_nodes": node_count,
        "seeded_route_relationships": route_count,
        "neo4j_nodes": db_node_count,
        "neo4j_routes": db_route_count,
        "source": "curated_reference",
    }
