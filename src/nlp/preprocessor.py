import spacy

class TextPreprocessor:
    """Preprocesses text for NLP and classification tasks."""

    def __init__(self, model_name="en_core_web_sm"):
        """Initialize the spaCy NLP pipeline."""
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            print(f"Warning: spaCy model '{model_name}' not found. "
                  f"Please run 'python scripts/download_models.py' first.")
            # Set to None so tests and initialization doesn't completely crash if no model
            self.nlp = None

    def clean_text(self, text: str) -> str:
        """
        Cleans the input string by:
        - Lowercasing
        - Removing punctuation
        - Removing stopwords
        - Tokenizing the text correctly
        """
        if not text:
            return ""

        if not self.nlp:
            raise RuntimeError("spaCy model is not loaded. Cannot process text.")

        # Process the text
        doc = self.nlp(text.lower())
        
        # Filter tokens that are not stop words, not punctuation, and not whitespace
        clean_tokens = [
            token.text for token in doc 
            if not token.is_stop and not token.is_punct and not token.is_space
        ]
        
        return " ".join(clean_tokens)

if __name__ == "__main__":
    # Quick test
    preprocessor = TextPreprocessor()
    if preprocessor.nlp:
        sample_text = "The quick, brown fox jumps over the lazy dog! It was a very bad day for port operations."
        cleaned = preprocessor.clean_text(sample_text)
        print(f"Original: {sample_text}")
        print(f"Cleaned: {cleaned}")
