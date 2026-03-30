# Requirements: ATLAS AI

**Defined:** 2026-03-30
**Core Value:** Providing actionable supply chain resilience insights through real-time monitoring and predictive disruption modeling using open-source data and local AI.

## v1 Requirements

### Data Ingestion (INGEST)

- [ ] **INGEST-01**: Integrate GDELT for global news event ingestion.
- [ ] **INGEST-02**: Integrate OpenWeatherMap for real-time weather data.
- [ ] **INGEST-03**: Store raw event data locally (CSV/JSON/SQLite).

### NLP Engine (NLP)

- [ ] **NLP-01**: Clean and preprocess text data (tokenization, stopword removal).
- [ ] **NLP-02**: Classify events into categories (e.g., Strike, Disaster, Port Closure) using local HuggingFace models.
- [ ] **NLP-03**: Extract locations (Countries, Cities, Ports) using spaCy NER.
- [ ] **NLP-04**: Link extracted entities to supply chain graph nodes.

### Graph & Intelligence (GRAPH)

- [ ] **GRAPH-01**: Setup Neo4j Community Edition and define supply chain schema (Supplier, Factory, Route).
- [ ] **GRAPH-02**: Assign severity scores (0-1) to events based on logic.
- [ ] **GRAPH-03**: Build a geographic correlation engine to detect multi-hop ripple effects.

### Dashboard UI (DASH)

- [ ] **DASH-01**: Interactive map interface using React and Leaflet.js.
- [ ] **DASH-02**: Real-time event overlay on the map.
- [ ] **DASH-03**: Alert panel for live disruption notifications.

### Prediction Engine (PREDICT)

- [ ] **PREDICT-01**: Calculate initial lead time delay estimates.
- [ ] **PREDICT-02**: Run Monte Carlo simulations for risk distribution.
- [ ] **PREDICT-03**: Calculate "Resilience Scores" for nodes and routes.
- [ ] **PREDICT-04**: Suggest alternative paths using NetworkX (Dijkstra).

### AI Assistant (AI)

- [ ] **AI-01**: Integrate local LLM via Ollama (Mistral/LLaMA) for recommendation generation.
- [ ] **AI-02**: Generate actionable insights based on disruption data and alternatives.
- [ ] **AI-03**: Implement a feedback loop system for user-refined recommendations.

## v2 Requirements

- **TRANS-01**: Real-time transit tracking integration (beyond news-based events).
- **INV-01**: Inventory level visualization and optimization.
- **COST-01**: Financial impact analysis per disruption.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Paid News APIs | GDELT/NewsAPI free tier sufficient for MVP costs. |
| Cloud LLM APIs | Local Ollama preferred to keep system free/private. |
| Multi-user Auth | Single-user prototype focus for initial 30 days. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGEST-01, 02, 03 | Phase 1 | Pending |
| NLP-01, 02, 03, 04 | Phase 1 | Pending |
| GRAPH-01, 02, 03 | Phase 2 | Pending |
| DASH-01, 02, 03 | Phase 2 | Pending |
| PREDICT-01, 02, 03, 04 | Phase 3 | Pending |
| AI-01, 02, 03 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-30*
*Last updated: 2026-03-30 after initialization*
