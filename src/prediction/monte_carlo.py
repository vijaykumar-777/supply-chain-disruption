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
        
        Fix #2: Guard against empty/invalid route stats and iterations <= 0.
        """
        # Fix #2: Guard against invalid iterations
        if iterations <= 0:
            return {"error": "iterations must be greater than 0"}
        
        total_times = []
        
        # Base stats for edges
        route_stats = []
        for u, v in route_edges:
            if self.network.graph.has_edge(u, v):
                base_lt = self.network.graph[u][v].get("weight", 1.0)
                route_stats.append(base_lt)
            else:
                return {"error": f"Invalid route edge: {u} -> {v} does not exist in the network"}

        # Fix #2: Guard against empty route
        if not route_stats:
            return {"error": "No valid route edges to simulate"}

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
            "mean_days": round(float(np.mean(times_array)), 2),
            "p50_days": round(float(np.percentile(times_array, 50)), 2),
            "p95_days": round(float(np.percentile(times_array, 95)), 2),
            "max_risk_days": round(float(np.max(times_array)), 2),
            "std_dev": round(float(np.std(times_array)), 2)
        }
