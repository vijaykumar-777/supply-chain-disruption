"""
ReliefRoute Karnataka - FastAPI backend.
Bridges weather, graph routing, and relief logistics workflows with the React frontend.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import List, Optional
import uuid
import datetime
import logging
import time
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.monitoring.supply_chain_monitor import SupplyChainMonitor
from src.ingestion.company_intelligence import CompanyIntelligenceService
from src.config import ATLAS_MODE
from src.relief.reference_data import load_reference_data, road_network_bytes
from src.relief.live_disasters import collect_live_disasters
from src.relief.neo4j_seed import seed_reference_graph

app = FastAPI(
    title="ReliefRoute Karnataka API",
    version="2.0",
    description="Flood and landslide relief logistics backend for Karnataka",
)
monitor_service = SupplyChainMonitor()
company_intelligence_service = CompanyIntelligenceService()

# ─── Explicit Demo Data (Only used when ATLAS_MODE=demo) ─────────────────────

DEMO_EVENTS = [
    {
        "id": "rain-kodagu-001",
        "title": "Very Heavy Rainfall Alert: Kodagu Ghats",
        "category": "Weather",
        "severity": 0.86,
        "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat(),
        "locations": ["Madikeri", "Kodagu", "Western Ghats"],
        "description": "Sustained rainfall over steep ghat roads raises landslide and waterlogging risk on relief access routes.",
        "type": "critical",
    },
    {
        "id": "landslide-shiradi-002",
        "title": "Landslide Watch: Shiradi Ghat Section",
        "category": "Landslide",
        "severity": 0.74,
        "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=5)).isoformat(),
        "locations": ["Sakleshpur", "Shiradi Ghat", "Hassan"],
        "description": "Slope instability may block the main road corridor between Hassan and Mangaluru relief staging areas.",
        "type": "critical",
    },
    {
        "id": "flood-udupi-003",
        "title": "Coastal Waterlogging Risk: Udupi District",
        "category": "Flood",
        "severity": 0.62,
        "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat(),
        "locations": ["Udupi", "Kundapura", "Coastal Karnataka"],
        "description": "Low-lying roads near coastal settlements may slow last-mile relief truck movement.",
        "type": "warning",
    },
]

DEMO_RELIEF_NODES = [
    {"id": "HUB_BENGALURU", "name": "Bengaluru Relief Hub", "labels": ["ReliefHub"], "lat": 12.9716, "lon": 77.5946, "country": "Karnataka", "resilience_score": 0.92},
    {"id": "HUB_MANGALURU", "name": "Mangaluru Coastal Hub", "labels": ["ReliefHub"], "lat": 12.9141, "lon": 74.8560, "country": "Karnataka", "resilience_score": 0.78},
    {"id": "TOWN_MADIKERI", "name": "Madikeri", "labels": ["Town"], "lat": 12.4244, "lon": 75.7382, "country": "Karnataka", "resilience_score": 0.46},
    {"id": "VILLAGE_BHAGAMANDALA", "name": "Bhagamandala", "labels": ["Village"], "lat": 12.3861, "lon": 75.5291, "country": "Karnataka", "resilience_score": 0.32},
    {"id": "TOWN_SAKLESHPUR", "name": "Sakleshpur", "labels": ["Town"], "lat": 12.9442, "lon": 75.7848, "country": "Karnataka", "resilience_score": 0.41},
    {"id": "VILLAGE_KOLLUR", "name": "Kollur", "labels": ["Village"], "lat": 13.8667, "lon": 74.8167, "country": "Karnataka", "resilience_score": 0.37},
    {"id": "TOWN_UDUPI", "name": "Udupi", "labels": ["Town"], "lat": 13.3409, "lon": 74.7421, "country": "Karnataka", "resilience_score": 0.55},
]

DEMO_RELIEF_LINKS = [
    {"source_id": "HUB_BENGALURU", "target_id": "TOWN_SAKLESHPUR", "rel_type": "RELIEF_ROAD"},
    {"source_id": "TOWN_SAKLESHPUR", "target_id": "HUB_MANGALURU", "rel_type": "RELIEF_ROAD"},
    {"source_id": "TOWN_SAKLESHPUR", "target_id": "TOWN_MADIKERI", "rel_type": "GHAT_ROAD"},
    {"source_id": "TOWN_MADIKERI", "target_id": "VILLAGE_BHAGAMANDALA", "rel_type": "VILLAGE_ACCESS"},
    {"source_id": "HUB_MANGALURU", "target_id": "TOWN_UDUPI", "rel_type": "COASTAL_ROAD"},
    {"source_id": "TOWN_UDUPI", "target_id": "VILLAGE_KOLLUR", "rel_type": "VILLAGE_ACCESS"},
]

DEMO_NODES = len(DEMO_RELIEF_NODES)

OPERATIONAL_NODE_WHERE = "NOT n:Event AND NOT n:Filing AND NOT n:Ticker AND NOT n:Regulator AND NOT n:Country"
_runtime_mode = ATLAS_MODE


def is_demo_mode() -> bool:
    return _runtime_mode == "demo"


def current_mode() -> str:
    return _runtime_mode

# ─── Fix #3: Harden CORS — environment-driven allowlist ─────────────────────
ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
).split(",")

# When explicit origins are set, credentials are safe. With wildcard, disable credentials.
_is_dev = os.getenv("ATLAS_ENV", "development") == "development"
if _is_dev and not os.getenv("CORS_ALLOWED_ORIGINS"):
    # Development fallback — permissive but without credentials
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Fix #3: wildcard + credentials is invalid per spec
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ─── Fix #8: Neo4j Connection Lifecycle — cache with TTL ────────────────────

_neo4j_cache = {"client": None, "healthy": False, "last_check": 0.0, "last_error": ""}
_NEO4J_CHECK_TTL = 30  # seconds between re-check attempts when unhealthy


def get_neo4j_client():
    """Try to create/reuse a Neo4j client. Returns (client, None) or (None, error_msg).
    Implements TTL caching to avoid hammering a down database (Fix #8)."""
    now = time.time()

    # If we recently failed, don't retry yet — reduce log spam
    if not _neo4j_cache["healthy"] and (now - _neo4j_cache["last_check"]) < _NEO4J_CHECK_TTL:
        return None, _neo4j_cache["last_error"]

    try:
        from src.graph.neo4j_client import Neo4jClient
        client = Neo4jClient()
        with client.driver.session() as session:
            session.run("RETURN 1")
        _neo4j_cache.update(client=client, healthy=True, last_check=now, last_error="")
        return client, None
    except Exception as e:
        err = str(e)
        # Only log if it's a new error or enough time has passed (Fix #8: reduce spam)
        if err != _neo4j_cache["last_error"]:
            logger.warning(f"Neo4j connection failed: {e}")
        _neo4j_cache.update(client=None, healthy=False, last_check=now, last_error=err)
        return None, err


def get_network():
    """Build a live NetworkX graph from Neo4j. Returns None if unavailable."""
    client = None
    try:
        from src.graph.neo4j_client import Neo4jClient
        from src.prediction.network_model import SupplyChainNetwork
        client = Neo4jClient()
        graph_data = client.get_full_graph()
        sc_network = SupplyChainNetwork()
        sc_network.load_from_neo4j(graph_data)
        return sc_network
    except Exception as e:
        logger.warning(f"Network build failed: {e}")
        return None
    finally:
        # Fix #8: ensure client always closes
        if client:
            try:
                client.close()
            except Exception:
                pass

# ─── Pydantic Models (Fix #2: input validation, Fix #5: feedback contract) ───

class SimulateRequest(BaseModel):
    source: str
    target: str
    disrupted_nodes: Optional[List[str]] = []
    iterations: Optional[int] = 5000

    # Fix #2: Enforce iterations > 0
    @field_validator("iterations")
    @classmethod
    def iterations_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("iterations must be greater than 0")
        if v is not None and v > 100000:
            raise ValueError("iterations must not exceed 100000")
        return v

    @field_validator("source", "target")
    @classmethod
    def nodes_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("node ID must not be empty")
        return v.strip()

class RecommendRequest(BaseModel):
    event_title: str
    event_category: str
    locations: List[str]
    simulation_results: dict
    alt_route: Optional[List[str]] = []

class FeedbackRequest(BaseModel):
    recommendation_id: str
    rating: int  # Fix #5: 1 = helpful, -1 = not helpful (normalized contract)
    comment: Optional[str] = ""

    @field_validator("rating")
    @classmethod
    def rating_must_be_valid(cls, v):
        if v not in (1, -1):
            raise ValueError("rating must be 1 (helpful) or -1 (not helpful)")
        return v


class ModeRequest(BaseModel):
    mode: str

    @field_validator("mode")
    @classmethod
    def mode_must_be_valid(cls, v):
        mode = str(v).strip().lower()
        if mode not in {"live", "demo"}:
            raise ValueError("mode must be either 'live' or 'demo'")
        return mode


class CompanyImportSelection(BaseModel):
    lei: Optional[str] = None
    cik: Optional[str] = None
    name: Optional[str] = None
    ticker: Optional[str] = None

    @field_validator("lei", "cik", "name", "ticker", mode="before")
    @classmethod
    def strip_optional_strings(cls, value):
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None


class CompanyImportRequest(BaseModel):
    companies: List[CompanyImportSelection]

    @field_validator("companies")
    @classmethod
    def validate_companies(cls, value):
        if not value:
            raise ValueError("At least one company selection is required")
        return value


class CompanyBulkImportRequest(BaseModel):
    company_names: List[str]

    @field_validator("company_names")
    @classmethod
    def validate_company_names(cls, value):
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        if not cleaned:
            raise ValueError("At least one company name is required")
        return cleaned


class SeedReferenceRequest(BaseModel):
    clear_existing: bool = False


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    client, err = get_neo4j_client()
    neo4j_status = "connected" if client else "unavailable"
    if client:
        try:
            client.close()
        except Exception:
            pass
    return {
        "status": "ok",
        "service": "ReliefRoute Karnataka API",
        "mode": current_mode(),
        "neo4j": neo4j_status,
        "timestamp": datetime.datetime.now().isoformat(),
    }


@app.get("/api/mode")
def get_mode():
    return {
        "mode": current_mode(),
        "source_policy": "demo and live are mutually exclusive; demo data is only returned in demo mode",
    }


@app.post("/api/mode")
def set_mode(req: ModeRequest):
    global _runtime_mode
    _runtime_mode = req.mode
    _neo4j_cache.update(client=None, healthy=False, last_check=0.0, last_error="")
    return {
        "mode": current_mode(),
        "source_policy": "demo and live are mutually exclusive; demo data is only returned in demo mode",
    }


@app.get("/api/events")
def get_events(category: Optional[str] = None, severity_min: Optional[float] = None, location: Optional[str] = None):
    """Return active flood, landslide, and road-disruption events.

    Live mode never silently substitutes demo data. Demo data is returned only
    when ATLAS_MODE=demo so dashboards can clearly label synthetic scenarios.
    """
    client, err = get_neo4j_client()
    source = "live"
    events = []

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
            
            if not events and is_demo_mode():
                logger.info("Neo4j is empty of events. Using explicit demo relief events.")
                events = list(DEMO_EVENTS)
                source = "demo"
        finally:
            client.close()
    else:
        source = "unavailable"
        logger.info("No live event data available: %s", err)
        if is_demo_mode():
            events = list(DEMO_EVENTS)
            source = "demo"

    # Apply filters
    if category and category.lower() != "all":
        events = [e for e in events if e["category"].lower() == category.lower()]
    if severity_min is not None:
        events = [e for e in events if e["severity"] >= severity_min]
    if location:
        events = [e for e in events if any(location.lower() in loc.lower() for loc in e["locations"])]

    return {"events": events, "count": len(events), "source": source}  # Fix #10


@app.get("/api/graph/nodes")
def get_graph_nodes():
    """Return relief hubs, settlements, road points, and road links."""
    client, err = get_neo4j_client()
    source = "live"

    if client:
        try:
            import random
            sc_network = get_network()
            
            # Fetch nodes, joining with Location for Companies based on the 'country' property
            query_nodes = """
            MATCH (n)
            WHERE NOT n:Event AND NOT n:Filing AND NOT n:Ticker AND NOT n:Regulator AND NOT n:Country
            OPTIONAL MATCH (l:Location {name: n.country})
            RETURN labels(n) as labels, properties(n) as props, properties(l) as loc_props
            """
            nodes = []
            nodes_by_id = {}
            with client.driver.session() as session:
                for record in session.run(query_nodes):
                    props = record["props"]
                    loc_props = record["loc_props"] or {}
                    
                    node_id = props.get("id") or props.get("name")
                    is_company = "Company" in record["labels"]
                    
                    lat = props.get("lat") or loc_props.get("lat")
                    lon = props.get("lon") or loc_props.get("lon")
                    
                    # Add jitter for companies so they don't perfectly overlap
                    if is_company and lat is not None and lon is not None:
                        lat += random.uniform(-1.0, 1.0)
                        lon += random.uniform(-1.0, 1.0)
                        
                    resilience = sc_network.calculate_resilience_score(node_id) if sc_network else 0.5
                    
                    node_data = {
                        "id": node_id,
                        "name": props.get("name", "Unknown"),
                        "labels": record["labels"],
                        "lat": lat,
                        "lon": lon,
                        "country": props.get("country") or loc_props.get("country"),
                        "resilience_score": resilience,
                    }
                    nodes.append(node_data)
                    nodes_by_id[node_id] = node_data

            # Fetch links/relationships
            query_links = """
            MATCH (source)-[r:ROUTES_TO]->(target)
            RETURN properties(source).id as source_id, properties(source).name as source_name,
                   properties(target).id as target_id, properties(target).name as target_name,
                   type(r) as rel_type
            """
            links = []
            with client.driver.session() as session:
                for record in session.run(query_links):
                    source_id = record["source_id"] or record["source_name"]
                    target_id = record["target_id"] or record["target_name"]
                    
                    if source_id in nodes_by_id and target_id in nodes_by_id:
                        s_node = nodes_by_id[source_id]
                        t_node = nodes_by_id[target_id]
                        
                        # Only include link if we can draw it (both nodes have coords)
                        if s_node.get("lat") is not None and s_node.get("lon") is not None and t_node.get("lat") is not None and t_node.get("lon") is not None:
                            links.append({
                                "source_id": source_id,
                                "target_id": target_id,
                                "rel_type": record["rel_type"]
                            })

            return {"nodes": nodes, "links": links, "count": len(nodes), "source": source}
        finally:
            client.close()
    else:
        source = "unavailable"
        logger.info("No live graph nodes available: %s", err)
        if is_demo_mode():
            return {
                "nodes": DEMO_RELIEF_NODES,
                "links": DEMO_RELIEF_LINKS,
                "count": len(DEMO_RELIEF_NODES),
                "source": "demo",
            }
        return {"nodes": [], "links": [], "count": 0, "source": source}


@app.get("/api/metrics")
def get_dashboard_metrics():
    """Return high-level KPI metrics for the dashboard."""
    client, err = get_neo4j_client()
    source = "live"

    if client:
        try:
            with client.driver.session() as session:
                event_count = session.run("MATCH (e:Event) RETURN count(e) as c").single()["c"]
                high_risk = session.run("MATCH (e:Event) WHERE e.severity >= 0.7 RETURN count(e) as c").single()["c"]
                node_count = session.run(
                    f"MATCH (n) WHERE {OPERATIONAL_NODE_WHERE} RETURN count(n) as c"
                ).single()["c"]

            if event_count == 0 and is_demo_mode():
                logger.info("Metrics: Empty DB. Using explicit demo relief counts.")
                return {
                    "total_active_events": len(DEMO_EVENTS),
                    "high_risk_nodes": len([e for e in DEMO_EVENTS if e["type"] == "critical"]),
                    "monitored_nodes": node_count if node_count > 0 else DEMO_NODES,
                    "weather_alerts": 1,
                    "source": "demo",
                }

            return {
                "total_active_events": event_count,
                "high_risk_nodes": high_risk,
                "monitored_nodes": node_count,
                "weather_alerts": 0,
                "source": source,  # Fix #10
            }
        finally:
            client.close()
    else:
        source = "unavailable"
        if is_demo_mode():
            return {
                "total_active_events": len(DEMO_EVENTS),
                "high_risk_nodes": len([e for e in DEMO_EVENTS if e["type"] == "critical"]),
                "monitored_nodes": DEMO_NODES,
                "weather_alerts": 2,
                "source": "demo",
            }
        return {
            "total_active_events": 0,
            "high_risk_nodes": 0,
            "monitored_nodes": 0,
            "weather_alerts": 0,
            "source": source,  # Fix #10
        }


@app.post("/api/simulate")
def run_simulation(req: SimulateRequest):
    """Run pathfinding + Monte Carlo simulation for a given source/target route.
    Fix #2: validates iterations > 0 via Pydantic, validates node existence."""
    sc_network = get_network()

    if sc_network:
        try:
            from src.prediction.monte_carlo import RiskSimulator
            import networkx as nx

            # Fix #2: Validate source/target exist in the graph
            if req.source not in sc_network.graph:
                raise HTTPException(status_code=400, detail=f"Source node '{req.source}' not found in the relief logistics network")
            if req.target not in sc_network.graph:
                raise HTTPException(status_code=400, detail=f"Target node '{req.target}' not found in the relief logistics network")

            try:
                optimal_path = sc_network.find_alternative_route(req.source, req.target)
            except nx.NodeNotFound as e:
                raise HTTPException(status_code=400, detail=f"Node not found: {e}")

            try:
                alt_path = sc_network.find_alternative_route(req.source, req.target, req.disrupted_nodes)
            except nx.NodeNotFound:
                alt_path = []

            if not optimal_path:
                raise HTTPException(status_code=404, detail=f"No route found from '{req.source}' to '{req.target}'")

            route_edges = [(optimal_path[i], optimal_path[i+1]) for i in range(len(optimal_path)-1)]
            simulator = RiskSimulator(sc_network)
            sim_results = simulator.simulate_route_risk(route_edges, iterations=req.iterations)

            return {
                "optimal_route": optimal_path,
                "alternative_route": alt_path,
                "simulation": sim_results,
                "source": "live",  # Fix #10
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    elif is_demo_mode():
        import networkx as nx

        graph = nx.DiGraph()
        for node in DEMO_RELIEF_NODES:
            graph.add_node(node["id"], **node)
        for link in DEMO_RELIEF_LINKS:
            graph.add_edge(link["source_id"], link["target_id"], weight=1.0, rel_type=link["rel_type"])
            graph.add_edge(link["target_id"], link["source_id"], weight=1.15, rel_type=link["rel_type"])

        if req.source not in graph:
            raise HTTPException(status_code=400, detail=f"Source node '{req.source}' not found in the relief logistics network")
        if req.target not in graph:
            raise HTTPException(status_code=400, detail=f"Target node '{req.target}' not found in the relief logistics network")

        disrupted_lookup = {item.lower() for item in req.disrupted_nodes}
        disrupted_node_ids = [
            node["id"]
            for node in DEMO_RELIEF_NODES
            if any(term in node["name"].lower() or node["name"].lower() in term for term in disrupted_lookup)
        ]

        try:
            optimal_path = nx.shortest_path(graph, source=req.source, target=req.target, weight="weight")
        except nx.NetworkXNoPath:
            raise HTTPException(status_code=404, detail=f"No relief route found from '{req.source}' to '{req.target}'")

        safe_graph = graph.copy()
        safe_graph.remove_nodes_from([node_id for node_id in disrupted_node_ids if node_id not in {req.source, req.target}])
        try:
            alternative_path = nx.shortest_path(safe_graph, source=req.source, target=req.target, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            alternative_path = []

        disrupted_penalty = max(len(disrupted_node_ids), 1 if req.disrupted_nodes else 0)
        mean_days = round(max(len(optimal_path) - 1, 1) * (1.2 + 0.35 * disrupted_penalty), 2)
        return {
            "optimal_route": optimal_path,
            "alternative_route": alternative_path,
            "simulation": {
                "iterations": req.iterations,
                "mean_days": mean_days,
                "p50_days": round(mean_days * 0.88, 2),
                "p95_days": round(mean_days * 1.65, 2),
                "max_risk_days": round(mean_days * 2.1, 2),
                "std_dev": round(mean_days * 0.22, 2),
            },
            "source": "demo",
            "explanation": {
                "triggered_by": req.disrupted_nodes,
                "blocked_nodes": disrupted_node_ids,
                "assumption": "Demo mode uses fixed Karnataka relief corridors and deterministic rainfall disruption penalties.",
            },
        }
    else:
        raise HTTPException(status_code=503, detail="Live relief logistics graph is unavailable. Load real road, hub, and village data into Neo4j before running simulations.")


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
        raise HTTPException(status_code=503, detail="Local AI recommendation service is unavailable. Start Ollama to generate recommendations.")


@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    """Store user feedback on AI recommendation quality.
    Fix #5: rating validated to 1/-1 via Pydantic.
    Fix #7: returns success: false on storage failure instead of lying."""
    try:
        from src.ai.ollama_client import AIAdvisor
        advisor = AIAdvisor()
        ok = advisor.submit_feedback(req.recommendation_id, req.rating, req.comment)
        if not ok:
            # Fix #7: honest failure reporting
            return {"success": False, "error": "Feedback storage failed"}
        return {"success": True}
    except Exception as e:
        logger.warning(f"Feedback storage failed: {e}")
        # Fix #7: do NOT report success when it failed
        return {"success": False, "error": str(e)}


@app.post("/api/ingest/events")
def trigger_event_ingestion():
    """Trigger an immediate ingestion of real-time alerts from GDELT and weather sources directly into Neo4j."""
    client, err = get_neo4j_client()
    if not client:
        raise HTTPException(status_code=503, detail=f"Neo4j is unavailable: {err}")
    
    try:
        snapshots = monitor_service.list_snapshots()
        if not snapshots:
            raise HTTPException(status_code=400, detail="No relief road network available for alert context. Please upload network data first.")
            
        latest_snapshot_id = snapshots[0]["snapshot_id"]
        snapshot = monitor_service.load_snapshot(latest_snapshot_id)
        
        alerts, source_status = monitor_service._collect_alerts(snapshot)
        
        inserted_count = 0
        for alert in alerts:
            client.insert_event(alert)
            inserted_count += 1
            
        return {
            "success": True,
            "inserted_events": inserted_count,
            "source_status": source_status
        }
    except Exception as e:
        logger.error(f"Event ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            client.close()
        except:
            pass


@app.get("/api/company-intel/search")
def search_company_intelligence(q: str, limit: int = 8):
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty")

    try:
        return company_intelligence_service.search_companies(query, limit=max(1, min(limit, 25)))
    except Exception as e:
        logger.error(f"Company intelligence search failed: {e}")
        raise HTTPException(status_code=503, detail="Live company intelligence sources are unavailable right now")


@app.post("/api/company-intel/import")
def import_company_intelligence(req: CompanyImportRequest):
    client, err = get_neo4j_client()
    if not client:
        raise HTTPException(status_code=503, detail=f"Neo4j is unavailable: {err}")

    try:
        client.load_schema()
        imported = company_intelligence_service.import_companies(
            [company.model_dump(exclude_none=True) for company in req.companies],
            client,
        )
        return {"imported": imported, "count": len(imported), "source": "live"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Company intelligence import failed: {e}")
        raise HTTPException(status_code=503, detail="Failed to import live company data into Neo4j")
    finally:
        try:
            client.close()
        except Exception:
            pass


@app.post("/api/company-intel/import-bulk")
def import_company_intelligence_bulk(req: CompanyBulkImportRequest):
    client, err = get_neo4j_client()
    if not client:
        raise HTTPException(status_code=503, detail=f"Neo4j is unavailable: {err}")

    try:
        client.load_schema()
        result = company_intelligence_service.import_company_names(req.company_names, client)
        return {
            "imported": result["imported"],
            "skipped": result["skipped"],
            "count": len(result["imported"]),
            "skipped_count": len(result["skipped"]),
            "source": "live",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Bulk company intelligence import failed: {e}")
        raise HTTPException(status_code=503, detail="Failed to bulk import live company data into Neo4j")
    finally:
        try:
            client.close()
        except Exception:
            pass


@app.get("/api/supply-chain/template")
@app.get("/api/relief/template")
def get_supply_chain_template():
    return monitor_service.template()


@app.get("/api/relief/reference-data")
def get_relief_reference_data():
    return load_reference_data()


@app.post("/api/relief/load-reference")
def load_relief_reference_network():
    original_geocode = monitor_service._geocode_location
    original_gdelt = monitor_service._fetch_gdelt_alerts
    original_weather = monitor_service._fetch_weather_alerts
    try:
        monitor_service._geocode_location = lambda *_args, **_kwargs: None
        monitor_service._fetch_gdelt_alerts = lambda _snapshot: []
        monitor_service._fetch_weather_alerts = lambda _snapshot: []
        snapshot = monitor_service.parse_upload("01_road_network.csv", road_network_bytes())
        return monitor_service.build_report(snapshot)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="01_road_network.csv was not found in the project root")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Reference relief network load failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to load reference relief road network")
    finally:
        monitor_service._geocode_location = original_geocode
        monitor_service._fetch_gdelt_alerts = original_gdelt
        monitor_service._fetch_weather_alerts = original_weather


@app.post("/api/relief/seed-reference-graph")
def seed_reference_relief_graph(req: SeedReferenceRequest):
    client, err = get_neo4j_client()
    if not client:
        raise HTTPException(status_code=503, detail=f"Neo4j is unavailable: {err}")

    try:
        result = seed_reference_graph(client, clear_existing=req.clear_existing)
        _neo4j_cache.update(client=None, healthy=False, last_check=0.0, last_error="")
        return result
    except Exception as e:
        logger.error(f"Reference graph seed failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to seed Neo4j with reference relief graph")
    finally:
        try:
            client.close()
        except Exception:
            pass


@app.get("/api/relief/snapshots/{snapshot_id}/export")
def export_supply_chain_snapshot(snapshot_id: str, format: str = "json"):
    try:
        snapshot = monitor_service.load_snapshot(snapshot_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Relief network snapshot not found")

    report = snapshot.get("latest_report") or monitor_service.build_report(snapshot)
    export_format = format.strip().lower()
    filename_base = f"reliefroute-{snapshot_id}"
    if export_format == "json":
        import json
        return Response(
            content=json.dumps(report, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.json"'},
        )
    if export_format != "csv":
        raise HTTPException(status_code=400, detail="format must be json or csv")

    import csv
    import io

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "route_id",
            "route_name",
            "status",
            "risk_score",
            "source",
            "target",
            "origin",
            "destination",
            "priority",
            "matched_alerts",
            "downstream_settlements",
            "alternative_route",
        ],
    )
    writer.writeheader()
    for link in report.get("impacted_links", []):
        writer.writerow(
            {
                "route_id": link.get("route_id"),
                "route_name": link.get("route_name"),
                "status": link.get("status"),
                "risk_score": link.get("risk_score"),
                "source": link.get("source_company"),
                "target": link.get("target_company"),
                "origin": link.get("origin"),
                "destination": link.get("destination"),
                "priority": link.get("criticality"),
                "matched_alerts": " | ".join(alert.get("alert_title", "") for alert in link.get("matched_alerts", [])),
                "downstream_settlements": " | ".join(link.get("downstream_companies", [])),
                "alternative_route": (link.get("alternative_route") or {}).get("summary"),
            }
        )
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename_base}.csv"'},
    )


@app.get("/api/disasters/live")
def get_live_disasters():
    try:
        return collect_live_disasters()
    except Exception as e:
        logger.error(f"Live disaster aggregation failed: {e}")
        raise HTTPException(status_code=503, detail="Failed to collect live disaster alerts")


@app.get("/api/supply-chain/snapshots")
@app.get("/api/relief/snapshots")
def list_supply_chain_snapshots():
    return {"snapshots": monitor_service.list_snapshots()}


@app.post("/api/supply-chain/upload")
@app.post("/api/relief/upload")
async def upload_supply_chain_file(request: Request):
    filename = request.headers.get("x-filename", "")
    if not filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename")

    try:
        content = await request.body()
        snapshot = monitor_service.parse_upload(filename, content)
        return monitor_service.build_report(snapshot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Relief network upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process uploaded relief road network file")


@app.get("/api/supply-chain/snapshots/{snapshot_id}")
@app.get("/api/relief/snapshots/{snapshot_id}")
def get_supply_chain_snapshot(snapshot_id: str, refresh: bool = True):
    try:
        snapshot = monitor_service.load_snapshot(snapshot_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Relief network snapshot not found")

    if not refresh and snapshot.get("latest_report"):
        return snapshot["latest_report"]

    try:
        return monitor_service.build_report(snapshot)
    except Exception as e:
        logger.error(f"Relief network refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh relief logistics report")


# ─── Hospital Network Endpoints ───────────────────────────────────────────────

from src.relief.hospital_network import hospital_network_service

class RouteOptimizationRequest(BaseModel):
    source_hospital_id: str
    target_hospital_id: str
    strategy: Optional[str] = "shortest"  # shortest, fastest, safest

    @field_validator("source_hospital_id", "target_hospital_id")
    @classmethod
    def hospital_id_must_not_be_empty(cls, v):
        if not v or not str(v).strip():
            raise ValueError("hospital ID must not be empty")
        return str(v).strip()

    @field_validator("strategy", mode="before")
    @classmethod
    def validate_strategy(cls, v):
        v = str(v or "shortest").strip().lower()
        allowed = {"shortest", "fastest", "safest"}
        if v not in allowed:
            raise ValueError(f"strategy must be one of: {', '.join(allowed)}")
        return v

class AIRouteAnalysisRequest(BaseModel):
    source_hospital_id: str
    target_hospital_id: str
    include_alternatives: Optional[bool] = True

    @field_validator("source_hospital_id", "target_hospital_id")
    @classmethod
    def hospital_id_must_not_be_empty(cls, v):
        if not v or not str(v).strip():
            raise ValueError("hospital ID must not be empty")
        return str(v).strip()


@app.get("/api/hospitals")
def list_hospitals(
    district: Optional[str] = None,
    min_beds: Optional[int] = None,
    trauma_level: Optional[str] = None,
    has_oxygen: Optional[bool] = None
):
    """List all hospitals in Karnataka with optional filters"""
    hospitals = hospital_network_service.get_hospitals(district=district, min_beds=min_beds)

    # Additional filters
    if trauma_level:
        hospitals = [h for h in hospitals if h.get("trauma_level") == trauma_level]
    if has_oxygen is not None:
        hospitals = [h for h in hospitals if h.get("oxygen_available") == has_oxygen]

    return {
        "hospitals": hospitals,
        "count": len(hospitals),
        "filters": {"district": district, "min_beds": min_beds, "trauma_level": trauma_level, "has_oxygen": has_oxygen}
    }


@app.get("/api/hospitals/{hospital_id}")
def get_hospital(hospital_id: str):
    """Get details of a specific hospital"""
    hospital = hospital_network_service.get_hospital_by_id(hospital_id)
    if not hospital:
        raise HTTPException(status_code=404, detail=f"Hospital {hospital_id} not found")

    # Get nearby hospitals
    nearby = hospital_network_service.get_nearby_hospitals(hospital_id, max_distance_km=80)

    return {
        "hospital": hospital,
        "nearby_hospitals": nearby[:5],
        "nearby_count": len(nearby)
    }


@app.get("/api/routes")
def list_routes(hospital_id: Optional[str] = None, blocked_only: bool = False):
    """List hospital network routes/edges"""
    routes = hospital_network_service.get_routes(hospital_id=hospital_id)

    if blocked_only:
        routes = [r for r in routes if r.get("blocked", False)]

    return {
        "routes": routes,
        "count": len(routes),
        "filters": {"hospital_id": hospital_id, "blocked_only": blocked_only}
    }


@app.post("/api/recalculate-routes")
def recalculate_routes():
    """Recalculate hospital route danger/blocked status from active disaster alerts."""
    summary = hospital_network_service.refresh()
    return {
        "success": True,
        **summary,
    }


@app.get("/api/alerts")
def list_alerts(active_only: bool = True, disaster_type: Optional[str] = None, district: Optional[str] = None):
    """List disaster alerts"""
    alerts = hospital_network_service.get_alerts(active_only=active_only)

    if disaster_type:
        alerts = [a for a in alerts if a.get("disaster_type") == disaster_type]
    if district:
        alerts = [a for a in alerts if a.get("district") == district]

    return {
        "alerts": alerts,
        "count": len(alerts),
        "filters": {"active_only": active_only, "disaster_type": disaster_type, "district": district}
    }


@app.post("/api/optimize-route")
def optimize_route(req: RouteOptimizationRequest):
    """Optimize route between two hospitals using shortest path algorithms"""
    result = hospital_network_service.optimize_route(
        source=req.source_hospital_id,
        target=req.target_hospital_id,
        strategy=req.strategy
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result.get("error"))

    return result


@app.post("/api/ai-route-analysis")
def ai_route_analysis(req: AIRouteAnalysisRequest):
    """AI-powered route analysis using Ollama"""
    source_hosp = hospital_network_service.get_hospital_by_id(req.source_hospital_id)
    target_hosp = hospital_network_service.get_hospital_by_id(req.target_hospital_id)

    if not source_hosp:
        raise HTTPException(status_code=404, detail=f"Source hospital {req.source_hospital_id} not found")
    if not target_hosp:
        raise HTTPException(status_code=404, detail=f"Target hospital {req.target_hospital_id} not found")

    hospital_network_service.refresh()

    # Get current routes and active alerts
    alerts = hospital_network_service.get_alerts(active_only=True)
    routes = hospital_network_service.get_routes(recalculate=False)

    # Get the optimal route
    optimal_route = hospital_network_service.optimize_route(
        source=req.source_hospital_id,
        target=req.target_hospital_id,
        strategy="safest"
    )

    if "error" in optimal_route:
        raise HTTPException(status_code=404, detail=optimal_route.get("error"))

    # Get alternative routes if requested
    alternatives = hospital_network_service.get_alternative_routes(
        req.source_hospital_id,
        req.target_hospital_id,
        limit=3,
    ) if req.include_alternatives else []

    # Prepare context for AI
    context = {
        "source": {
            "name": source_hosp["hospital_name"],
            "district": source_hosp["district"],
            "beds": source_hosp["available_beds"],
            "oxygen": source_hosp["oxygen_available"]
        },
        "target": {
            "name": target_hosp["hospital_name"],
            "district": target_hosp["district"],
            "beds": target_hosp["available_beds"],
            "oxygen": target_hosp["oxygen_available"]
        },
        "optimal_route": optimal_route,
        "alternatives": alternatives,
        "active_alerts": alerts,
        "blocked_routes": len([r for r in routes if r.get("blocked", False)])
    }

    # Try to get AI recommendation
    try:
        from src.ai.ollama_client import AIAdvisor
        advisor = AIAdvisor()
        ai_analysis = advisor.generate_route_analysis(
            source_hospital=source_hosp,
            target_hospital=target_hosp,
            recommended_route=optimal_route,
            alternatives=alternatives,
            active_alerts=alerts,
            blocked_routes=context["blocked_routes"],
        )
    except Exception as e:
        logger.warning(f"AI analysis failed: {e}")
        ai_analysis = "AI analysis unavailable"

    return {
        "analysis": ai_analysis,
        "context": context,
        "recommendation": optimal_route,
        "alternatives": alternatives,
    }


@app.get("/api/network-summary")
def get_network_summary():
    """Get summary statistics of the hospital network"""
    hospitals = hospital_network_service.hospitals
    routes = hospital_network_service.get_routes() if hospital_network_service.graph else []
    alerts = hospital_network_service.get_alerts(active_only=True)

    # Calculate stats
    total_beds = sum(h.get("available_beds", 0) for h in hospitals)
    total_capacity = sum(h.get("capacity", 0) for h in hospitals)
    hospitals_with_oxygen = sum(1 for h in hospitals if h.get("oxygen_available", False))

    blocked_routes = len([r for r in routes if r.get("blocked", False)])

    # District breakdown
    by_district = {}
    for h in hospitals:
        d = h["district"]
        if d not in by_district:
            by_district[d] = {"count": 0, "beds": 0}
        by_district[d]["count"] += 1
        by_district[d]["beds"] += h.get("available_beds", 0)

    return {
        "total_hospitals": len(hospitals),
        "total_routes": len(routes),
        "blocked_routes": blocked_routes,
        "total_available_beds": total_beds,
        "total_capacity": total_capacity,
        "beds_occupancy_pct": round((total_beds / total_capacity * 100), 1) if total_capacity > 0 else 0,
        "hospitals_with_oxygen": hospitals_with_oxygen,
        "active_alerts": len(alerts),
        "district_breakdown": by_district
    }


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
