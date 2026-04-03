import requests
from src.config import OPENWEATHERMAP_API_KEY
import sys

def test_weather_key():
    print(f"Testing key: {OPENWEATHERMAP_API_KEY[:5]}...")
    if not OPENWEATHERMAP_API_KEY:
        print("Error: No API key found in .env file or environment.")
        return
    
    # Singapore coordinates
    lat, lon = 1.3521, 103.8198
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHERMAP_API_KEY}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("✅ Success! The OpenWeatherMap API key is valid.")
            print(f"Current weather in Singapore: {response.json()['weather'][0]['description']}")
        elif response.status_code == 401:
            print("❌ Invalid API key. Please check your OpenWeatherMap dashboard.")
        else:
            print(f"❌ Error: Received status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")

if __name__ == "__main__":
    test_weather_key()
