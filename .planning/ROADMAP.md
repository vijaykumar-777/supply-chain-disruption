# Roadmap: ATLAS AI

## Overview

The roadmap spans 7 phases to build a world-class real-time AI supply chain monitoring and decision-support system. Phases 1–4 established the core prototype. Phases 5–7 complete the frontend, add real analytics, and layer in intelligence upgrades.

## Phases

- [x] **Phase 1: Data & NLP Foundation** - Set up news/weather ingestion and NLP preprocessing pipelines.
- [x] **Phase 2: Graph Intelligence & Dashboard** - Integrate Neo4j and build the interactive map dashboard.
- [x] **Phase 3: Prediction & Simulation** - Implement lead time modeling, Monte Carlo risk simulation, and pathfinding.
- [x] **Phase 4: AI Recommendations & Refinement** - Integrate local LLM via Ollama and implement feedback loops.
- [ ] **Phase 5: Frontend Completion** - Replace all placeholder views with real, fully interactive workflows.
- [ ] **Phase 6: Data & Analytics Foundation** - Persist event history and deliver real chart data.
- [ ] **Phase 7: Intelligence Upgrades** - Weather risk scoring, improved entity linking, alert subscriptions.

## Phase Details

### Phase 1: Data & NLP Foundation
**Goal**: Establish the automated data pipelines and unstructured text processing layer.
**Depends on**: Nothing
**Requirements**: INGEST-01, INGEST-02, INGEST-03, NLP-01, NLP-02, NLP-03, NLP-04
**Status**: ✓ Done (2026-03-30)
**Success Criteria**:
  1. System automatically fetches latest global news events via GDELT.
  2. News text is correctly cleaned and processed into tokenized/structured format.
  3. Locations (Cities/Ports) are successfully extracted from event text with >80% accuracy.
  4. Events are classified into supply chain disruption categories (e.g., Strike, Natural Disaster).

Plans:
- [x] 01-01: Setup repository structure and data ingestion pipeline (GDELT/Weather).
- [x] 01-02: Implement NLP preprocessing layer with spaCy/NLTK.
- [x] 01-03: Develop event classifier using local HuggingFace models.
- [x] 01-04: Implement NER and entity linking for geographical mapping.

---

### Phase 2: Graph Intelligence & Dashboard
**Goal**: Map disruptions to supply chain nodes and visualize them on an interactive dashboard.
**Depends on**: Phase 1
**Requirements**: GRAPH-01, GRAPH-02, GRAPH-03, DASH-01, DASH-02, DASH-03
**Status**: ✓ Done (2026-04-02)
**Success Criteria**:
  1. Neo4j graph database is operational with defined Supplier/Factory/Route schema.
  2. Events are linked to graph nodes, and severity scores are correctly assigned.
  3. Interactive map displays live event overlays and supply chain network.
  4. Alert panel updates in real-time as new disruptions are detected.

Plans:
- [x] 02-01: Setup Neo4j and implement supply chain node/route mapping.
- [x] 02-02: Develop severity scoring and geographic correlation engine.
- [x] 02-03: Create React + Leaflet map dashboard with real-time overlays.

---

### Phase 3: Prediction & Simulation
**Goal**: Add predictive intelligence to quantify risks and suggest mitigations.
**Depends on**: Phase 2
**Requirements**: PREDICT-01, PREDICT-02, PREDICT-03, PREDICT-04
**Status**: ✓ Done (2026-04-02)
**Success Criteria**:
  1. System provides lead time delay estimates based on disruption severity.
  2. Monte Carlo simulations generate risk distributions for key routes.
  3. Alternative routes are suggested via Dijkstra pathfinding during disruptions.

Plans:
- [x] 03-01: Implement lead time modeling and resilience scoring.
- [x] 03-02: Develop Monte Carlo simulation engine for route risk distribution.
- [x] 03-03: Implement pathfinding optimization for alternative route suggestion.

---

### Phase 4: AI Recommendations & Refinement
**Goal**: Integrate human-like reasoning and feedback to improve system insights.
**Depends on**: Phase 3
**Requirements**: AI-01, AI-02, AI-03
**Status**: ✓ Done (2026-04-02)
**Success Criteria**:
  1. Local LLM (Ollama) generates readable, actionable summaries of disruptions.
  2. System suggests specific mitigation steps (e.g., "Switch to Supplier B via Route C").
  3. User feedback is stored and used to refine future recommendations.

Plans:
- [x] 04-01: Integrate Ollama and implement recommendation prompt engineering.
- [x] 04-02: Develop feedback loop system and conduct final stress testing.

---

### Phase 5: Frontend Completion
**Goal**: Replace all placeholder frontend views with real, fully interactive workflows backed by existing APIs.
**Depends on**: Phase 4
**Priority**: Highest — exposes existing backend intelligence to users immediately with zero new backend work.
**Status**: ○ Planned
**Success Criteria**:
  1. Live Feed page shows real events with filtering by category, severity, location, and time range — supports manual and auto-refresh.
  2. AI Assistant page supports the full select-event → simulate → recommend → feedback workflow end-to-end.
  3. Route Simulation UI allows visual scenario planning with source/target/disrupted node selection and result display.
  4. Node Detail Panels on the map expose resilience score, connected disruptions, routes, and node metadata.

Plans:
- [ ] 05-01: Build `LiveFeedView` component backed by `/api/events` with full filter, search, and refresh support.
- [ ] 05-02: Build `AIAssistantView` multi-step page — event selection, run simulate, display recommendations, submit feedback.
- [ ] 05-03: Build Route Simulation Panel — node/disruption selectors, mean/p50/p95/worst-case output, optional map overlay.
- [ ] 05-04: Build Node Detail Side Panel/Modal on map — resilience score, connected routes, affected regions, node metadata.

---

### Phase 6: Data & Analytics Foundation
**Goal**: Persist event history and provide real chart data to replace all mock analytics.
**Depends on**: Phase 5
**Priority**: High — foundational for meaningful analytics, reporting, and future forecasting.
**Status**: ○ Planned
**Success Criteria**:
  1. Processed events are persisted over time and queryable by time window (24h / 7d / 30d).
  2. `/api/analytics/trends` and `/api/analytics/categories` endpoints return real aggregated data.
  3. Analytics page renders live charts: event trends, category breakdown, critical event count, average delay.
  4. Unified `/api/search` endpoint returns matched events and graph nodes from plain-language queries.

Plans:
- [ ] 06-01: Implement event history storage (SQLite snapshots) with ingestion hook on event processing.
- [ ] 06-02: Add `/api/analytics/trends` and `/api/analytics/categories` aggregation endpoints.
- [ ] 06-03: Replace mock chart sources in the Analytics page with real API data; support 24h/7d/30d time windows.
- [ ] 06-04: Add unified `/api/search` endpoint with text/filter matching across events and graph nodes.

---

### Phase 7: Intelligence Upgrades
**Goal**: Improve real-world accuracy with weather-driven severity, better entity linking, and user-defined alert subscriptions.
**Depends on**: Phase 6
**Priority**: Medium — quality multipliers to activate once end-to-end user workflows are fully live.
**Status**: ○ Planned
**Success Criteria**:
  1. Live weather conditions dynamically adjust disruption severity and surface active weather alerts in dashboard metrics.
  2. Extracted entities are fuzzy-matched to real Neo4j nodes with confidence scores and alias handling.
  3. Users can define saved alert rules (severity threshold, specific node/port, category + region) and receive in-app notifications.

Plans:
- [ ] 07-01: Integrate `weather_client.py` into the risk pipeline — scheduled refresh, caching, weather-based severity scoring, dashboard metrics update.
- [ ] 07-02: Upgrade `ner_extractor.py` — fuzzy match extracted locations/orgs to Neo4j nodes, alias dictionaries, confidence scores.
- [ ] 07-03: Implement alert-rules engine — saved user rules, backend evaluation against incoming events, in-app alert delivery.

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data & NLP Foundation | 4/4 | ✓ Done | 2026-03-30 |
| 2. Graph & Dashboard | 3/3 | ✓ Done | 2026-04-02 |
| 3. Prediction & Simulation | 3/3 | ✓ Done | 2026-04-02 |
| 4. AI Assistant | 2/2 | ✓ Done | 2026-04-02 |
| 5. Frontend Completion | 0/4 | ○ Planned | — |
| 6. Data & Analytics Foundation | 0/4 | ○ Planned | — |
| 7. Intelligence Upgrades | 0/3 | ○ Planned | — |

---
*Roadmap defined: 2026-03-30*
*Last updated: 2026-04-03 — Added Phases 5–7 from FUTURE_PLANNING.md (11 new plans)*
