import logging
from typing import List, Dict, Any

from neo4j import GraphDatabase

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
            "CREATE CONSTRAINT company_id IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT supplier_id IF NOT EXISTS FOR (s:Supplier) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT factory_id IF NOT EXISTS FOR (f:Factory) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT route_id IF NOT EXISTS FOR (r:Route) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT location_name IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",
            "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT filing_id IF NOT EXISTS FOR (f:Filing) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT ticker_symbol IF NOT EXISTS FOR (t:Ticker) REQUIRE t.symbol IS UNIQUE",
            "CREATE CONSTRAINT country_code IF NOT EXISTS FOR (c:Country) REQUIRE c.code IS UNIQUE",
            "CREATE CONSTRAINT regulator_id IF NOT EXISTS FOR (r:Regulator) REQUIRE r.id IS UNIQUE",
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
        clean_properties = {key: value for key, value in properties.items() if value is not None}

        if node_type == "Location" and clean_properties.get("name"):
            query = f"MERGE (n:{node_type} {{name: $merge_name}}) SET n += $props"
            params = {"merge_name": clean_properties["name"], "props": clean_properties}
        elif clean_properties.get("id"):
            query = f"MERGE (n:{node_type} {{id: $merge_id}}) SET n += $props"
            params = {"merge_id": clean_properties["id"], "props": clean_properties}
        elif clean_properties.get("name"):
            query = f"MERGE (n:{node_type} {{name: $merge_name}}) SET n += $props"
            params = {"merge_name": clean_properties["name"], "props": clean_properties}
        else:
            props_str = '{' + ', '.join([f"{k}: ${k}" for k in clean_properties.keys()]) + '}'
            query = f"MERGE (n:{node_type} {props_str})"
            params = clean_properties

        with self.driver.session() as session:
            session.run(query, **params)

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

    def upsert_company_intelligence(self, company: Dict[str, Any]):
        """Insert or update a live company profile plus its filing metadata."""
        company_properties = {
            "id": company["company_id"],
            "name": company.get("name"),
            "legal_name": company.get("legal_name"),
            "lei": company.get("lei"),
            "cik": company.get("cik"),
            "ticker": company.get("ticker"),
            "country": company.get("country"),
            "sector": company.get("sector"),
            "industry": company.get("industry"),
            "jurisdiction": company.get("jurisdiction"),
            "entity_status": company.get("entity_status"),
            "legal_form": company.get("legal_form"),
            "registered_as": company.get("registered_as"),
            "legal_address": company.get("legal_address"),
            "headquarters_address": company.get("headquarters_address"),
            "source_labels": company.get("source_labels", []),
            "description": company.get("description"),
        }

        company_query = """
        WITH $company AS company
        OPTIONAL MATCH (by_id:Company {id: company.id})
        WITH company, by_id
        OPTIONAL MATCH (by_identifier:Company)
        WHERE by_id IS NULL
          AND (
            (company.lei IS NOT NULL AND by_identifier.lei = company.lei)
            OR (company.cik IS NOT NULL AND by_identifier.cik = company.cik)
          )
        WITH company, by_id, collect(by_identifier)[0] AS by_identifier
        OPTIONAL MATCH (by_name:Company)
        WHERE by_id IS NULL
          AND by_identifier IS NULL
          AND company.name IS NOT NULL
          AND toLower(by_name.name) = toLower(company.name)
        WITH company, by_id, by_identifier, collect(by_name)[0] AS by_name
        WITH company, coalesce(by_id, by_identifier, by_name) AS existing
        CALL (existing, company) {
            WITH existing, company
            WITH existing, company WHERE existing IS NULL
            CREATE (created:Company {id: company.id})
            SET created += company
            RETURN created AS company_node
            UNION
            WITH existing, company
            WITH existing, company WHERE existing IS NOT NULL
            SET existing += company
            RETURN existing AS company_node
        }
        RETURN company_node
        """

        country_query = """
        MATCH (c:Company {id: $company_id})
        MERGE (country:Country {code: $country_code})
        SET country.name = $country_name
        MERGE (c)-[:REGISTERED_IN]->(country)
        """

        regulator_query = """
        MATCH (c:Company {id: $company_id})
        MERGE (r:Regulator {id: "regulator-sec"})
        SET r.name = "U.S. Securities and Exchange Commission",
            r.code = "SEC"
        MERGE (c)-[:FILES_WITH]->(r)
        """

        filings_query = """
        MATCH (c:Company {id: $company_id})
        UNWIND $filings AS filing
        MERGE (f:Filing {id: filing.id})
        SET f += filing
        MERGE (c)-[:FILED]->(f)
        """

        ticker_query = """
        MATCH (c:Company {id: $company_id})
        UNWIND $tickers AS ticker_symbol
        MERGE (t:Ticker {symbol: ticker_symbol})
        MERGE (c)-[:LISTED_AS]->(t)
        """

        with self.driver.session() as session:
            session.run(company_query, company=company_properties)

            if company.get("country"):
                country_code = str(company.get("country")).strip().upper().replace(" ", "_")
                session.run(
                    country_query,
                    company_id=company["company_id"],
                    country_code=country_code,
                    country_name=company.get("country"),
                )

            if company.get("cik"):
                session.run(regulator_query, company_id=company["company_id"])

            if company.get("filings"):
                session.run(filings_query, company_id=company["company_id"], filings=company["filings"])

            if company.get("tickers"):
                session.run(ticker_query, company_id=company["company_id"], tickers=company["tickers"])

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
