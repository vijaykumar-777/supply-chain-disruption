"""
Build a connected Karnataka hospital route graph.

Hospitals are connected to their nearest neighbors, then any remaining
components are bridged by the shortest available inter-component route.
"""
import sys
from pathlib import Path

import networkx as nx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.relief.hospital_network import GRAPH_PATH, HospitalNetworkService


def analyze_graph(graph: nx.Graph):
    print("\n=== Hospital Network Graph Analysis ===")
    print(f"Total nodes (hospitals): {graph.number_of_nodes()}")
    print(f"Total edges (routes): {graph.number_of_edges()}")

    if graph.number_of_nodes() == 0:
        return

    degrees = [graph.degree(node) for node in graph.nodes()]
    print(f"Avg connections per hospital: {sum(degrees) / len(degrees):.1f}")
    print(f"Max connections: {max(degrees)}")
    print(f"Min connections: {min(degrees)}")
    print(f"Connected components: {nx.number_connected_components(graph)}")

    distances = [data["distance_km"] for _, _, data in graph.edges(data=True)]
    if distances:
        print(f"Edge distance range: {min(distances):.1f} - {max(distances):.1f} km")
        print(f"Avg edge distance: {sum(distances) / len(distances):.1f} km")

    road_statuses = {}
    for _, _, data in graph.edges(data=True):
        status = data.get("road_status", "unknown")
        road_statuses[status] = road_statuses.get(status, 0) + 1
    print("Road status breakdown:", road_statuses)


if __name__ == "__main__":
    service = HospitalNetworkService()
    print(f"Loaded {len(service.hospitals)} hospitals")
    graph = service.build_connected_graph(service.hospitals)
    service.base_graph = graph
    service.graph = graph
    service._save_graph(graph)
    analyze_graph(graph)
    print(f"\nGraph saved to {GRAPH_PATH}")
