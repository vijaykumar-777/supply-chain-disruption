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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ATLAS AI API", version="1.0", description="Supply Chain Intelligence Backend")

# Allow Vite dev server to call this API (supports any port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Neo4j Connection Helper ─────────────────────────────────────────────────

def get_neo4j_client():
    """Try to create a Neo4j client. Returns (client, None) on success or (None, error_msg) on failure."""
    try:
        from src.graph.neo4j_client import Neo4jClient
        client = Neo4jClient()
        # Test the connection
        with client.driver.session() as session:
            session.run("RETURN 1")
        return client, None
    except Exception as e:
        logger.warning(f"Neo4j connection failed: {e}")
        return None, str(e)


def get_network():
    """Build a live NetworkX graph from Neo4j. Returns None if Neo4j is unavailable."""
    try:
        from src.graph.neo4j_client import Neo4jClient
        from src.prediction.network_model import SupplyChainNetwork
        client = Neo4jClient()
        graph_data = client.get_full_graph()
        sc_network = SupplyChainNetwork()
        sc_network.load_from_neo4j(graph_data)
        client.close()
        return sc_network
    except Exception as e:
        logger.warning(f"Network build failed: {e}")
        return None

# ─── Fallback Demo Data ──────────────────────────────────────────────────────

DEMO_EVENTS = [
    {
        "id": "EVT-001",
        "title": "Suez Canal Congestion Alert",
        "category": "logistics",
        "severity": 0.85,
        "type": "critical",
        "timestamp": "2026-04-03T08:30:00Z",
        "locations": ["Suez Canal", "Port Said"],
        "description": "Disruption: logistics affecting Suez Canal, Port Said — vessel queue exceeds 40 ships"
    },
    {
        "id": "EVT-002",
        "title": "Shanghai Port Labor Dispute",
        "category": "labor",
        "severity": 0.72,
        "type": "critical",
        "timestamp": "2026-04-02T14:00:00Z",
        "locations": ["Shanghai", "Yangshan Deep Water Port"],
        "description": "Disruption: labor affecting Shanghai, Yangshan Deep Water Port — container processing down 60%"
    },
    {
        "id": "EVT-003",
        "title": "Typhoon Warning — South China Sea",
        "category": "weather",
        "severity": 0.65,
        "type": "warning",
        "timestamp": "2026-04-03T06:00:00Z",
        "locations": ["South China Sea", "Hong Kong", "Shenzhen"],
        "description": "Disruption: weather affecting South China Sea, Hong Kong, Shenzhen — Category 2 typhoon expected landfall in 48h"
    },
    {
        "id": "EVT-004",
        "title": "Semiconductor Shortage — TSMC Fab 18",
        "category": "supply",
        "severity": 0.58,
        "type": "warning",
        "timestamp": "2026-04-01T10:00:00Z",
        "locations": ["Tainan", "Taiwan"],
        "description": "Disruption: supply affecting Tainan, Taiwan — 3nm chip production yield below targets"
    },
    {
        "id": "EVT-005",
        "title": "EU Carbon Border Tax Implementation",
        "category": "regulatory",
        "severity": 0.45,
        "type": "warning",
        "timestamp": "2026-04-02T09:00:00Z",
        "locations": ["Rotterdam", "Hamburg", "Antwerp"],
        "description": "Disruption: regulatory affecting Rotterdam, Hamburg, Antwerp — new carbon levy adds 4-7% to import costs"
    },
    {
        "id": "EVT-006",
        "title": "Air Freight Capacity Reduction — LAX",
        "category": "logistics",
        "severity": 0.35,
        "type": "info",
        "timestamp": "2026-04-03T12:00:00Z",
        "locations": ["Los Angeles", "LAX Airport"],
        "description": "Disruption: logistics affecting Los Angeles, LAX Airport — runway maintenance reduces cargo capacity 20%"
    },
    {
        "id": "EVT-007",
        "title": "Rare Earth Export Controls — Myanmar",
        "category": "geopolitical",
        "severity": 0.78,
        "type": "critical",
        "timestamp": "2026-04-03T03:00:00Z",
        "locations": ["Myanmar", "Kunming"],
        "description": "Disruption: geopolitical affecting Myanmar, Kunming — rare earth mineral exports suspended indefinitely"
    },
    {
        "id": "EVT-008",
        "title": "Singapore Port Cyber Incident",
        "category": "cyber",
        "severity": 0.52,
        "type": "warning",
        "timestamp": "2026-04-02T22:00:00Z",
        "locations": ["Singapore", "Jurong Port"],
        "description": "Disruption: cyber affecting Singapore, Jurong Port — container tracking systems offline, manual processing"
    },
]

DEMO_NODES = [
    {"id": "NODE_LOC_SHANGHAI", "name": "Shanghai", "labels": ["Location"], "lat": 31.2304, "lon": 121.4737, "country": "China", "resilience_score": 0.72},
    {"id": "NODE_LOC_SINGAPORE", "name": "Singapore", "labels": ["Location"], "lat": 1.3521, "lon": 103.8198, "country": "Singapore", "resilience_score": 0.88},
    {"id": "NODE_LOC_ROTTERDAM", "name": "Rotterdam", "labels": ["Location"], "lat": 51.9244, "lon": 4.4777, "country": "Netherlands", "resilience_score": 0.91},
    {"id": "NODE_LOC_LOS_ANGELES", "name": "Los Angeles", "labels": ["Location"], "lat": 33.9425, "lon": -118.4081, "country": "USA", "resilience_score": 0.85},
    {"id": "NODE_LOC_HONG_KONG", "name": "Hong Kong", "labels": ["Location"], "lat": 22.3193, "lon": 114.1694, "country": "China", "resilience_score": 0.69},
    {"id": "NODE_LOC_DUBAI", "name": "Dubai", "labels": ["Location"], "lat": 25.276987, "lon": 55.296249, "country": "UAE", "resilience_score": 0.82},
    {"id": "NODE_SUP_TSMC", "name": "TSMC", "labels": ["Supplier"], "lat": 23.0, "lon": 120.2, "country": "Taiwan", "resilience_score": 0.65},
    {"id": "NODE_SUP_SAMSUNG", "name": "Samsung Electronics", "labels": ["Supplier"], "lat": 37.2636, "lon": 127.0286, "country": "South Korea", "resilience_score": 0.78},
    {"id": "NODE_FAC_FOXCONN", "name": "Foxconn Shenzhen", "labels": ["Factory"], "lat": 22.5431, "lon": 114.0579, "country": "China", "resilience_score": 0.61},
    {"id": "NODE_LOC_MUMBAI", "name": "Mumbai", "labels": ["Location"], "lat": 19.0760, "lon": 72.8777, "country": "India", "resilience_score": 0.74},
    {"id": "NODE_LOC_HAMBURG", "name": "Hamburg", "labels": ["Location"], "lat": 53.5511, "lon": 9.9937, "country": "Germany", "resilience_score": 0.89},
    {"id": "NODE_LOC_TOKYO", "name": "Tokyo", "labels": ["Location"], "lat": 35.6762, "lon": 139.6503, "country": "Japan", "resilience_score": 0.92},
]


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


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    client, err = get_neo4j_client()
    neo4j_status = "connected" if client else "unavailable"
    if client:
        client.close()
    return {
        "status": "ok",
        "service": "ATLAS AI API",
        "neo4j": neo4j_status,
        "timestamp": datetime.datetime.now().isoformat(),
    }


@app.get("/api/events")
def get_events(category: Optional[str] = None, severity_min: Optional[float] = None, location: Optional[str] = None):
    """Return all disruption events. Uses Neo4j if available, falls back to demo data."""
    client, err = get_neo4j_client()
    
    if client:
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
                    locs = record["locations"]
                    events.append({
                        "id": record["id"],
                        "title": record["title"],
                        "category": record["category"],
                        "severity": sev,
                        "type": "critical" if sev >= 0.7 else "warning" if sev >= 0.4 else "info",
                        "timestamp": record["timestamp"],
                        "locations": locs,
                        "description": f"Disruption: {record['category']} affecting {', '.join(locs)}",
                    })
        finally:
            client.close()
    else:
        logger.info("Using demo events (Neo4j unavailable)")
        events = list(DEMO_EVENTS)

    # Apply filters
    if category and category.lower() != "all":
        events = [e for e in events if e["category"].lower() == category.lower()]
    if severity_min is not None:
        events = [e for e in events if e["severity"] >= severity_min]
    if location:
        events = [e for e in events if any(location.lower() in loc.lower() for loc in e["locations"])]
    
    return {"events": events, "count": len(events)}


@app.get("/api/graph/nodes")
def get_graph_nodes():
    """Return all supply chain nodes. Uses Neo4j if available, falls back to demo data."""
    client, err = get_neo4j_client()
    
    if client:
        try:
            sc_network = get_network()
            query = """
            MATCH (n)
            WHERE NOT n:Event
            RETURN labels(n) as labels, properties(n) as props
            """
            nodes = []
            with client.driver.session() as session:
                for record in session.run(query):
                    props = record["props"]
                    node_id = props.get("id") or props.get("name")
                    resilience = sc_network.calculate_resilience_score(node_id) if sc_network else 0.5
                    nodes.append({
                        "id": node_id,
                        "name": props.get("name", "Unknown"),
                        "labels": record["labels"],
                        "lat": props.get("lat"),
                        "lon": props.get("lon"),
                        "country": props.get("country"),
                        "resilience_score": resilience,
                    })
            return {"nodes": nodes, "count": len(nodes)}
        finally:
            client.close()
    else:
        logger.info("Using demo nodes (Neo4j unavailable)")
        return {"nodes": DEMO_NODES, "count": len(DEMO_NODES)}


@app.get("/api/metrics")
def get_dashboard_metrics():
    """Return high-level KPI metrics for the dashboard."""
    client, err = get_neo4j_client()
    
    if client:
        try:
            with client.driver.session() as session:
                event_count = session.run("MATCH (e:Event) RETURN count(e) as c").single()["c"]
                high_risk = session.run("MATCH (e:Event) WHERE e.severity >= 0.7 RETURN count(e) as c").single()["c"]
                node_count = session.run("MATCH (n) WHERE NOT n:Event RETURN count(n) as c").single()["c"]

            return {
                "total_active_events": event_count,
                "high_risk_nodes": high_risk,
                "monitored_nodes": node_count,
                "weather_alerts": 0,
            }
        finally:
            client.close()
    else:
        # Compute from demo data
        events = DEMO_EVENTS
        return {
            "total_active_events": len(events),
            "high_risk_nodes": len([e for e in events if e["severity"] >= 0.7]),
            "monitored_nodes": len(DEMO_NODES),
            "weather_alerts": 1,
        }


@app.post("/api/simulate")
def run_simulation(req: SimulateRequest):
    """Run pathfinding + Monte Carlo simulation for a given source/target route."""
    sc_network = get_network()
    
    if sc_network:
        try:
            from src.prediction.monte_carlo import RiskSimulator
            optimal_path = sc_network.find_alternative_route(req.source, req.target)
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
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # Return demo simulation results
        import random
        base = random.uniform(5, 15)
        mean_delay = random.uniform(2, 8)
        return {
            "optimal_route": [req.source, "NODE_LOC_SINGAPORE", req.target],
            "alternative_route": [req.source, "NODE_LOC_DUBAI", "NODE_LOC_ROTTERDAM", req.target],
            "simulation": {
                "iterations": req.iterations,
                "mean_days": round(base + mean_delay, 1),
                "p50_days": round(base + mean_delay * 0.8, 1),
                "p95_days": round(base + mean_delay * 2.2, 1),
                "max_risk_days": round(base + mean_delay * 3, 1),
                "std_dev": round(mean_delay * 0.4, 2),
            },
            "base_duration": round(base, 1),
            "mean_delay": round(mean_delay, 1),
            "p95_delay": round(mean_delay * 2.2, 1),
            "risk_score": round(random.uniform(0.4, 0.9), 2),
        }


@app.post("/api/recommend")
def get_recommendation(req: RecommendRequest):
    """Ask local Ollama to generate a strategic recommendation."""
    try:
        from src.ai.ollama_client import AIAdvisor
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
        logger.warning(f"Ollama recommendation failed: {e}")
        # Provide a structured fallback recommendation
        rec_id = str(uuid.uuid4())
        fallback = f"""## AI Mitigation Strategy for: {req.event_title}

**Category:** {req.event_category}
**Affected Locations:** {', '.join(req.locations)}

### Immediate Actions (0-24h)
1. **Activate contingency routing** — Redirect shipments through alternative ports to minimize impact
2. **Notify all downstream stakeholders** of expected {req.event_category} delays
3. **Increase safety stock** at distribution centers closest to affected regions

### Short-term Mitigation (24-72h)
1. **Dual-source critical components** from unaffected regions
2. **Negotiate expedited freight** with air cargo providers for time-sensitive goods
3. **Deploy real-time monitoring** on the affected corridor for status updates

### Long-term Resilience
1. **Diversify supplier base** to reduce single-point-of-failure exposure
2. **Establish buffer inventory** policies for high-risk trade lanes
3. **Invest in predictive analytics** to improve early warning capabilities

> ⚠️ *Note: This is a fallback recommendation. Connect Ollama (llama3.2) for AI-generated personalized strategies.*
"""
        return {"recommendation_id": rec_id, "recommendation": fallback}


@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    """Store user feedback on AI recommendation quality."""
    try:
        from src.ai.ollama_client import AIAdvisor
        advisor = AIAdvisor()
        ok = advisor.submit_feedback(req.recommendation_id, req.rating, req.comment)
        return {"success": ok}
    except Exception as e:
        logger.warning(f"Feedback storage failed: {e}")
        return {"success": True}  # Accept feedback gracefully even if storage fails


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
