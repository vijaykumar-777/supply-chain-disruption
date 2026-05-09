import json

import networkx as nx

from src.relief.hospital_network import HospitalNetworkService


def make_hospitals():
    return [
        {
            "hospital_id": "H1",
            "hospital_name": "Alpha Hospital",
            "district": "Bengaluru Urban",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "capacity": 100,
            "available_beds": 50,
            "trauma_level": "Level 1",
            "oxygen_available": True,
            "emergency_contact": "+91 900 000 0001",
        },
        {
            "hospital_id": "H2",
            "hospital_name": "Beta Hospital",
            "district": "Tumakuru",
            "latitude": 13.34,
            "longitude": 77.1,
            "capacity": 100,
            "available_beds": 45,
            "trauma_level": "Level 2",
            "oxygen_available": True,
            "emergency_contact": "+91 900 000 0002",
        },
        {
            "hospital_id": "H3",
            "hospital_name": "Gamma Hospital",
            "district": "Mysuru",
            "latitude": 12.2958,
            "longitude": 76.6394,
            "capacity": 100,
            "available_beds": 40,
            "trauma_level": "Level 2",
            "oxygen_available": False,
            "emergency_contact": "+91 900 000 0003",
        },
        {
            "hospital_id": "H4",
            "hospital_name": "Delta Hospital",
            "district": "Mangaluru",
            "latitude": 12.9141,
            "longitude": 74.856,
            "capacity": 100,
            "available_beds": 35,
            "trauma_level": "Level 3",
            "oxygen_available": True,
            "emergency_contact": "+91 900 000 0004",
        },
    ]


def test_build_connected_graph_connects_all_hospitals():
    service = HospitalNetworkService()
    graph = service.build_connected_graph(make_hospitals(), nearest_neighbors=1)

    assert graph.number_of_nodes() == 4
    assert nx.is_connected(graph)
    assert all("distance_km" in data for _, _, data in graph.edges(data=True))


def test_route_optimization_avoids_disaster_blocked_edge():
    service = HospitalNetworkService()
    service.hospitals = make_hospitals()
    graph = nx.Graph()
    for hospital in service.hospitals:
        graph.add_node(hospital["hospital_id"], **hospital)

    graph.add_edge("H1", "H2", distance_km=20, estimated_time=20, road_status="good", risk_score=0.1, blocked=False, danger_level=0, affected_by=[])
    graph.add_edge("H2", "H4", distance_km=20, estimated_time=20, road_status="good", risk_score=0.1, blocked=False, danger_level=0, affected_by=[])
    graph.add_edge("H1", "H3", distance_km=40, estimated_time=45, road_status="fair", risk_score=0.2, blocked=False, danger_level=0, affected_by=[])
    graph.add_edge("H3", "H4", distance_km=40, estimated_time=45, road_status="fair", risk_score=0.2, blocked=False, danger_level=0, affected_by=[])

    service.base_graph = graph
    service.graph = graph.copy()
    service.alerts = [
        {
            "alert_id": "A1",
            "disaster_type": "bridge_collapse",
            "district": "Tumakuru",
            "location_name": "Blocked bridge",
            "latitude": 13.34,
            "longitude": 77.1,
            "severity": 0.95,
            "affected_radius_km": 60,
            "blocked_routes": [],
            "timestamp": "2026-05-09T00:00:00",
            "is_active": True,
            "description": "Bridge collapse test",
        }
    ]
    service._load_alerts = lambda: service.alerts

    route = service.optimize_route("H1", "H4", strategy="shortest")

    assert route["path"] == ["H1", "H3", "H4"]
    assert route["blocked_segments"] == 0
    assert any(item["blocked"] for item in service.get_routes(recalculate=False))


def test_api_recalculate_routes_contract(monkeypatch):
    import src.api.main as api_main

    monkeypatch.setattr(
        api_main.hospital_network_service,
        "refresh",
        lambda: {"total_routes": 10, "blocked_routes": 2, "affected_routes": 3, "active_alerts": 1},
    )

    response = api_main.recalculate_routes()

    assert response == {
        "success": True,
        "total_routes": 10,
        "blocked_routes": 2,
        "affected_routes": 3,
        "active_alerts": 1,
    }
