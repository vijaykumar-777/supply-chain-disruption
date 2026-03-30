import os
import json
import requests
import datetime

try:
    from src.config import RAW_DATA_DIR, OPENWEATHERMAP_API_KEY
except ImportError:
    RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "raw")
    OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

class WeatherClient:
    """Client for fetching data from OpenWeatherMap."""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or OPENWEATHERMAP_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def fetch_weather(self, lat: float, lon: float, output_dir=RAW_DATA_DIR) -> str:
        """Fetches the weather for a specific lat/lon coordinate."""
        try:
            if not self.api_key:
                raise ValueError("OPENWEATHERMAP_API_KEY is not set.")
                
            print(f"Fetching weather for lat: {lat}, lon: {lon}...")
            
            res = requests.get(
                self.base_url, 
                params={
                    "lat": lat, 
                    "lon": lon, 
                    "appid": self.api_key,
                    "units": "metric"  # Optional: metric or imperial
                },
                timeout=10
            )
            res.raise_for_status()

            # The response is JSON
            weather_data = res.json()
            
            # Create the output filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"weather_{lat}_{lon}_{timestamp}.json"
            file_path = os.path.join(output_dir, filename)

            os.makedirs(output_dir, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(weather_data, f, indent=4)
                
            print(f"Successfully saved weather data to {file_path}")
            return file_path
            
        except requests.RequestException as e:
            print(f"Error communicating with OpenWeatherMap API: {e}")
            raise
        except Exception as e:
            print(f"Error processing weather data: {e}")
            raise

if __name__ == "__main__":
    # Example usage
    client = WeatherClient()
    # Test for London, UK if API key is present
    if client.api_key:
        client.fetch_weather(51.5074, -0.1278)
    else:
        print("API key not set, skipping test.")
