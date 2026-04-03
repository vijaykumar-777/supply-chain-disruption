import networkx as nx
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class SupplyChainNetwork:
    """NetworkX wrapper over the Neo4j supply chain for advanced pathfinding and modeling."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        
    def load_from_neo4j(self, graph_data: Dict[str, Any]):
        """Load nodes and edges into NetworkX from Neo4j dictionary."""
        self.graph.clear()
        
        for node_id, node_data in graph_data.get("nodes", {}).items():
            self.graph.add_node(node_id, **node_data["properties"], labels=node_data["labels"])
            
        for edge in graph_data.get("edges", []):
            if edge["type"] == "ROUTES_TO":
                # Convert lead time defaults, handling potential missing values securely
                lead_time = float(edge["properties"].get("lead_time_days", 1.0))
                self.graph.add_edge(edge["source"], edge["target"], 
                                    weight=lead_time, 
                                    **edge["properties"])
        
        logger.info(f"Loaded graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
        
    def calculate_resilience_score(self, node_id: str) -> float:
        """Calculate resilience score in canonical 0..1 range (Fix #9).
        Based on connectivity/alternative paths. PREDICT-03."""
        if node_id not in self.graph:
            return 0.0
            
        # Structural resilience: Degree centrality based metric
        out_degree = self.graph.out_degree(node_id)
        in_degree = self.graph.in_degree(node_id)
        
        # Fix #9: Scale to 0..1 (not 0..100) for API consistency
        score = min((out_degree + in_degree) / 5, 1.0)
        return max(score, 0.1)  # Base resilience floor of 10%

    def estimate_delay(self, route_edges: List[Tuple[str, str]], event_severity: float) -> float:
        """Estimate added lead time (days) for a route given a disruption event severity. PREDICT-01."""
        total_delay = 0.0
        
        # We assume standard delay scales drastically with event severity.
        for u, v in route_edges:
            if self.graph.has_edge(u, v):
                base_time = self.graph[u][v].get("weight", 1.0)
                # Apply an exponential delay factor based on urgency/severity level (0.0 to 1.0)
                impact_factor = (event_severity * 2) ** 2
                total_delay += base_time * impact_factor
                
        return round(total_delay, 1)

    def find_alternative_route(self, source: str, target: str, disrupted_nodes: List[str] = None) -> List[str]:
        """Find the shortest path avoiding disrupted nodes. PREDICT-04."""
        if disrupted_nodes is None:
            disrupted_nodes = []
            
        # Create a view of the subgraph missing the disrupted nodes
        safe_nodes = [n for n in self.graph.nodes() if n not in disrupted_nodes]
        subgraph = self.graph.subgraph(safe_nodes)
        
        try:
            path = nx.shortest_path(subgraph, source=source, target=target, weight="weight")
            return path
        except nx.NetworkXNoPath:
            return []
        except nx.NodeNotFound:
            return []
