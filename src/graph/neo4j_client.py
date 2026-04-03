from neo4j import GraphDatabase
import logging
from typing import List, Dict, Any
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

logger = logging.getLogger(__name__)

class Neo4jClient:
    """Client for interacting with Neo4j graph database."""
    
    def __init__(self, uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"Initialized Neo4j client at {uri}")

    def close(self):
        """Close the database driver."""
        self.driver.close()

    def load_schema(self):
        """Initialize indexes and constraints for supply chain nodes."""
        queries = [
            "CREATE CONSTRAINT supplier_id IF NOT EXISTS FOR (s:Supplier) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT factory_id IF NOT EXISTS FOR (f:Factory) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT route_id IF NOT EXISTS FOR (r:Route) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT location_name IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",
            "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
        ]
        
        with self.driver.session() as session:
            for query in queries:
                session.run(query)
            logger.info("Initialized graph constraints and indices")

    def insert_event(self, event_data: Dict[str, Any]):
        """Insert a disruption event into the graph, linking it to locations."""
        query = """
        MERGE (e:Event {id: $id})
        SET e.title = $title,
            e.category = $category,
            e.severity = $severity,
            e.timestamp = $timestamp
        
        WITH e
        UNWIND $locations as loc_name
        MERGE (l:Location {name: loc_name})
        MERGE (e)-[:AFFECTS]->(l)
        """
        
        with self.driver.session() as session:
            session.run(query, 
                        id=event_data.get('id'),
                        title=event_data.get('title'),
                        category=event_data.get('category'),
                        severity=event_data.get('severity', 0.5), # Default severity
                        timestamp=event_data.get('timestamp'),
                        locations=event_data.get('locations', []))

    def insert_node(self, node_type: str, properties: Dict[str, Any]):
        """Insert a generic supply chain node."""
        props_str = '{' + ', '.join([f"{k}: ${k}" for k in properties.keys()]) + '}'
        query = f"MERGE (n:{node_type} {props_str})"
        
        with self.driver.session() as session:
            session.run(query, **properties)

    def insert_route(self, from_node_id: str, to_node_id: str, properties: Dict[str, Any]):
        """Create a network route between two supply chain nodes."""
        query = """
        MATCH (a) WHERE a.id = $from_id OR a.name = $from_id
        MATCH (b) WHERE b.id = $to_id OR b.name = $to_id
        MERGE (a)-[r:ROUTES_TO]->(b)
        SET r += $properties
        """
        
        with self.driver.session() as session:
            session.run(query, from_id=from_node_id, to_id=to_node_id, properties=properties)

    def get_full_graph(self) -> Dict[str, Any]:
        """Retrieve all supply chain nodes and routing relationships for NetworkX conversion."""
        query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, r, m
        """
        
        nodes = {}
        edges = []
        
        with self.driver.session() as session:
            records = session.run(query)
            for record in records:
                n = record["n"]
                if n and n.id not in nodes:
                    # Provide fallback key for nodes without explicit ID
                    node_id = dict(n).get("id") or dict(n).get("name") or str(n.element_id)
                    nodes[node_id] = {"labels": list(n.labels), "properties": dict(n)}
                
                r = record["r"]
                m = record["m"]
                if r and m:
                    u_id = dict(n).get("id") or dict(n).get("name") or str(n.element_id)
                    v_id = dict(m).get("id") or dict(m).get("name") or str(m.element_id)
                    edges.append({
                        "source": u_id,
                        "target": v_id,
                        "type": r.type,
                        "properties": dict(r)
                    })
                    
        return {"nodes": nodes, "edges": edges}
