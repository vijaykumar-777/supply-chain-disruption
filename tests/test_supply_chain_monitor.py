import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.monitoring.supply_chain_monitor import SupplyChainMonitor


def test_parse_csv_upload_supports_aliases(tmp_path):
    monitor = SupplyChainMonitor(storage_dir=str(tmp_path))
    monitor._geocode_location = lambda *_args, **_kwargs: None
    content = b"""company_a,company_b,relationship,raw_material,origin_port,destination_port,mode,priority\nMineCo,RefineCo,supplies,Lithium Ore,Chile,Shanghai,sea,high\n"""

    snapshot = monitor.parse_upload("network.csv", content)

    assert snapshot["route_count"] == 1
    route = snapshot["routes"][0]
    assert route["source_company"] == "MineCo"
    assert route["target_company"] == "RefineCo"
    assert route["material"] == "Lithium Ore"
    assert route["criticality"] == "high"


def test_build_report_scores_impacts_and_downstream_exposure(tmp_path, monkeypatch):
    monitor = SupplyChainMonitor(storage_dir=str(tmp_path))
    monkeypatch.setattr(monitor, "_geocode_location", lambda *_args, **_kwargs: None)
    routes = [
        {
            "source_company": "MineCo",
            "target_company": "RefineCo",
            "relationship_type": "supplies",
            "material": "Lithium Ore",
            "origin": "Myanmar",
            "destination": "Shanghai",
            "transport_mode": "sea",
            "criticality": "high",
            "route_name": "Myanmar to Shanghai",
        },
        {
            "source_company": "RefineCo",
            "target_company": "BatteryCo",
            "relationship_type": "supplies",
            "material": "Lithium Cells",
            "origin": "Shanghai",
            "destination": "Mumbai",
            "transport_mode": "sea",
            "criticality": "high",
            "route_name": "Shanghai to Mumbai",
        },
    ]

    snapshot = monitor.parse_upload("network.json", json.dumps(routes).encode("utf-8"))

    monkeypatch.setattr(
        monitor,
        "_fetch_gdelt_alerts",
        lambda _snapshot: [
            {
                "id": "gdelt-impact-1",
                "title": "Myanmar export controls tighten",
                "description": "Cross-border movement of rare earth materials has been interrupted.",
                "category": "geopolitical",
                "severity": 0.81,
                "type": "critical",
                "locations": ["Myanmar", "Shanghai"],
                "companies": [],
                "timestamp": "2026-04-04T08:00:00Z",
                "source": "gdelt",
            }
        ],
    )
    monkeypatch.setattr(monitor, "_fetch_weather_alerts", lambda snapshot: [])

    report = monitor.build_report(snapshot)

    assert report["metrics"]["total_routes"] == 2
    assert report["metrics"]["active_alerts"] >= 1
    assert len(report["impacted_links"]) >= 1
    assert report["impacted_links"][0]["status"] in {"blocked", "at_risk"}
    battery = next(company for company in report["impacted_companies"] if company["company"] == "BatteryCo")
    assert battery["risk_score"] > 0


def test_live_alerts_do_not_force_fallback_alerts(tmp_path, monkeypatch):
    monitor = SupplyChainMonitor(storage_dir=str(tmp_path))
    monkeypatch.setattr(monitor, "_geocode_location", lambda *_args, **_kwargs: None)
    routes = [
        {
            "source_company": "SupplierCo",
            "target_company": "FactoryCo",
            "relationship_type": "supplies",
            "material": "Copper",
            "origin": "Chennai",
            "destination": "Mumbai",
            "transport_mode": "rail",
            "criticality": "high",
            "route_name": "India copper corridor",
        }
    ]

    snapshot = monitor.parse_upload("network.json", json.dumps(routes).encode("utf-8"))

    monkeypatch.setattr(
        monitor,
        "_fetch_gdelt_alerts",
        lambda _snapshot: [
            {
                "id": "gdelt-live-1",
                "title": "Freight congestion near Chennai",
                "description": "Rail freight congestion is slowing cargo departures from Chennai.",
                "category": "logistics",
                "severity": 0.64,
                "type": "warning",
                "locations": ["Chennai"],
                "companies": [],
                "timestamp": "2026-04-04T08:00:00Z",
                "source": "gdelt",
            }
        ],
    )
    monkeypatch.setattr(monitor, "_fetch_weather_alerts", lambda _snapshot: [])

    report = monitor.build_report(snapshot)

    assert report["source_status"]["gdelt"]["live"] is True
    assert report["source_status"]["fallback"]["live"] is False
    assert report["alerts"][0]["source"] == "gdelt"


def test_impacted_route_includes_alternate_route(tmp_path, monkeypatch):
    monitor = SupplyChainMonitor(storage_dir=str(tmp_path))
    monkeypatch.setattr(monitor, "_geocode_location", lambda *_args, **_kwargs: None)
    routes = [
        {
            "source_company": "Samsung",
            "target_company": "Tesla",
            "relationship_type": "supplies",
            "material": "EV Batteries",
            "origin": "Shanghai",
            "destination": "Long Beach",
            "transport_mode": "sea",
            "criticality": "high",
            "route_name": "CN-US Battery Route",
        },
        {
            "source_company": "Panasonic",
            "target_company": "Tesla",
            "relationship_type": "supplies",
            "material": "EV Batteries",
            "origin": "Osaka",
            "destination": "San Francisco",
            "transport_mode": "sea",
            "criticality": "high",
            "route_name": "JP-US EV Battery",
        },
    ]

    snapshot = monitor.parse_upload("network.json", json.dumps(routes).encode("utf-8"))

    monkeypatch.setattr(
        monitor,
        "_fetch_gdelt_alerts",
        lambda _snapshot: [
            {
                "id": "gdelt-live-2",
                "title": "Shanghai port labor dispute",
                "description": "Container throughput is reduced because of ongoing labor action.",
                "category": "labor",
                "severity": 0.8,
                "type": "critical",
                "locations": ["Shanghai"],
                "companies": ["Samsung"],
                "timestamp": "2026-04-04T08:00:00Z",
                "source": "gdelt",
            }
        ],
    )
    monkeypatch.setattr(monitor, "_fetch_weather_alerts", lambda _snapshot: [])

    report = monitor.build_report(snapshot)

    impacted_route = next(link for link in report["impacted_links"] if link["source_company"] == "Samsung")
    assert impacted_route["alternative_route"] is not None
    assert impacted_route["alternative_route"]["strategy"] == "supplier_substitution"
    assert impacted_route["alternative_route"]["company_path"] == ["Panasonic", "Tesla"]
    assert impacted_route["alternative_route"]["route_names"] == ["JP-US EV Battery"]
