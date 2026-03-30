#!/usr/bin/env python3
import subprocess
import sys

def download_spacy_models():
    """Downloads the necessary spaCy models."""
    print("Downloading spaCy en_core_web_sm model...")
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        print("Successfully downloaded en_core_web_sm model.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to download the spaCy model. Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_spacy_models()
