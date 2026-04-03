from typing import Dict, Any, List

class CorrelationEngine:
    """Engine for assigning severity scores and correlating events geographically."""

    def __init__(self):
        # Base severity for different disruption categories
        self.category_severity = {
            "STRIKE": 0.6,
            "NATURAL_DISASTER": 0.8,
            "PORT_CLOSURE": 0.9,
            "WEATHER_DELAY": 0.4,
            "GEOPOLITICAL": 0.7,
            "UNKNOWN": 0.3
        }

    def calculate_severity(self, event: Dict[str, Any]) -> float:
        """
        Calculate severity score for an event based on category, keywords, and context.
        Returns a score between 0.0 and 1.0.
        """
        category = event.get('category', 'UNKNOWN')
        base_score = self.category_severity.get(category, 0.3)
        
        # Adjust based on keywords in title
        title = event.get('title', '').upper()
        multiplier = 1.0
        
        if "SEVERE" in title or "CRITICAL" in title or "MAJOR" in title:
            multiplier = 1.2
        elif "MINOR" in title or "RESOLVED" in title:
            multiplier = 0.5
            
        final_score = min(base_score * multiplier, 1.0)
        return final_score

    def find_geographic_correlations(self, neo4j_client, location_name: str, max_hops: int = 2) -> List[Dict[str, Any]]:
        """
        Find supply chain routes and nodes correlated geographically to a location.
        """
        query = """
        MATCH (l:Location {name: $location_name})
        MATCH path = (n)-[*1..$max_hops]-(l)
        RETURN n, [r in relationships(path) | type(r)] as path_rels
        """
        
        results = []
        try:
            with neo4j_client.driver.session() as session:
                records = session.run(query, location_name=location_name, max_hops=max_hops)
                for record in records:
                    node = record["n"]
                    results.append({
                        "id": dict(node).get("id", "Unknown"),
                        "labels": list(node.labels),
                        "path_relationships": record["path_rels"]
                    })
        except Exception as e:
            print(f"Error finding geographic correlations: {e}")
            
        return results
