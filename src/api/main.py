"""
ATLAS AI — FastAPI Backend
Bridges the Python prediction/AI engine with the React frontend.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import List, Optional
import uuid
import datetime
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.monitoring.supply_chain_monitor import SupplyChainMonitor
from src.ingestion.company_intelligence import CompanyIntelligenceService

app = FastAPI(title="ATLAS AI API", version="1.1", description="Supply Chain Intelligence Backend")
monitor_service = SupplyChainMonitor()
company_intelligence_service = CompanyIntelligenceService()

# ─── Demo Data (Fallback for Initial UX) ────────────────────────────────────

DEMO_EVENTS = [
    {
        "id": "gdelt-001",
        "title": "Port Congestion in Hamburg",
        "category": "Logistics",
        "severity": 0.8,
        "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat(),
        "locations": ["Hamburg, Germany"],
        "description": "Significant vessel backlog at Hamburg terminal affecting European logistics routes.",
        "type": "critical"
    },
    {
        "id": "gdelt-002",
        "title": "Semiconductor Supply Warning",
        "category": "Trade",
        "severity": 0.6,
        "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=5)).isoformat(),
        "locations": ["Taiwan", "South Korea"],
        "description": "Production slowdown reported in major fab facilities due to power grid maintenance.",
        "type": "warning"
    },
    {
        "id": "weather-003",
        "title": "Severe Storm Risk: East Coast",
        "category": "Weather",
        "severity": 0.75,
        "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat(),
        "locations": ["Savannah, GA", "Charleston, SC"],
        "description": "Flash flooding risk for major coastal logistics hubs.",
        "type": "critical"
    }
]

DEMO_NODES = 142  # Static count for fallback

OPERATIONAL_NODE_WHERE = "NOT n:Event AND NOT n:Filing AND NOT n:Ticker AND NOT n:Regulator AND NOT n:Country"

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
        "service": "ATLAS AI API",
        "neo4j": neo4j_status,
        "timestamp": datetime.datetime.now().isoformat(),
    }


@app.get("/api/events")
def get_events(category: Optional[str] = None, severity_min: Optional[float] = None, location: Optional[str] = None):
    """Return all disruption events from live data sources only."""
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
            
            # Implementation Fix #11: Fallback to demo events if DB is empty
            if not events:
                logger.info("Neo4j is empty of events. Using Fallback Demo Data.")
                events = list(DEMO_EVENTS)
                source = "fallback (no live records)"
        finally:
            client.close()
    else:
        source = "unavailable"
        logger.info("No live event data available: %s. Using Fallback Demo Data.", err)
        events = list(DEMO_EVENTS)

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
    """Return all supply chain nodes and links from live data sources only."""
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

            # Fix #11: Fallback if DB connects but has no events
            if event_count == 0:
                logger.info("Metrics: Empty DB. Using fallback counts.")
                return {
                    "total_active_events": len(DEMO_EVENTS),
                    "high_risk_nodes": len([e for e in DEMO_EVENTS if e["type"] == "critical"]),
                    "monitored_nodes": node_count if node_count > 0 else DEMO_NODES,
                    "weather_alerts": 1,
                    "source": "fallback (empty db)",
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
        return {
            "total_active_events": len(DEMO_EVENTS),
            "high_risk_nodes": len([e for e in DEMO_EVENTS if e["type"] == "critical"]),
            "monitored_nodes": DEMO_NODES,
            "weather_alerts": 1,
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
                raise HTTPException(status_code=400, detail=f"Source node '{req.source}' not found in the supply chain network")
            if req.target not in sc_network.graph:
                raise HTTPException(status_code=400, detail=f"Target node '{req.target}' not found in the supply chain network")

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
    else:
        raise HTTPException(status_code=503, detail="Live supply chain graph is unavailable. Load real graph data into Neo4j before running simulations.")


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
            raise HTTPException(status_code=400, detail="No supply chain data available for alert context. Please upload network data first.")
            
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
def get_supply_chain_template():
    return monitor_service.template()


@app.get("/api/supply-chain/snapshots")
def list_supply_chain_snapshots():
    return {"snapshots": monitor_service.list_snapshots()}


@app.post("/api/supply-chain/upload")
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
        logger.error(f"Supply-chain upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process uploaded supply-chain file")


@app.get("/api/supply-chain/snapshots/{snapshot_id}")
def get_supply_chain_snapshot(snapshot_id: str, refresh: bool = True):
    try:
        snapshot = monitor_service.load_snapshot(snapshot_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Supply-chain snapshot not found")

    if not refresh and snapshot.get("latest_report"):
        return snapshot["latest_report"]

    try:
        return monitor_service.build_report(snapshot)
    except Exception as e:
        logger.error(f"Supply-chain refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh supply-chain monitoring report")


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
