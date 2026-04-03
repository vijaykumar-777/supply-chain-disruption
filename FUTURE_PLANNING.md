# ATLAS AI Future Planning

This document outlines the next major feature additions for the ATLAS AI project. It is intended to serve as a practical implementation roadmap for both frontend and backend expansion.

## Goals

- Complete the currently placeholder frontend views with real workflows.
- Expose more of the backend intelligence already present in the project.
- Improve prediction quality, observability, and usability for real-world monitoring.
- Reduce reliance on mock data and move toward fully live analytics.

## Priority 1: Highest-Value Features

### 1. Live Feed Page

Objective:
Create a fully functional Live Feed page backed by `/api/events`.

Planned capabilities:
- Filter by category
- Filter by severity
- Filter by location
- Filter by time range
- Search event titles and descriptions
- Support manual refresh and auto-refresh

Why this matters:
- The frontend already has a placeholder for Live Feed.
- This is one of the most visible operational views in the product.
- It gives users direct access to disruption monitoring without needing to inspect the dashboard cards.

Suggested implementation:
- Add a dedicated `LiveFeedView` component in the frontend.
- Extend the events API if needed to support query params like `category`, `severity`, `location`, `start_time`, and `end_time`.
- Reuse the current event typing from `frontend/src/services/api.ts`.

Dependencies:
- `/api/events`
- Frontend event hooks

---

### 2. AI Assistant Workflow

Objective:
Build a complete AI assistant page where users can investigate an event, run a simulation, request recommendations, and submit feedback.

Planned capabilities:
- Select an event from the current disruption list
- Choose source and target nodes for route analysis
- Run `/api/simulate`
- Call `/api/recommend`
- Display recommendation output clearly
- Submit helpful or unhelpful feedback through `/api/feedback`

Why this matters:
- The backend already supports this workflow.
- It turns the app from a monitoring dashboard into a decision-support tool.
- It makes the Ollama integration actually usable from the frontend.

Suggested implementation:
- Create an `AIAssistantView` page with a multistep interaction flow.
- Add loading, failure, and offline states for Ollama/API issues.
- Store the most recent simulation result locally in the UI so users can compare multiple scenarios.

Dependencies:
- `/api/simulate`
- `/api/recommend`
- `/api/feedback`
- Graph node data for route selection

---

### 3. Real Analytics Page

Objective:
Replace placeholder analytics with real charts and trends.

Planned capabilities:
- Event trends over time
- Event category breakdown
- Critical-event count over time
- Average predicted delay
- Potential future chart for region-wise disruption density

Why this matters:
- The current dashboard still uses mock chart data.
- Analytics is one of the strongest differentiators for this project.
- It helps users move from reacting to understanding patterns.

Suggested implementation:
- Add new backend aggregation endpoints for analytics.
- Replace mock chart sources in the frontend.
- Support chart time windows such as 24h, 7d, and 30d.

Dependencies:
- Historical event storage
- Trend aggregation API

---

### 4. Node Detail Panels on the Map

Objective:
Make the map interactive beyond basic markers by allowing deep inspection of supply chain nodes.

Planned capabilities:
- Show connected disruptions
- Show resilience score
- Show routes connected to that node
- Show affected regions or downstream dependencies
- Display node metadata like type, country, and role

Why this matters:
- The map is a core part of the product experience.
- This adds meaningful analysis to each node instead of just visual presence.
- It creates a bridge between graph intelligence and the UI.

Suggested implementation:
- Add a node detail side panel or modal.
- Introduce a dedicated backend endpoint for node details if the existing graph-node response is too thin.
- Expose resilience score from the NetworkX model.

Dependencies:
- `/api/graph/nodes`
- Neo4j graph traversal
- Resilience scoring from `src/prediction/network_model.py`

---

### 5. Route Simulation UI

Objective:
Allow users to simulate disruption scenarios visually in the frontend.

Planned capabilities:
- Select source node
- Select target node
- Choose disrupted nodes
- Compare optimal route and alternative route
- Display simulation outputs such as mean delay, p50, p95, and worst case
- Show the selected route on the map when possible

Why this matters:
- The backend simulation engine is already present.
- This is one of the most practical operations-focused features in the system.
- It supports real scenario planning for logistics teams.

Suggested implementation:
- Add a route simulation panel either inside Analytics or AI Assistant.
- Use graph node data to populate dropdowns.
- Add route visualization overlay on the map.

Dependencies:
- `/api/simulate`
- Node inventory from graph APIs

## Priority 2: Strong Backend Upgrades

### 6. Weather-Powered Risk Scoring

Objective:
Integrate live weather conditions into event severity and dashboard metrics.

Current gap:
- `weather_alerts` is still hardcoded to `0` in `src/api/main.py`.
- Weather ingestion exists in `src/ingestion/weather_client.py` but is not fully connected to the risk pipeline.

Planned capabilities:
- Fetch weather for monitored node coordinates
- Detect severe conditions
- Increase disruption severity based on weather rules
- Surface active weather alerts in dashboard metrics

Why this matters:
- Weather is a major real-world supply chain risk factor.
- This makes the dashboard metrics more realistic and dynamic.

Suggested implementation:
- Add a scheduled weather refresh job.
- Cache weather responses locally to avoid unnecessary requests.
- Create a scoring rule that combines disruption category, keyword severity, and weather severity.

Dependencies:
- OpenWeatherMap integration
- Node coordinates
- Severity scoring logic

---

### 7. Natural-Language Search

Objective:
Add search across events and graph nodes using plain-language queries.

Planned capabilities:
- Search events by title, category, and description
- Search nodes by name, country, or label
- Support queries like "strikes in Asia" or "ports affected by storms"

Why this matters:
- The frontend spec already calls for this.
- It improves usability as the dataset grows.
- It reduces the need for manual filtering through long feeds.

Suggested implementation:
- Start with backend text matching and filters.
- Later expand into NLP-assisted query interpretation.
- Add a unified `/api/search` endpoint returning both events and nodes.

Dependencies:
- Event dataset
- Graph node dataset
- NLP preprocessing layer for advanced search later

---

### 8. Improved Entity Linking

Objective:
Upgrade entity extraction from stub mapping into graph-aware linking.

Current gap:
- `src/nlp/ner_extractor.py` currently formats simple placeholder node IDs.

Planned capabilities:
- Match extracted locations to real Neo4j `Location` nodes
- Match organizations to supplier, factory, or partner nodes
- Handle fuzzy matches and aliases
- Return confidence scores for linked entities

Why this matters:
- Better entity linking improves downstream graph accuracy.
- It enables more reliable correlations and route impact analysis.
- It reduces false positives in disruption mapping.

Suggested implementation:
- Add lookup tables and fuzzy matching logic.
- Maintain alias dictionaries for ports, cities, and suppliers.
- Return both raw entities and matched graph node references.

Dependencies:
- spaCy NER extraction
- Neo4j node inventory
- Matching logic and normalization rules

---

### 9. Event History Storage and Trend APIs

Objective:
Persist event history so charts and trend analysis are backed by real data.

Current gap:
- The frontend chart area still depends on mock values.
- Trend analysis cannot mature without historical storage.

Planned capabilities:
- Store event snapshots over time
- Track event frequency by day or hour
- Track severity distribution historically
- Aggregate metrics for frontend analytics

Why this matters:
- Historical data is essential for real analytics.
- It enables forecasting, reporting, and anomaly detection.

Suggested implementation:
- Store processed events in SQLite or JSON as a first step.
- Later migrate to a more structured persistent store if needed.
- Add endpoints such as `/api/analytics/trends` and `/api/analytics/categories`.

Dependencies:
- Event ingestion pipeline
- Analytics endpoint design

---

### 10. Alert Thresholds and Subscriptions

Objective:
Allow users to define custom alert rules and subscribe to important disruptions.

Planned capabilities:
- Alert when severity exceeds a threshold
- Alert when a specific node or port is affected
- Alert when a category appears in a selected region
- Support future notification channels like email, webhooks, or in-app alerts

Why this matters:
- Personalized alerting makes the platform operationally useful.
- It helps users focus on the disruptions that matter to them.

Suggested implementation:
- Start with in-app saved alert rules.
- Add backend evaluation logic against incoming events.
- Later extend to notification delivery integrations.

Dependencies:
- Event processing pipeline
- User preference storage
- Threshold evaluation logic

## Suggested Delivery Phases

### Phase 1: Frontend Completion

- Live Feed page
- AI Assistant page
- Route Simulation UI
- Node detail panel

### Phase 2: Data and Analytics Foundation

- Event history storage
- Trend APIs
- Real Analytics page
- Search API

### Phase 3: Intelligence Upgrades

- Weather-powered risk scoring
- Improved entity linking
- Alert rules and subscriptions

## Recommended Order of Implementation

1. Live Feed page
2. AI Assistant page
3. Route Simulation UI
4. Event history storage and trend APIs
5. Analytics page
6. Node detail panels
7. Weather-powered risk scoring
8. Natural-language search
9. Improved entity linking
10. Alert thresholds and subscriptions

## Notes

- The fastest wins come from exposing backend features that already exist through the frontend.
- The most important backend investment is historical event storage, because it unlocks analytics, reporting, and better forecasting.
- Weather scoring and entity linking should be treated as quality multipliers once the end-to-end user workflows are in place.
