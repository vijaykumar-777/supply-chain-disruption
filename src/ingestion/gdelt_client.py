import os
import io
import zipfile
import requests

try:
    from src.config import RAW_DATA_DIR
except ImportError:
    RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "raw")

class GDELTClient:
    """Client for fetching data from the GDELT Project."""
    
    def __init__(self):
        self.lastupdate_url = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"

    def fetch_latest_events(self, output_dir=RAW_DATA_DIR):
        """Fetches the latest events from GDELT 2.0 API, downloads the zip, and extracts the CSV."""
        try:
            # 1. Fetch lastupdate.txt to get the URL of the most recent export
            print(f"Fetching GDELT lastupdate.txt from {self.lastupdate_url}...")
            res = requests.get(self.lastupdate_url, timeout=10)
            res.raise_for_status()

            lines = res.text.strip().split("\n")
            if not lines:
                raise ValueError("GDELT lastupdate.txt is empty.")

            # The first line is typically the 'export' file (events)
            export_line = lines[0]
            parts = export_line.split(" ")
            
            if len(parts) < 3:
                raise ValueError(f"Unexpected format in lastupdate.txt: {export_line}")
                
            export_url = parts[2]
            
            # 2. Download the zip file
            print(f"Downloading latest GDELT export from: {export_url}")
            zip_res = requests.get(export_url, timeout=30)
            zip_res.raise_for_status()

            # 3. Extract the contents
            os.makedirs(output_dir, exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(zip_res.content)) as zip_ref:
                zip_ref.extractall(output_dir)
                extracted_files = zip_ref.namelist()
                print(f"Successfully extracted {len(extracted_files)} files to {output_dir}")
                
            return [os.path.join(output_dir, f) for f in extracted_files]
            
        except requests.RequestException as e:
            print(f"Error communicating with GDELT API: {e}")
            raise
        except Exception as e:
            print(f"Error processing GDELT data: {e}")
            raise

if __name__ == "__main__":
    client = GDELTClient()
    client.fetch_latest_events()
