# Roadmap: ATLAS AI

## Overview

The roadmap spans 4 phases (aligned with the 30-day plan) to build a real-time AI supply chain monitoring system. Starting with data ingestion and NLP foundation, moving to graph database integration and UI visualization, then layering on predictive modeling, and concluding with a local AI recommendation engine.

## Phases

- [ ] **Phase 1: Data & NLP Foundation** - Set up news/weather ingestion and NLP preprocessing pipelines.
- [ ] **Phase 2: Graph Intelligence & Dashboard** - Integrate Neo4j and build the interactive map dashboard.
- [ ] **Phase 3: Prediction & Simulation** - Implement lead time modeling, Monte Carlo risk simulation, and pathfinding.
- [ ] **Phase 4: AI Recommendations & Refinement** - Integrate local LLM via Ollama and implement feedback loops.

## Phase Details

### Phase 1: Data & NLP Foundation
**Goal**: Establish the automated data pipelines and unstructured text processing layer.
**Depends on**: Nothing
**Requirements**: INGEST-01, INGEST-02, INGEST-03, NLP-01, NLP-02, NLP-03, NLP-04
**Success Criteria**:
  1. System automatically fetches latest global news events via GDELT.
  2. News text is correctly cleaned and processed into tokenized/structured format.
  3. Locations (Cities/Ports) are successfully extracted from event text with >80% accuracy.
  4. Events are classified into supply chain disruption categories (e.g., Strike, Natural Disaster).
**Plans**: 4 plans

Plans:
- [ ] 01-01: Setup repository structure and data ingestion pipeline (GDELT/Weather).
- [ ] 01-02: Implement NLP preprocessing layer with spaCy/NLTK.
- [ ] 01-03: Develop event classifier using local HuggingFace models.
- [ ] 01-04: Implement NER and entity linking for geographical mapping.

### Phase 2: Graph Intelligence & Dashboard
**Goal**: Map disruptions to supply chain nodes and visualize them on an interactive dashboard.
**Depends on**: Phase 1
**Requirements**: GRAPH-01, GRAPH-02, GRAPH-03, DASH-01, DASH-02, DASH-03
**Success Criteria**:
  1. Neo4j graph database is operational with defined Supplier/Factory/Route schema.
  2. Events are linked to graph nodes, and severity scores are correctly assigned.
  3. Interactive map displays live event overlays and supply chain network.
  4. Alert panel updates in real-time as new disruptions are detected.
**Plans**: TBD

Plans:
- [ ] 02-01: Setup Neo4j and implement supply chain node/route mapping.
- [ ] 02-02: Develop severity scoring and geographic correlation engine.
- [ ] 02-03: Create React + Leaflet map dashboard with real-time overlays.

### Phase 3: Prediction & Simulation
**Goal**: Add predictive intelligence to quantify risks and suggest mitigations.
**Depends on**: Phase 2
**Requirements**: PREDICT-01, PREDICT-02, PREDICT-03, PREDICT-04
**Success Criteria**:
  1. System provides lead time delay estimates based on disruption severity.
  2. Monte Carlo simulations generate risk distributions for key routes.
  3. Alternative routes are suggested via Dijkstra pathfinding during disruptions.
**Plans**: TBD

Plans:
- [ ] 03-01: Implement lead time modeling and resilience scoring.
- [ ] 03-02: Develop Monte Carlo simulation engine for route risk distribution.
- [ ] 03-03: Implement pathfinding optimization for alternative route suggestion.

### Phase 4: AI Recommendations & Refinement
**Goal**: Integrate human-like reasoning and feedback to improve system insights.
**Depends on**: Phase 3
**Requirements**: AI-01, AI-02, AI-03
**Success Criteria**:
  1. Local LLM (Ollama) generates readable, actionable summaries of disruptions.
  2. System suggests specific mitigation steps (e.g., "Switch to Supplier B via Route C").
  3. User feedback is stored and used to refine future recommendations.
**Plans**: TBD

Plans:
- [ ] 04-01: Integrate Ollama and implement recommendation prompt engineering.
- [ ] 04-02: Develop feedback loop system and conduct final stress testing.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data & NLP Foundation | 0/4 | Not started | - |
| 2. Graph & Dashboard | 0/3 | Not started | - |
| 3. Prediction & Simulation | 0/3 | Not started | - |
| 4. AI Assistant | 0/2 | Not started | - |

---
*Roadmap defined: 2026-03-30*
*Last updated: 2026-03-30 after initial definition*
