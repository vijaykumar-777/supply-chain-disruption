import requests
import sys
import os

# Add project root to path for config import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import OPENWEATHERMAP_API_KEY

def test_weather_key():
    """Test OpenWeatherMap API key validity.
    Fix #13: null-check key before slicing, use HTTPS, add timeout/error handling."""
    
    # Fix #13: Null-check before slicing
    if not OPENWEATHERMAP_API_KEY:
        print("Error: No API key found in .env file or environment.")
        print("Set OPENWEATHERMAP_API_KEY in your .env file.")
        return
    
    print(f"Testing key: {OPENWEATHERMAP_API_KEY[:5]}...")
    
    # Singapore coordinates
    lat, lon = 1.3521, 103.8198
    # Fix #13: Use HTTPS instead of HTTP
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHERMAP_API_KEY}"
    
    try:
        # Fix #13: Add timeout
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("✅ Success! The OpenWeatherMap API key is valid.")
            data = response.json()
            weather = data.get("weather", [{}])
            if weather:
                print(f"Current weather in Singapore: {weather[0].get('description', 'N/A')}")
        elif response.status_code == 401:
            print("❌ Invalid API key. Please check your OpenWeatherMap dashboard.")
        else:
            print(f"❌ Error: Received status code {response.status_code}")
            print(response.text)
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Check your network connection.")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Check your network connection.")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_weather_key()
