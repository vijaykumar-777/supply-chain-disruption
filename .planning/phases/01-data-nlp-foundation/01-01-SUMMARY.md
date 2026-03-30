# Plan 01-01: Setup repository structure and data ingestion pipeline (GDELT/Weather)

Completed At: 2026-03-30
Outcome: SUCCESS

## What Was Done
Created the Python repository structure and dependency files (`requirements.txt`). Implemented modular data ingestion clients inside `src/ingestion`:
1. `GDELTClient` (`gdelt_client.py`): Fetches the latest GDELT updates, parses the URL, downloads, unzips, and stores unstructured CSV event data inside `data/raw/`.
2. `WeatherClient` (`weather_client.py`): Reaches out to OpenWeatherMap API for targeted geographic lookup of severe weather risks. Built for ease of use via coordinates and returning JSON payload inside `data/raw/`.

## Key Decisions
- Placed ingestion scripts into a separated `src/ingestion/` module instead of root package.
- Chose `python-dotenv` for scalable API key management (`OPENWEATHERMAP_API_KEY`).
- Used naive CSV storage on disk instead of SQLite per Phase 1 simplicity constraints.

## Artifacts Generated
- `src/config.py`
- `src/ingestion/gdelt_client.py`
- `src/ingestion/weather_client.py`
- `.gitignore`, `requirements.txt`
