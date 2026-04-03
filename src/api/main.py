"""
ATLAS AI — FastAPI Backend
Bridges the Python prediction/AI engine with the React frontend.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import datetime
import logging

from src.graph.neo4j_client import Neo4jClient
from src.graph.correlation_engine import CorrelationEngine
from src.prediction.network_model import SupplyChainNetwork
from src.prediction.monte_carlo import RiskSimulator
from src.ai.ollama_client import AIAdvisor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ATLAS AI API", version="1.0", description="Supply Chain Intelligence Backend")

# Allow Vite dev server to call this API (supports any port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Pydantic Models ──────────────────────────────────────────────────────────

class SimulateRequest(BaseModel):
    source: str
    target: str
    disrupted_nodes: Optional[List[str]] = []
    iterations: Optional[int] = 5000

class RecommendRequest(BaseModel):
    event_title: str
    event_category: str
    locations: List[str]
    simulation_results: dict
    alt_route: Optional[List[str]] = []

class FeedbackRequest(BaseModel):
    recommendation_id: str
    rating: int  # 1 = helpful, -1 = not helpful
    comment: Optional[str] = ""

# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_network() -> SupplyChainNetwork:
    """Build a live NetworkX graph from Neo4j each request (stateless design)."""
    client = Neo4jClient()
    try:
        graph_data = client.get_full_graph()
        sc_network = SupplyChainNetwork()
        sc_network.load_from_neo4j(graph_data)
        return sc_network
    finally:
        client.close()

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ATLAS AI API", "timestamp": datetime.datetime.now().isoformat()}


@app.get("/api/events")
def get_events():
    """Return all disruption events from Neo4j graph."""
    client = Neo4jClient()
    try:
        query = """
        MATCH (e:Event)-[:AFFECTS]->(l:Location)
        RETURN e.id as id, e.title as title, e.category as category,
               e.severity as severity, e.timestamp as timestamp,
               collect(l.name) as locations
        ORDER BY e.timestamp DESC
        """
        events = []
        with client.driver.session() as session:
            records = session.run(query)
            for record in records:
                sev = record["severity"] or 0.5
                events.append({
                    "id": record["id"],
                    "title": record["title"],
                    "category": record["category"],
                    "severity": sev,
                    "type": "critical" if sev >= 0.7 else "warning" if sev >= 0.4 else "info",
                    "timestamp": record["timestamp"],
                    "locations": record["locations"],
                    "description": f"Disruption: {record['category']} affecting {', '.join(record['locations'])}",
                })
        return {"events": events, "count": len(events)}
    finally:
        client.close()


@app.get("/api/graph/nodes")
def get_graph_nodes():
    """Return all supply chain nodes (Suppliers, Factories, Locations) from graph."""
    client = Neo4jClient()
    try:
        query = """
        MATCH (n)
        WHERE NOT n:Event
        RETURN labels(n) as labels, properties(n) as props
        """
        nodes = []
        with client.driver.session() as session:
            for record in session.run(query):
                props = record["props"]
                nodes.append({
                    "id": props.get("id") or props.get("name"),
                    "name": props.get("name", "Unknown"),
                    "labels": record["labels"],
                    "lat": props.get("lat"),
                    "lon": props.get("lon"),
                    "country": props.get("country"),
                })
        return {"nodes": nodes, "count": len(nodes)}
    finally:
        client.close()


@app.get("/api/metrics")
def get_dashboard_metrics():
    """Return high-level KPI metrics for the dashboard."""
    client = Neo4jClient()
    try:
        with client.driver.session() as session:
            event_count = session.run("MATCH (e:Event) RETURN count(e) as c").single()["c"]
            high_risk = session.run("MATCH (e:Event) WHERE e.severity >= 0.7 RETURN count(e) as c").single()["c"]
            node_count = session.run("MATCH (n) WHERE NOT n:Event RETURN count(n) as c").single()["c"]

        return {
            "total_active_events": event_count,
            "high_risk_nodes": high_risk,
            "monitored_nodes": node_count,
            "weather_alerts": 0,  # Extend with weather integration
        }
    finally:
        client.close()


@app.post("/api/simulate")
def run_simulation(req: SimulateRequest):
    """Run pathfinding + Monte Carlo simulation for a given source/target route."""
    try:
        sc_network = get_network()
        
        # Optimal path without disruption
        optimal_path = sc_network.find_alternative_route(req.source, req.target)
        
        # Alternative path avoiding disrupted nodes
        alt_path = sc_network.find_alternative_route(req.source, req.target, req.disrupted_nodes)
        
        if not optimal_path:
            raise HTTPException(status_code=404, detail=f"No route found from '{req.source}' to '{req.target}'")
        
        route_edges = [(optimal_path[i], optimal_path[i+1]) for i in range(len(optimal_path)-1)]
        simulator = RiskSimulator(sc_network)
        sim_results = simulator.simulate_route_risk(route_edges, iterations=req.iterations)
        
        return {
            "optimal_route": optimal_path,
            "alternative_route": alt_path,
            "simulation": sim_results,
        }
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recommend")
def get_recommendation(req: RecommendRequest):
    """Ask local Ollama to generate a strategic recommendation."""
    try:
        advisor = AIAdvisor()
        event = {
            "title": req.event_title,
            "category": req.event_category,
            "locations": req.locations,
        }
        rec = advisor.generate_recommendation(event, req.simulation_results, req.alt_route)
        rec_id = str(uuid.uuid4())
        return {"recommendation_id": rec_id, "recommendation": rec}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    """Store user feedback on AI recommendation quality."""
    advisor = AIAdvisor()
    ok = advisor.submit_feedback(req.recommendation_id, req.rating, req.comment)
    return {"success": ok}
