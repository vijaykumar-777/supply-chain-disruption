import sys
import os

# Add the project root to sys.path for absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph.neo4j_client import Neo4jClient
from src.prediction.network_model import SupplyChainNetwork
from src.prediction.monte_carlo import RiskSimulator
import json

def test_predictions():
    client = Neo4jClient()
    
    try:
        print("1. Fetching Full Graph from Neo4j...")
        graph_data = client.get_full_graph()
        
        print(f"   => Found {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges.")
        
        print("\n2. Initializing NetworkX Supply Chain Model...")
        sc_network = SupplyChainNetwork()
        sc_network.load_from_neo4j(graph_data)
        
        route_edges_in_graph = [
            (edge["source"], edge["target"])
            for edge in graph_data["edges"]
            if edge["type"] == "ROUTES_TO"
        ]
        if not route_edges_in_graph:
            raise RuntimeError("No live ROUTES_TO edges found in Neo4j. Import real route data before testing predictions.")

        source, target = route_edges_in_graph[0]
        
        print(f"\n3. Running Pathfinding Optimization (Normal Delivery) from {source} to {target}")
        best_path = sc_network.find_alternative_route(source, target)
        print(f"   => Optimal Route: {' -> '.join(best_path)}")
        
        print(f"\n4. Risk Scenario: Disruption at {target}!")
        disrupted_nodes = [target]
        alt_path = sc_network.find_alternative_route(source, target, disrupted_nodes=disrupted_nodes)
        if alt_path:
            print(f"   => Alternative Route Found: {' -> '.join(alt_path)}")
        else:
            print(f"   => CRITICAL WARNING: No alternative routing available! Network broken.")
            
        print("\n5. Running Monte Carlo Simulation (10,000 iterations) on original route...")
        
        # Convert node array to edge array [(u,v), (v,w)]
        route_edges = [(best_path[i], best_path[i+1]) for i in range(len(best_path)-1)]
        
        simulator = RiskSimulator(sc_network)
        results = simulator.simulate_route_risk(route_edges, iterations=10000)
        
        print(f"   => Target Route: {' -> '.join(best_path)}")
        print(f"   => Mean Delivery Time: {results['mean_days']:.1f} days")
        print(f"   => P50 (Expected) Time: {results['p50_days']:.1f} days")
        print(f"   => P95 (Worst Case) Time: {results['p95_days']:.1f} days")
        print(f"   => Absolute Max Delay Simulated: {results['max_risk_days']:.1f} days")
        
        print("\n6. Asking AI Assistant (Ollama) for Recommendations...")
        from src.ai.ollama_client import AIAdvisor
        advisor = AIAdvisor()
        
        with client.driver.session() as session:
            event_record = session.run(
                """
                MATCH (e:Event)-[:AFFECTS]->(l:Location)
                RETURN e.title as title, e.category as category, collect(l.name) as locations
                ORDER BY e.timestamp DESC
                LIMIT 1
                """
            ).single()

        if event_record:
            event_dict = {
                "title": event_record["title"],
                "category": event_record["category"],
                "locations": event_record["locations"],
            }
            recommendation = advisor.generate_recommendation(event_dict, results, alt_path)
            print("\n--- AI ADVISOR RECOMMENDATION ---")
            print(recommendation)
            print("---------------------------------")
        else:
            print("\n6. No live disruption events found in Neo4j, so AI recommendation generation was skipped.")
        
        # Test feedback loop
        advisor.submit_feedback("rec_test_123", 1, "Provided good actionable steps during testing.")
        
        print("\nPrediction Engine & AI Assistant (Phase 3 & 4) Successfully Validated!")
        
    finally:
        client.close()

if __name__ == "__main__":
    test_predictions()
