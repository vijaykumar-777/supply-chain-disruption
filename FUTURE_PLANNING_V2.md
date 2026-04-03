# ATLAS AI — Future Planning V2

_Generated: 2026-04-03 | Based on full project audit_

---

## Audit: Confirmed Findings

The following findings were verified against the live codebase. All six are **confirmed true**.

### [CONFIRMED — P1] Three major frontend views are still placeholders

**File:** `frontend/src/App.tsx`, lines 21–23

The component directories `frontend/src/components/ai/`, `frontend/src/components/feed/`, and `frontend/src/components/analytics/` exist but are **completely empty**.

---

### [CONFIRMED — P1] Weather alerts are still hardcoded to zero

**File:** `src/api/main.py`, line 155

`src/ingestion/weather_client.py` exists and can call OpenWeatherMap, but it is never invoked by the API. The `WeatherClient` class has `fetch_weather(lat, lon)` but no scoring logic connects it to the risk pipeline.

Additional bug: `src/config.py` exports `OPENWEATHER_API_KEY` but `weather_client.py` imports `OPENWEATHERMAP_API_KEY` — a silent env var mismatch.

---

### [CONFIRMED — P1] No analytics, search, or history endpoints exist

The only endpoints currently exposed are:
- `GET /health`
- `GET /api/events`
- `GET /api/graph/nodes`
- `GET /api/metrics`
- `POST /api/simulate`
- `POST /api/recommend`
- `POST /api/feedback`

There is **no** `/api/analytics`, `/api/analytics/trends`, `/api/search`, `/api/alerts`, or any weather-scoring endpoint.

---

### [CONFIRMED — P2] Dashboard chart is driven by mock data

**File:** `frontend/src/components/dashboard/DashboardView.tsx`, line 13 and lines 149–157

`LOGISTICS_VOLUME_DATA` imported from `mockData.tsx` — 7 hardcoded data points. No event persistence exists on the backend.

---

### [CONFIRMED — P2] Node detail panels do not exist; map uses basic popups only

**File:** `frontend/src/components/dashboard/GlobalMapView.tsx`, lines 68–74

Clicking a node shows only name, labels, and country. `calculate_resilience_score()` exists in `src/prediction/network_model.py` but is never called from any API endpoint.

---

### [CONFIRMED — P2] NER entity linking is still a stub

**File:** `src/nlp/ner_extractor.py`, lines 42–60

`link_entities_to_nodes()` generates synthetic IDs like `NODE_LOC_SINGAPORE` instead of matching against real Neo4j node identifiers.

---

## What Is Already Working

| Component | Status | Notes |
|---|---|---|
| FastAPI backend | ✅ Functional | 7 endpoints, CORS configured |
| `/api/simulate` | ✅ Functional | Monte Carlo + NetworkX pathfinding wired up |
| `/api/recommend` | ✅ Functional | Calls local Ollama with structured prompt |
| `/api/feedback` | ✅ Functional | Persists to `data/feedback_loop.json` |
| `useSimulation` hook | ✅ Ready | In `useAtlasData.ts` — just needs a UI |
| `api.recommend()` | ✅ Ready | Full call defined in `services/api.ts` |
| Global Map | ✅ Functional | Live Leaflet map with real nodes and events |
| Dashboard KPIs | ✅ Functional | Polling `/api/metrics` and `/api/events` |
| Dashboard event feed | ✅ Functional | Real events from Neo4j |
| `WeatherClient` | ⚠️ Disconnected | Client exists, never called from API |
| `EntityExtractor` | ⚠️ Stub linking | NER extraction real; linking is synthetic |

---

## Phase 1 — Frontend Completion (Highest Immediate Impact)

> The backend already supports all of these workflows. Phase 1 is about surfacing that intelligence in the UI.

### 1.1 — AI Assistant Workflow (`frontend/src/components/ai/`)

**Multistep interaction flow:**

1. **Select Event** — Dropdown from `/api/events`, shows title + severity badge
2. **Define Route** — Source / target / disrupted nodes from `/api/graph/nodes`
3. **Run Simulation** — Calls `POST /api/simulate`, shows optimal route chain, alt route, and stats (mean, p50, p95, worst case, std dev)
4. **Get AI Recommendation** — Calls `POST /api/recommend`, renders Ollama output in a styled card
5. **Rate Recommendation** — Thumbs up/down + comment → `POST /api/feedback`

**States to handle:** Ollama offline, no route found (404), loading (Ollama can take 5–30s)

**Technical approach:**
- Create `AIAssistantView.tsx` inside `frontend/src/components/ai/`
- Reuse existing `useSimulation()` hook
- Add `useRecommendation()` hook in `useAtlasData.ts`
- Store last simulation in local state for scenario comparison

**Dependencies:** All backend endpoints exist ✅

---

### 1.2 — Live Feed Page (`frontend/src/components/feed/`)

**Planned capabilities:**
- Filter bar: Category dropdown, Severity chips (critical/warning/info), Location text input
- Time range selector: 1h / 6h / 24h / 7d
- Real-time text search on titles and descriptions (client-side)
- Manual refresh + auto-refresh toggle (15s interval)
- Event cards with severity indicator, timestamp, category badge, location tags, and description
- Export visible events to CSV

**Backend extension needed:** Add optional query params to `GET /api/events`: `?category=&severity_min=&location=&hours_back=`

---

### 1.3 — Analytics View (`frontend/src/components/analytics/`)

**Phase 1 version (live event data, no history yet):**
- Event category breakdown pie chart — from live `/api/events`
- Top affected locations bar chart — from live `/api/events`
- Time-trend charts — placeholder until Phase 2 adds persistence
- Remove `LOGISTICS_VOLUME_DATA` from `DashboardView.tsx`

---

## Phase 2 — Data Foundation

### 2.1 — Event History Persistence

**New file:** `src/storage/event_store.py`

SQLite `data/event_history.db` with `events` table:
```sql
CREATE TABLE events (
  id TEXT PRIMARY KEY,
  title TEXT, category TEXT, severity REAL,
  timestamp TEXT, locations TEXT,
  ingested_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

On every `/api/events` request, upsert results into SQLite via FastAPI `BackgroundTasks`.

---

### 2.2 — Analytics & Trend Endpoints

**New file:** `src/api/analytics_router.py`

```
GET /api/analytics/trends?window=7d
GET /api/analytics/categories
GET /api/analytics/locations
GET /api/analytics/summary
```

All queries run against SQLite `event_history.db`. Include via `app.include_router()` in `main.py`.

---

### 2.3 — Weather-Powered Risk Scoring

**Steps:**
1. Fix env var name: `OPENWEATHER_API_KEY` → `OPENWEATHERMAP_API_KEY` (or vice versa, pick one)
2. Add `WeatherScorer` class that fetches weather for node coordinates and applies severity rules:
   - Wind speed > 50 km/h → flag
   - Heavy precipitation → flag
   - Extreme condition codes → flag
3. Cache in `data/weather_cache.json` with 30-minute TTL
4. Return real `weather_alerts` count from `/api/metrics`

---

### 2.4 — Natural-Language Search

```
GET /api/search?q=strikes+Asia&types=events,nodes
→ Returns: { "events": [...], "nodes": [...] }
```

Phase 2: SQLite `LIKE` for events + Neo4j text match for nodes.
Phase 3 upgrade: Use existing spaCy pipeline to parse query intent.

---

## Phase 3 — Intelligence Upgrades

### 3.1 — Node Detail Panels on the Map

**New backend endpoint:**
```
GET /api/graph/nodes/{node_id}
→ { id, name, labels, country, lat, lon,
    resilience_score, connected_events, in_routes, out_routes }
```

`calculate_resilience_score()` already exists in `network_model.py` — just needs to be called.

**Frontend:** Replace Leaflet `<Popup>` with click handler → slide-in `NodeDetailPanel.tsx`

---

### 3.2 — Improved Entity Linking

**Replace stub `link_entities_to_nodes()` with:**
1. `NodeIndex` class — loads all Neo4j node names into a lookup dict at startup
2. Fuzzy matching using `rapidfuzz` (free library)
3. Return matched Neo4j node ID + confidence score
4. Fall back to stub only if confidence < 0.7

---

### 3.3 — Alert Thresholds and Subscriptions

**New endpoints:**
```
GET  /api/alerts/rules
POST /api/alerts/rules   { condition_type, threshold, node_id, category, region }
DELETE /api/alerts/rules/{rule_id}
GET  /api/alerts/active
```

Store rules in `data/alert_rules.json`. Evaluate on each `/api/events` poll cycle.

---

## Phase 4 — Polish & Resilience

### 4.1 — Automated Ingestion Scheduler
Use `APScheduler` or FastAPI `lifespan` to run GDELT ingestion (every 15 min) and weather cache refresh (every 30 min) automatically. Add `GET /api/system/status` showing last run timestamps.

### 4.2 — Route Visualization Overlay on Map
After `/api/simulate` returns, draw polylines on the Leaflet map connecting the optimal route nodes. Dashed line for alternative route. Disrupted nodes highlighted in red.

### 4.3 — Export Features
- Live feed → CSV
- Simulation result → formatted PDF
- Analytics data → JSON download

### 4.4 — Remove All Mock Data
After Phase 2.2 analytics endpoints exist, replace `LOGISTICS_VOLUME_DATA` in `DashboardView.tsx` and delete unused entries from `mockData.tsx`.

---

## Recommended Implementation Order

| # | Feature | Phase | Priority | Effort |
|---|---|---|---|---|
| 1 | AI Assistant Workflow | 1.1 | 🔴 Critical | Medium — backend ready |
| 2 | Live Feed Page | 1.2 | 🔴 Critical | Low — frontend only |
| 3 | Analytics View (shell) | 1.3 | 🟠 High | Low — UI only |
| 4 | Event History Storage | 2.1 | 🔴 Critical | Medium |
| 5 | Analytics & Trend APIs | 2.2 | 🟠 High | Medium |
| 6 | Weather Risk Scoring | 2.3 | 🟠 High | Medium |
| 7 | Natural-Language Search | 2.4 | 🟡 Medium | Medium |
| 8 | Node Detail Panels | 3.1 | 🟡 Medium | Medium |
| 9 | Improved Entity Linking | 3.2 | 🟡 Medium | Medium |
| 10 | Alert Subscriptions | 3.3 | 🟡 Medium | Medium |
| 11 | Ingestion Scheduler | 4.1 | 🟢 Polish | Low |
| 12 | Route Overlay on Map | 4.2 | 🟢 Polish | Low |
| 13 | Export Features | 4.3 | 🟢 Polish | Low |
| 14 | Remove All Mock Data | 4.4 | 🟢 Cleanup | Low (after 2.2) |

---

## Quick Wins (Start Immediately)

1. **Fix env var mismatch** — `OPENWEATHER_API_KEY` vs `OPENWEATHERMAP_API_KEY` — one-line fix
2. **Wire `AIAssistantView`** — `useSimulation()` hook exists, zero backend changes needed
3. **Wire `LiveFeedView`** — `useEvents()` hook exists, just needs a component + filter UI
4. **Expose resilience score** — `calculate_resilience_score()` exists, calling it is a 5-line API change

---

## Technical Debt Register

| Item | File | Issue |
|---|---|---|
| Env var name mismatch | `src/config.py` vs `weather_client.py` | `OPENWEATHER_API_KEY` vs `OPENWEATHERMAP_API_KEY` |
| Stub entity linking | `src/nlp/ner_extractor.py:42–60` | `link_entities_to_nodes()` generates fictitious IDs |
| Hardcoded `weather_alerts: 0` | `src/api/main.py:155` | Never reflects real data |
| Mock chart data | `frontend/src/constants/mockData.tsx` | `LOGISTICS_VOLUME_DATA` drives dashboard chart |
| Empty component folders | `ai/`, `feed/`, `analytics/` under `components/` | Created but completely empty |
| Resilience score unused | `src/prediction/network_model.py` | `calculate_resilience_score()` never called from API |

---

## Notes

- The fastest path to a demo-ready system is completing **Phase 1** — it exposes all already-built backend intelligence through a proper UI.
- The most valuable backend investment is **event history storage** (2.1) — it unblocks analytics, trend APIs, and eventually forecasting.
- Weather scoring and entity linking are **quality multipliers** — they improve accuracy but should come after primary user journeys are built.
- All cost constraints remain in force: Ollama (local), Neo4j Community, GDELT, OpenWeatherMap free tier, SQLite — 100% free stack.

---

_Last updated: 2026-04-03 — ATLAS AI V2 Roadmap_
