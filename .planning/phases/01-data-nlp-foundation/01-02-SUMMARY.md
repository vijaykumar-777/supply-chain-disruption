# Plan 01-02: Implement NLP preprocessing layer with spaCy/NLTK

Completed At: 2026-03-30
Outcome: SUCCESS

## What Was Done
Added `spacy` to `requirements.txt`. Created a helper script `scripts/download_models.py` for downloading the `en_core_web_sm` model easily. Created `src/nlp/preprocessor.py` containing `TextPreprocessor`. This component loads the local spaCy model to perform offline text cleaning: lower-casing, tokenization, stop-word and punctuation removal.

## Key Decisions
- Adopted `spaCy` exclusively over NLTK for better performance and simpler model packaging (`en_core_web_sm`).
- Preprocessor fails gracefully (logs a warning) instead of hard crashing on import if the pipeline model is not downloaded, but will raise a runtime error during execution ensuring clean testability.

## Artifacts Generated
- `requirements.txt` (updated)
- `scripts/download_models.py`
- `src/nlp/preprocessor.py`
