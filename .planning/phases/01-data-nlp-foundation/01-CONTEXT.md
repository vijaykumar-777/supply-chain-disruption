# Phase 1: Data & NLP Foundation - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning
**Source:** PRD Express Path (project.md)

<domain>
## Phase Boundary

This phase delivers the automated real-time data ingestion pipelines using GDELT and OpenWeatherMap APIs (free tier focus), plus the unstructured text processing layer using local open-source tools (spaCy, NLTK, HuggingFace DistilBERT) to clean, classify, and extract geographical entities (NER) from supply chain news events.
</domain>

<decisions>
## Implementation Decisions

### Data Ingestion
- Use GDELT for global news event ingestion (100% free)
- Use OpenWeatherMap for real-time weather data
- Store raw event data locally (CSV/JSON/SQLite) to avoid database costs early on

### NLP Preprocessing
- Use spaCy/NLTK for text cleaning (tokenization, stopword removal)
- Use local HuggingFace models (e.g. DistilBERT / zero-shot) for zero-cost event classification (Strike, Disaster, Port Closure)

### Named Entity Recognition
- Use spaCy for extracting locations (Countries, Cities, Ports)
- Map extracted locations to supply chain nodes (custom logic)

### the agent's Discretion
- Code architecture and module separation (e.g. `src/ingestion`, `src/nlp`).
- Configuration parsing (e.g. `.env` for OpenWeatherMap keys).
- Logging format and structure.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Specifications
- `project.md` — The original 30-day roadmap and project specifications.
- `.planning/PROJECT.md` — The overall project purpose and constraints.
- `.planning/ROADMAP.md` — Phased goals.
</canonical_refs>

<specifics>
## Specific Ideas

- The stack must strictly avoid paid APIs. Run classification and NER locally.
- GDELT is the preferred data source over NewsAPI. If NewsAPI is used, strictly obey free tier limits.
- The pipeline should be a continuous or scheduled event ingestion pipeline.
- This is the very foundation; output should be structured event data ready for SQLite/Graph consumption.
</specifics>

<deferred>
## Deferred Ideas

- Graph database (Neo4j) creation is deferred to Phase 2.
- UI/Dashboard is deferred to Phase 2.
- Predictive models are deferred to Phase 3.
- Recommendations LLM (Ollama) is deferred to Phase 4.
</deferred>

---

*Phase: 01-data-nlp-foundation*
*Context gathered: 2026-03-30 via PRD Express Path*
