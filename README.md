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

## Data Provenance

The project deliberately separates real feeds, curated reference data, and simulated operational data.

### Real Or API-Backed

- GDELT public news search: used now for disaster/news signals, but rate-limited.
- OpenWeatherMap: used now when `OPENWEATHERMAP_API_KEY` is set.
- Nominatim/OpenStreetMap: used for geocoding missing locations with `NOMINATIM_USER_AGENT`.
- IMD alerts: placeholder via `IMD_ALERT_FEED_URL` and `IMD_API_KEY`.
- KSNDMC rainfall: placeholder via `KSNDMC_RAINFALL_FEED_URL` and `KSNDMC_API_KEY`.
- KSDMA bulletins: placeholder via `KSDMA_BULLETIN_FEED_URL` and `KSDMA_API_KEY`.
- CWC FloodWatch: placeholder via `CWC_FLOODWATCH_FEED_URL` and `CWC_API_KEY`.
- NewsAPI: optional backup local-news source via `NEWSAPI_KEY`.
- Google News RSS: enabled by default with no key.
- Bing News RSS: enabled by default with no key.
- PIB RSS: enabled by default through `PIB_RSS_URL`.
- NewsData.io: optional free-tier source via `NEWSDATA_API_KEY`.
- TheNewsAPI: optional free-tier source via `THENEWSAPI_TOKEN`.
- Mediastack: optional free-tier source via `MEDIASTACK_API_KEY`.
- GNews: optional free-tier source via `GNEWS_API_KEY`.
- World News API: optional free-tier source via `WORLDNEWSAPI_KEY`.
- FreeNewsApi.io: optional free source via `FREENEWSAPI_KEY`.
- The Guardian Open Platform: optional free developer source via `GUARDIAN_API_KEY`.
- OSRM: optional real routing via `OSRM_BASE_URL`.
- Mapbox: optional map/geocoding provider via `MAPBOX_API_KEY`.

### News Coverage Links

- GDELT DOC API: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
- Google News RSS search: https://news.google.com/rss/search
- Bing News RSS search: https://www.bing.com/news/search
- PIB RSS: https://www.pib.gov.in/RssMain.aspx
- NewsAPI: https://newsapi.org/docs
- NewsData.io: https://newsdata.io/docs
- TheNewsAPI: https://www.thenewsapi.com/documentation
- Mediastack: https://mediastack.com/documentation
- GNews: https://gnews.io/docs/v4
- World News API: https://worldnewsapi.com/docs/
- FreeNewsApi.io: https://freenewsapi.io/
- The Guardian Open Platform: https://open-platform.theguardian.com/

The live disaster tab deduplicates cross-source articles by canonical URL first, then by normalized title token overlap plus overlapping Karnataka locations. The source cards show how many Karnataka matches each provider returned.
By default, news items are filtered to the last `NEWS_LOOKBACK_DAYS=30` days so the disaster tab stays operationally current.

### Curated Reference CSVs

- `01_road_network.csv`: Karnataka relief road graph.
- `02_relief_hubs.csv`: staging hubs and district control points.
- `03_villages_at_risk.csv`: at-risk villages/towns with coordinates and priority.
- `04_historical_disaster_points.csv`: historical flood/landslide/watch points.
- `05_rainfall_thresholds.csv`: rainfall thresholds by district/taluk.
- `06_vehicle_rules.csv`: vehicle suitability rules.
- `07_priority_logic.csv`: relief prioritization rules.

### Simulated Operational CSVs

These are intentionally fake, but structured like realistic control-room data so the project can demonstrate a complete workflow before official integrations exist.

- `08_hub_inventory_simulated.csv`: supplies, quantities, reserves, and reorder levels.
- `09_truck_fleet_simulated.csv`: trucks, vehicle types, load limits, teams, and availability.
- `10_blocked_roads_simulated.csv`: current blocked/partially open roads.
- `11_village_relief_demand_simulated.csv`: village-level food, water, medicine, rescue, and shelter demand.
- `12_field_reports_simulated.csv`: field observations from local responders.
- `13_rescue_teams_simulated.csv`: rescue/NDRF/SDRF/fire/medical teams and deployment status.
- `14_road_passability_rules_simulated.csv`: rainfall, landslide, bridge, and vehicle passability rules.
- `15_external_api_sources_placeholder.csv`: live integration checklist.

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

## API Keys To Add Later

Copy `.env.example` to `.env`, then fill whichever real sources you obtain:

```bash
OPENWEATHERMAP_API_KEY=

IMD_API_KEY=
IMD_ALERT_FEED_URL=

KSNDMC_API_KEY=
KSNDMC_RAINFALL_FEED_URL=

KSDMA_API_KEY=
KSDMA_BULLETIN_FEED_URL=

CWC_API_KEY=
CWC_FLOODWATCH_FEED_URL=

NEWSAPI_KEY=
OSRM_BASE_URL=
MAPBOX_API_KEY=

NEWSDATA_API_KEY=
THENEWSAPI_TOKEN=
MEDIASTACK_API_KEY=
GNEWS_API_KEY=
WORLDNEWSAPI_KEY=
FREENEWSAPI_KEY=
GUARDIAN_API_KEY=

GOOGLE_NEWS_RSS_ENABLED=true
BING_NEWS_RSS_ENABLED=true
PIB_RSS_URL=https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=6
NEWS_LOOKBACK_DAYS=30
```

Until these are filled, the dashboard shows those sources as unavailable or placeholder. It does not mix simulated CSV incidents into live disaster alerts.

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
