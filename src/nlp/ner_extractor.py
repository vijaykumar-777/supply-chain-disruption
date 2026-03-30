import spacy

class EntityExtractor:
    """Extracts Named Entities (NER) using spaCy for downstream Graph Node linking."""
    
    def __init__(self, model_name="en_core_web_sm"):
        """Initialize the spaCy NLP pipeline."""
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            print(f"Warning: spaCy model '{model_name}' not found. NER extraction will default to empty.")
            self.nlp = None

    def extract_entities(self, text: str) -> dict:
        """
        Parses the text and returns arrays of Geographical (GPE, LOC) and Organizational (ORG) entities.
        """
        if not text:
            return {"locations": [], "organizations": []}
            
        if not self.nlp:
            raise RuntimeError("spaCy model is not loaded. Cannot extract entities.")

        doc = self.nlp(text)
        
        locations = set()
        organizations = set()
        
        for ent in doc.ents:
            # GPE (Countries, cities, states) and LOC (Non-GPE locations, mountain ranges, bodies of water)
            if ent.label_ in ["GPE", "LOC"]:
                locations.add(ent.text)
            # ORG (Companies, agencies, institutions)
            elif ent.label_ == "ORG":
                organizations.add(ent.text)
                
        return {
            "locations": list(locations),
            "organizations": list(organizations)
        }

    def link_entities_to_nodes(self, extracted: dict) -> list:
        """
        Stub function for Phase 2: Formats extracted raw entities into standardized
        Graph Node IDs. (e.g., 'New York' -> 'NODE_NEW_YORK')
        Returns a flat list of node identifiers.
        """
        nodes = []
        
        # Format Locations
        for loc in extracted.get("locations", []):
            formatted_loc = str(loc).upper().replace(" ", "_")
            nodes.append(f"NODE_LOC_{formatted_loc}")
            
        # Format Organizations
        for org in extracted.get("organizations", []):
            formatted_org = str(org).upper().replace(" ", "_")
            nodes.append(f"NODE_ORG_{formatted_org}")
            
        return nodes

if __name__ == "__main__":
    extractor = EntityExtractor()
    if extractor.nlp:
        sample_text = "The supply ship Ever Given belonging to Evergreen Marine was blocked in the Suez Canal near Egypt."
        
        print("--- Extraction Test ---")
        entities = extractor.extract_entities(sample_text)
        print(f"Extracted Entities: {entities}")
        
        print("\n--- Linking Test ---")
        nodes = extractor.link_entities_to_nodes(entities)
        print(f"Generated Nodes: {nodes}")
