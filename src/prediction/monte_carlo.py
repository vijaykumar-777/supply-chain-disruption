import numpy as np
from typing import List, Dict, Any, Tuple
from src.prediction.network_model import SupplyChainNetwork

class RiskSimulator:
    """Monte Carlo simulation engine for analyzing route risk distributions."""
    
    def __init__(self, sc_network: SupplyChainNetwork):
        self.network = sc_network
        
    def simulate_route_risk(self, route_edges: List[Tuple[str, str]], iterations: int = 1000) -> Dict[str, Any]:
        """
        Run a Monte Carlo simulation. PREDICT-02.
        Calculates the probability distribution of total delivery time across many scenarios,
        assuming normal variance in transit times plus rare high-impact disruption risks.
        """
        total_times = []
        
        # Base stats for edges
        route_stats = []
        for u, v in route_edges:
            if self.network.graph.has_edge(u, v):
                base_lt = self.network.graph[u][v].get("weight", 1.0)
                route_stats.append(base_lt)
            else:
                return {"error": "Invalid route graph"}

        for _ in range(iterations):
            run_total = 0.0
            
            for base_lt in route_stats:
                # 1. Standard operational variance (Normal Distribution +/- 20%)
                std_dev = base_lt * 0.2
                operational_time = np.random.normal(base_lt, std_dev)
                
                # 2. Risk factor: Black swan / disruption variance
                # 5% chance of a major delay happening on any node
                if np.random.random() < 0.05:
                    impact_multiplier = np.random.uniform(1.5, 4.0) 
                    operational_time *= impact_multiplier
                    
                run_total += max(0, operational_time) # Ensure time is positive
                
            total_times.append(run_total)
            
        times_array = np.array(total_times)
        
        return {
            "iterations": iterations,
            "mean_days": float(np.mean(times_array)),
            "p50_days": float(np.percentile(times_array, 50)),
            "p95_days": float(np.percentile(times_array, 95)),
            "max_risk_days": float(np.max(times_array)),
            "std_dev": float(np.std(times_array))
        }
