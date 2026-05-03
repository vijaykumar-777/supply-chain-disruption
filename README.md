# ReliefRoute Karnataka

ReliefRoute Karnataka is a disaster-relief logistics prototype for floods and landslides in Karnataka, focused on Western Ghats and coastal road access.

The system models relief hubs, towns, villages, and road corridors as a graph. Weather and disruption signals are matched to road segments so responders can see blocked routes, cascading village isolation, and alternate truck paths.

## What It Does

- Tracks flood, landslide, heavy-rain, and road-access hazards.
- Models roads as graph edges between relief hubs and settlements.
- Scores road segments as healthy, at risk, or blocked.
- Shows cascading impact when one road cuts off downstream villages.
- Suggests alternate routes when the uploaded graph contains backups.
- Keeps demo data separate from live data with `ATLAS_MODE=demo`.

## Modes

The backend has an explicit data mode:

- `ATLAS_MODE=live`: default. No fake data is silently returned. If Neo4j is unavailable, API responses say `source: "unavailable"`.
- `ATLAS_MODE=demo`: returns a small Karnataka relief scenario for UI demos and route simulation.

The frontend top bar has a Live/Demo toggle that calls `/api/mode`. Switching modes remounts the active view so demo and live data are not displayed together.

This prevents demo data from looking like operational truth.

## Tech Stack

- Backend: FastAPI, Pydantic, NetworkX, Neo4j
- Frontend: React, TypeScript, Vite, Leaflet, Recharts
- Data sources: OpenWeatherMap, GDELT, uploaded CSV/JSON road networks
- Optional local AI: Ollama

## Setup

```bash
cp .env.example .env
pip install -r requirements.txt

cd frontend
npm install
```

Start the backend:

```bash
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Start the frontend:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

## Docker Compose

```bash
docker compose up --build
```

The compose file starts Neo4j, the FastAPI backend, and the Vite frontend.

## Road Network Upload

Upload `.csv` or `.json` with columns such as:

- `source_company`: relief hub, town, or upstream settlement
- `target_company`: destination town or village
- `relationship_type`: road type, access type, or corridor type
- `material`: relief payload or aid type
- `origin`: road origin point
- `destination`: road destination point
- `transport_mode`: usually truck
- `criticality`: high, medium, or low
- `route_name`: road segment or corridor name

Common aliases are accepted, including `relief_hub`, `village`, `road_segment`, `corridor`, `from_settlement`, `to_settlement`, and `medical_priority`.

## Verification

Backend tests:

```bash
python3 -m pytest tests -q
```

Frontend typecheck:

```bash
cd frontend
npm run lint
```

Frontend production build:

```bash
cd frontend
npm run build
```

## Project Structure

```text
src/
  api/          FastAPI routes
  graph/        Neo4j graph client
  ingestion/    Weather, GDELT, and public-source clients
  monitoring/   Relief network upload, hazard matching, impact scoring
  prediction/   NetworkX route and resilience modeling
frontend/       React dashboard
tests/          Backend tests
```

## Current Scope

This is an MVP/prototype, not an emergency-certified operational system. The next serious improvements should be calibrated rainfall thresholds, better landslide susceptibility data, road inventory imports, manual validation queues, and response-report exports.
