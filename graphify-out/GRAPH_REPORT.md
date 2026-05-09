# Graph Report - /Users/vijaykumarbk/Desktop/MAIN EL 2026  (2026-05-09)

## Corpus Check
- Corpus is ~37,520 words - fits in a single context window. You may not need a graph.

## Summary
- 560 nodes · 1129 edges · 24 communities detected
- Extraction: 72% EXTRACTED · 28% INFERRED · 0% AMBIGUOUS · INFERRED: 316 edges (avg confidence: 0.56)
- Token cost: 25,000 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Backend Core & AI|Backend Core & AI]]
- [[_COMMUNITY_Frontend & UI|Frontend & UI]]
- [[_COMMUNITY_Disaster News Ingestion|Disaster News Ingestion]]
- [[_COMMUNITY_Hospital Network & Routing|Hospital Network & Routing]]
- [[_COMMUNITY_GDELT Ingestion & Tests|GDELT Ingestion & Tests]]
- [[_COMMUNITY_API Endpoints & Seeding|API Endpoints & Seeding]]
- [[_COMMUNITY_Company Intelligence|Company Intelligence]]
- [[_COMMUNITY_Supply Chain Monitor|Supply Chain Monitor]]
- [[_COMMUNITY_External Data Clients|External Data Clients]]
- [[_COMMUNITY_Named Entity Recognition|Named Entity Recognition]]
- [[_COMMUNITY_Correlation Engine|Correlation Engine]]
- [[_COMMUNITY_Graph Seeding|Graph Seeding]]
- [[_COMMUNITY_Disaster Alert Generation|Disaster Alert Generation]]
- [[_COMMUNITY_Event Classification|Event Classification]]
- [[_COMMUNITY_Text Preprocessing|Text Preprocessing]]
- [[_COMMUNITY_Weather API|Weather API]]
- [[_COMMUNITY_Hospital Data Gen|Hospital Data Gen]]
- [[_COMMUNITY_Fast Seed|Fast Seed]]
- [[_COMMUNITY_API Key Testing|API Key Testing]]
- [[_COMMUNITY_Model Downloads|Model Downloads]]
- [[_COMMUNITY_Monitoring Init|Monitoring Init]]
- [[_COMMUNITY_Relief Init|Relief Init]]
- [[_COMMUNITY_GDELT Init|GDELT Init]]
- [[_COMMUNITY_Hospital Network Misc|Hospital Network Misc]]

## God Nodes (most connected - your core abstractions)
1. `SupplyChainMonitor` - 71 edges
2. `SupplyChainNetwork` - 61 edges
3. `CompanyIntelligenceService` - 52 edges
4. `RiskSimulator` - 52 edges
5. `Neo4jClient` - 45 edges
6. `AIAdvisor` - 38 edges
7. `HospitalNetworkService` - 32 edges
8. `SimulateRequest` - 30 edges
9. `FeedbackRequest` - 27 edges
10. `ReliefRoute Karnataka` - 21 edges

## Surprising Connections (you probably didn't know these)
- `Frontend AI Studio App Documentation` --semantically_similar_to--> `Frontend Docker Service`  [INFERRED] [semantically similar]
  frontend/README.md → docker-compose.yml
- `Build a connected Karnataka hospital route graph.  Hospitals are connected to th` --uses--> `HospitalNetworkService`  [INFERRED]
  scripts/build_hospital_graph.py → src/relief/hospital_network.py
- `main()` --calls--> `Neo4jClient`  [INFERRED]
  fast_seed.py → src/graph/neo4j_client.py
- `TestSimulateRequestValidation` --uses--> `SupplyChainNetwork`  [INFERRED]
  tests/test_atlas_fixes.py → src/prediction/network_model.py
- `TestSimulateRequestValidation` --uses--> `RiskSimulator`  [INFERRED]
  tests/test_atlas_fixes.py → src/prediction/monte_carlo.py

## Hyperedges (group relationships)
- **Backend Tech Stack** — fastapi, pydantic, networkx, neo4j [EXTRACTED 1.00]
- **Frontend Tech Stack** — react, typescript, vite, leaflet, recharts [EXTRACTED 1.00]
- **Docker Services Architecture** — neo4j_service, backend_service, frontend_service [EXTRACTED 1.00]

## Communities

### Community 0 - "Backend Core & AI"
Cohesion: 0.05
Nodes (65): AIAdvisor, Ollama AI Client for generating insights and recommendations., Store user feedback (+1 / -1) on AI recommendations to track strategy efficacy., Ensure local feedback storage exists., Generate human-readable insights based on disruption data and simulation., Ask Ollama for concise alternate route guidance for hospital transfers., ai_route_analysis(), AIRouteAnalysisRequest (+57 more)

### Community 1 - "Frontend & UI"
Cohesion: 0.03
Nodes (33): Alternate Route Suggestion, ATLAS_MODE Configuration, ATLAS_MODE Demo, ATLAS_MODE Live, Backend Docker Service, Cascading Impact Analysis, Disaster Relief Logistics, Docker Compose Configuration (+25 more)

### Community 2 - "Disaster News Ingestion"
Cohesion: 0.12
Nodes (50): _alert_from_feed_item(), _bing_news_rss_alerts(), _canonical_url(), _category(), _chunks(), collect_live_disasters(), _configured_json_feed_alerts(), _dedupe_alerts() (+42 more)

### Community 3 - "Hospital Network & Routing"
Cohesion: 0.07
Nodes (20): _estimate_travel_time(), haversine_distance(), HospitalNetworkService, Hospital network service for Karnataka emergency supply routing.  The service ow, Build a connected graph using nearest neighbors plus component bridges., Reload alerts and recalculate route impacts., Apply active disaster alerts to a fresh copy of the base graph., Hospital network operations and route optimization. (+12 more)

### Community 4 - "GDELT Ingestion & Tests"
Cohesion: 0.08
Nodes (19): FeedbackRequest, SimulateRequest, GDELTClient, _is_safe_path(), Client for fetching data from the GDELT Project., Fetches the latest events from GDELT 2.0 API, downloads the zip, and extracts th, ATLAS AI — Backend Test Suite Fix #14 & #15: Pytest coverage for critical code p, Test the path traversal protection in GDELT client. (+11 more)

### Community 5 - "API Endpoints & Seeding"
Cohesion: 0.06
Nodes (29): current_mode(), get_dashboard_metrics(), get_events(), get_graph_nodes(), get_hospital(), get_live_disasters(), get_mode(), get_neo4j_client() (+21 more)

### Community 6 - "Company Intelligence"
Cohesion: 0.1
Nodes (18): CompanyIntelligenceService, _normalize(), Searches, enriches, and imports live company metadata from free public sources., load_company_names(), load_company_rows(), main(), parse_company_names(), ATLAS AI — Bulk Live Company Importer  Imports a newline- or comma-separated lis (+10 more)

### Community 7 - "Supply Chain Monitor"
Cohesion: 0.11
Nodes (6): _clean_key(), _dedupe_preserve(), _norm_lookup(), _normalize_text(), _slug(), _utc_now()

### Community 8 - "External Data Clients"
Cohesion: 0.14
Nodes (9): _format_address(), GLEIFClient, _nested_name(), _normalize(), Client for searching and retrieving live company records from the GLEIF API., _normalize(), _pad_cik(), Client for public-company metadata and filing data from the SEC. (+1 more)

### Community 9 - "Named Entity Recognition"
Cohesion: 0.22
Nodes (5): EntityExtractor, Parses the text and returns arrays of Geographical (GPE, LOC) and Organizational, Extracts Named Entities (NER) using spaCy for downstream Graph Node linking., Stub function for Phase 2: Formats extracted raw entities into standardized, Initialize the spaCy NLP pipeline.

### Community 10 - "Correlation Engine"
Cohesion: 0.25
Nodes (4): CorrelationEngine, Calculate severity score for an event based on category, keywords, and context., Find supply chain routes and nodes correlated geographically to a location., Engine for assigning severity scores and correlating events geographically.

### Community 11 - "Graph Seeding"
Cohesion: 0.57
Nodes (6): _company_node(), import_routes(), _location_node(), main(), _slug(), _unique()

### Community 12 - "Disaster Alert Generation"
Cohesion: 0.33
Nodes (4): generate_description(), generate_disaster_alerts(), Generate Disaster Alerts for Karnataka, Generate a realistic disaster description

### Community 13 - "Event Classification"
Cohesion: 0.29
Nodes (4): EventClassifier, Initialize the HuggingFace zero-shot classification pipeline., Classifies the text against the candidate labels.         Returns the top label, Classifies unstructured text into supply chain event categories using zero-shot

### Community 14 - "Text Preprocessing"
Cohesion: 0.29
Nodes (4): Cleans the input string by:         - Lowercasing         - Removing punctuation, Preprocesses text for NLP and classification tasks., Initialize the spaCy NLP pipeline., TextPreprocessor

### Community 15 - "Weather API"
Cohesion: 0.33
Nodes (3): Client for fetching data from OpenWeatherMap., Fetches the weather for a specific lat/lon coordinate., WeatherClient

### Community 16 - "Hospital Data Gen"
Cohesion: 0.5
Nodes (3): generate_hospitals(), generate_phone(), Generate fake Karnataka Hospital Dataset

### Community 17 - "Fast Seed"
Cohesion: 1.0
Nodes (2): hardcoded_geocodes(), main()

### Community 18 - "API Key Testing"
Cohesion: 0.67
Nodes (2): Test OpenWeatherMap API key validity.     Fix #13: null-check key before slicing, test_weather_key()

### Community 19 - "Model Downloads"
Cohesion: 0.67
Nodes (2): download_spacy_models(), Downloads the necessary spaCy models.

### Community 23 - "Monitoring Init"
Cohesion: 1.0
Nodes (1): Supply-chain upload monitoring utilities.

### Community 24 - "Relief Init"
Cohesion: 1.0
Nodes (1): ReliefRoute Karnataka domain helpers.

### Community 30 - "GDELT Init"
Cohesion: 1.0
Nodes (1): Fix #4: Validate that a zip member path stays within the target directory (preve

### Community 35 - "Hospital Network Misc"
Cohesion: 1.0
Nodes (1): Calculate distance in km between two coordinates.

## Knowledge Gaps
- **69 isolated node(s):** `Test OpenWeatherMap API key validity.     Fix #13: null-check key before slicing`, `Downloads the necessary spaCy models.`, `Generate Disaster Alerts for Karnataka`, `Generate a realistic disaster description`, `Generate fake Karnataka Hospital Dataset` (+64 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Fast Seed`** (3 nodes): `fast_seed.py`, `hardcoded_geocodes()`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API Key Testing`** (3 nodes): `test_key.py`, `Test OpenWeatherMap API key validity.     Fix #13: null-check key before slicing`, `test_weather_key()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Model Downloads`** (3 nodes): `download_spacy_models()`, `download_models.py`, `Downloads the necessary spaCy models.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Monitoring Init`** (2 nodes): `Supply-chain upload monitoring utilities.`, `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Relief Init`** (2 nodes): `ReliefRoute Karnataka domain helpers.`, `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `GDELT Init`** (1 nodes): `Fix #4: Validate that a zip member path stays within the target directory (preve`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Hospital Network Misc`** (1 nodes): `Calculate distance in km between two coordinates.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SupplyChainMonitor` connect `Backend Core & AI` to `Graph Seeding`, `GDELT Ingestion & Tests`, `API Endpoints & Seeding`, `Supply Chain Monitor`?**
  _High betweenness centrality (0.188) - this node is a cross-community bridge._
- **Why does `NetworkX` connect `Frontend & UI` to `Hospital Network & Routing`, `Supply Chain Monitor`?**
  _High betweenness centrality (0.186) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `SupplyChainMonitor` (e.g. with `ATLAS AI — Real Supply Chain Graph Importer  Imports a user-provided CSV or JSON` and `SimulateRequest`) actually correct?**
  _`SupplyChainMonitor` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `SupplyChainNetwork` (e.g. with `TestSimulateRequestValidation` and `TestFeedbackRequestValidation`) actually correct?**
  _`SupplyChainNetwork` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 38 inferred relationships involving `CompanyIntelligenceService` (e.g. with `FakeGLEIFClient` and `FakeSECClient`) actually correct?**
  _`CompanyIntelligenceService` has 38 INFERRED edges - model-reasoned connections that need verification._
- **Are the 48 inferred relationships involving `RiskSimulator` (e.g. with `TestSimulateRequestValidation` and `TestFeedbackRequestValidation`) actually correct?**
  _`RiskSimulator` has 48 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `Neo4jClient` (e.g. with `ATLAS AI — Bulk Live Company Importer  Imports a newline- or comma-separated lis` and `ATLAS AI — Real Supply Chain Graph Importer  Imports a user-provided CSV or JSON`) actually correct?**
  _`Neo4jClient` has 35 INFERRED edges - model-reasoned connections that need verification._