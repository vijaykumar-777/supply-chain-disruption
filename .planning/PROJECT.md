# ATLAS AI

## What This Is

ATLAS AI is a real-time AI-powered supply chain monitoring and prediction system. It ingests data from public sources (news, weather) to identify potential disruptions and uses graph intelligence and predictive modeling to suggest alternative routes and suppliers, all while prioritizing a free or low-cost technology stack.

## Core Value

Providing actionable supply chain resilience insights through real-time monitoring and predictive disruption modeling using open-source data and local AI.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] News & Data Ingestion Pipeline (GDELT, OpenWeatherMap)
- [ ] NLP Preprocessing Layer (spaCy/NLTK)
- [ ] Event Classification (HuggingFace local models)
- [ ] NER & Entity Linking (Location extraction & mapping)
- [ ] Supply Chain Graph Database (Neo4j Community)
- [ ] Severity Scoring & Geographic Correlation Engine
- [ ] Real-time Dashboard Map UI (React + Leaflet.js)
- [ ] Alert Panel UI (WebSockets/Polling)
- [ ] Predictive Modeling (Lead Time, Monte Carlo, Ripple Effect)
- [ ] Pathfinding & Optimization (NetworkX/Dijkstra)
- [ ] LLM Recommendation Engine (Ollama/Mistral/LLaMA)
- [ ] Feedback Loop & System Testing

### Out of Scope

- [Paid News APIs] — Using GDELT/NewsAPI free tier instead to minimize costs.
- [High-cost LLM APIs] — Prioritizing local Ollama models unless credits are available.

## Context

The project is structured as a 30-day execution roadmap. It focuses on building a full-stack intelligence system from data ingestion to actionable recommendations. The user has provided a detailed daily breakdown of tasks in `project.md`.

## Constraints

- **Cost**: 100% free where possible, use cheapest alternatives if not.
- **Data Sources**: News (GDELT), Weather (OpenWeatherMap).
- **Backend**: FastAPI, Python (spaCy, HuggingFace, NumPy, NetworkX).
- **Database**: Neo4j Community Edition (Graph), SQLite/JSON (Local Storage).
- **Frontend**: React, Leaflet.js.
- **LLM**: Ollama (Local) preferred.
- **Timeline**: 30-day development cycle.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use GDELT | Free, comprehensive global event database. | — Pending |
| Use Neo4j Community | Native graph processing for supply chain dependencies. | — Pending |
| Use React + Leaflet | Open-source, flexible mapping solution. | — Pending |
| Use Ollama | Local LLM execution to avoid API costs. | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-30 after initialization*
