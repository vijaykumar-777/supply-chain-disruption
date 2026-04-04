import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.monitoring.supply_chain_monitor import SupplyChainMonitor


def test_parse_csv_upload_supports_aliases(tmp_path):
    monitor = SupplyChainMonitor(storage_dir=str(tmp_path))
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

    monkeypatch.setattr(monitor, "_fetch_gdelt_alerts", lambda snapshot: [])
    monkeypatch.setattr(monitor, "_fetch_weather_alerts", lambda snapshot: [])

    report = monitor.build_report(snapshot)

    assert report["metrics"]["total_routes"] == 2
    assert report["metrics"]["active_alerts"] >= 1
    assert len(report["impacted_links"]) >= 1
    assert report["impacted_links"][0]["status"] in {"blocked", "at_risk"}
    battery = next(company for company in report["impacted_companies"] if company["company"] == "BatteryCo")
    assert battery["risk_score"] > 0
