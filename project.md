# 🧠 ATLAS AI – 30 Day Execution Roadmap

A structured, dependency-aware roadmap for building a real-time AI-powered supply chain monitoring and prediction system.

---

## 💰 Cost Constraint (IMPORTANT)

This project is designed to be:

- ✅ **100% free where possible**
- ⚠️ If not free → use **cheapest available alternatives**
- ❌ Avoid paid APIs unless absolutely necessary

### Preferred Free Stack:

- **News Data:** GDELT (free) > NewsAPI (limited free tier)
- **Weather:** OpenWeatherMap (free tier)
- **NLP:** spaCy / HuggingFace (local models)
- **Graph DB:** Neo4j Community Edition (free)
- **Backend:** FastAPI (free)
- **Frontend:** React + Leaflet (free)
- **LLM:**
  - Preferred: Open-source (LLaMA, Mistral via Ollama)
  - Fallback: OpenAI (only if credits available)

---

# 📅 WEEK 1 — Data + NLP Foundation

## Day 1 — Project Setup & Schema Design

- Define core entities:
  - Event, Supplier, Factory, Route, Product
- Setup:
  - Repo structure
  - Database (JSON/CSV initially — free)
- Output:
  - Defined schema + sample dataset

---

## Day 2 — News & Data Ingestion Pipeline

- Integrate:
  - GDELT (preferred free source)
  - NewsAPI (free tier fallback)
  - OpenWeatherMap (free tier)
- Store raw events locally
- Output:
  - Continuous event ingestion pipeline

---

## Day 3 — Preprocessing Layer

- Clean text:
  - Tokenization
  - Stopword removal
- Use:
  - NLTK / spaCy (free)
- Output:
  - Cleaned event dataset

---

## Day 4 — Event Classification

- Train lightweight classifier:
  - Use HuggingFace (DistilBERT / zero-shot)
- Run locally (no API cost)
- Output:
  - Classified events

---

## Day 5 — NER (Location Extraction)

- Use:
  - spaCy (free)
- Extract:
  - Countries, Cities, Ports
- Output:
  - Structured location tags

---

## Day 6 — NER (Entity Linking)

- Map extracted entities to:
  - Supply chain nodes (custom logic)
- No paid tools
- Output:
  - Linked entities → graph nodes

---

## Day 7 — Data Validation + Storage

- Store structured events:
  - SQLite / JSON (free)
- Output:
  - Clean event dataset ready

---

# 📅 WEEK 2 — Graph + Event Intelligence

## Day 8 — Event Classifier Improvement

- Improve accuracy using:
  - Fine-tuning (optional, local)
- Output:
  - Reliable classification

---

## Day 9 — Severity Scoring

- Assign severity (0–1)
- Pure logic-based (no cost)
- Output:
  - Severity score per event

---

## Day 10 — Geographic Correlation Engine

- Use:
  - Neo4j Community / NetworkX (free)
- Build multi-hop dependency
- Output:
  - Ripple detection system

---

## Day 11 — Graph Database Setup

- Use:
  - Neo4j Community Edition (free)
- Output:
  - Supply chain graph

---

## Day 12 — Dashboard Map UI

- Use:
  - React + Leaflet.js (free)
- Output:
  - Visual graph UI

---

## Day 13 — Real-time Event Overlay

- No paid tools required
- Output:
  - Live event visualization

---

## Day 14 — Alert Panel UI

- Use:
  - WebSockets / polling (free)
- Output:
  - Alert dashboard

---

## Day 15 — Integration Day

- Combine all free components
- Output:
  - Working monitoring system

---

# 📅 WEEK 3 — Prediction & Intelligence

## Day 16 — Lead Time Model (Base)

- Pure mathematical model (free)
- Output:
  - Initial delay estimates

---

## Day 17 — Monte Carlo Simulation

- Use:
  - NumPy (free)
- Output:
  - Risk distribution

---

## Day 18 — Ripple Effect Engine

- Graph traversal (free)
- Output:
  - Ripple score

---

## Day 19 — Pathfinding Optimization

- Use:
  - NetworkX (free)
- Output:
  - Route suggestions

---

## Day 20 — Resilience Score

- Logic-based scoring (free)
- Output:
  - Weak point detection

---

## Day 21 — Multi-scenario Simulation

- Local simulation (free)
- Output:
  - Scenario comparison

---

## Day 22 — Integration Day

- Combine prediction modules
- Output:
  - Fully predictive system

---

# 📅 WEEK 4 — AI Recommendations + Testing

## Day 23 — Alternative Route Suggestion

- Use:
  - Dijkstra via NetworkX (free)
- Output:
  - Decision options

---

## Day 24 — Alternative Supplier Matching

- Query graph (free)
- Output:
  - Supplier alternatives

---

## Day 25 — LLM Recommendation Engine

### Preferred (FREE):

- Ollama + Mistral / LLaMA (local)

### Fallback:

- OpenAI / Claude (only if credits available)

- Output:
  - Actionable insights

---

## Day 26 — Recommendation Refinement

- Prompt engineering (free)
- Output:
  - Better suggestions

---

## Day 27 — Feedback Loop System

- Store feedback:
  - SQLite / JSON
- Output:
  - Learning system

---

## Day 28 — Scenario Dataset Preparation

- Use:
  - Public datasets / manual creation
- Output:
  - Test scenarios

---

## Day 29 — System Testing

- Local testing (free)
- Output:
  - Debugged system

---

## Day 30 — Final Stress Test

- Full pipeline test
- Output:
  - Production-ready system

---

# 🚀 FINAL OUTPUT

A complete AI system with:

- Real-time event monitoring
- Supply chain graph intelligence
- Predictive disruption modeling
- AI-driven recommendations

---

# 🧩 Pipeline Overview

Free Data Sources (GDELT + Weather)
↓
NER + Classification (spaCy + HF local)
↓
Graph Mapping (Neo4j Community)
↓
Correlation Engine
↓
Prediction Engine (NumPy + NetworkX)
↓
Dashboard (React + Leaflet)
↓
LLM Recommendations (Ollama / Free Tier APIs)
