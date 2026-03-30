try:
    from transformers import pipeline
except ImportError:
    pipeline = None

class EventClassifier:
    """Classifies unstructured text into supply chain event categories using zero-shot classification."""

    def __init__(self, model_name="cross-encoder/nli-distilroberta-base"):
        """Initialize the HuggingFace zero-shot classification pipeline."""
        if not pipeline:
            print("Warning: transformers package is not installed. EventClassifier cannot be initialized.")
            self.classifier_pipeline = None
            return
            
        try:
            # We use a smaller, faster model specifically good for NLI and zero-shot out of the box
            self.classifier_pipeline = pipeline("zero-shot-classification", model=model_name)
        except Exception as e:
            print(f"Error initializing HuggingFace pipeline with model {model_name}: {e}")
            self.classifier_pipeline = None

        # Default standard supply chain disruptions
        self.default_candidate_labels = [
            "port strike", 
            "natural disaster", 
            "bankruptcy", 
            "production halt", 
            "extreme weather", 
            "supply chain disruption"
        ]

    def classify_event(self, text: str, candidate_labels: list = None) -> dict:
        """
        Classifies the text against the candidate labels.
        Returns the top label and its confidence score.
        """
        if not self.classifier_pipeline:
            raise RuntimeError("Classifier pipeline is not available.")

        if not text:
            return {"label": "unknown", "score": 0.0}

        if candidate_labels is None:
            candidate_labels = self.default_candidate_labels

        try:
            # Run the zero-shot inference
            result = self.classifier_pipeline(text, candidate_labels)
            
            # Extract top predicted label and its score
            top_label = result['labels'][0]
            top_score = result['scores'][0]
            
            return {
                "label": top_label,
                "score": round(top_score, 4),
                "all_scores": dict(zip(result['labels'], result['scores']))
            }
        except Exception as e:
            print(f"Error during classification inference: {e}")
            return {"label": "error", "score": 0.0}

if __name__ == "__main__":
    # Test execution
    classifier = EventClassifier()
    if classifier.classifier_pipeline:
        sample_event = "Dockworkers in Los Angeles have initiated a massive walkout shutting down all operations indefinitely."
        prediction = classifier.classify_event(sample_event)
        print(f"Event: {sample_event}")
        print(f"Classification: {prediction['label']} (confidence: {prediction['score']})")
