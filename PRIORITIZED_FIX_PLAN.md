# ATLAS AI Prioritized Fix Plan

## Goal
Resolve all identified issues with a risk-first sequence so we stabilize production behavior first, then improve reliability, performance, and maintainability.

## Priority Levels
- `P0` Critical: security/runtime failures or data integrity risks; fix immediately.
- `P1` High: correctness/reliability issues that can mislead users or degrade operations.
- `P2` Medium: performance/quality gaps that impact UX and maintainability.
- `P3` Low: cleanup and long-term engineering hygiene.

## Phase 1 (`P0`) - Immediate Stabilization and Security

### 1) Add missing runtime dependency (`numpy`)
- Issues covered: missing dependency for simulation runtime.
- Files:
  - `requirements.txt`
- Fix:
  - Add `numpy` (prefer pinned/min version strategy for reproducibility).
- Verification:
  - Fresh env install succeeds.
  - `src/prediction/monte_carlo.py` imports without error.

### 2) Validate simulation inputs and prevent crash paths
- Issues covered: `iterations <= 0` crash, invalid node inputs causing 500s.
- Files:
  - `src/api/main.py`
  - `src/prediction/network_model.py`
  - `src/prediction/monte_carlo.py`
- Fix:
  - Enforce `iterations > 0` via Pydantic constraints.
  - Validate `source`/`target` existence before simulation.
  - Catch `NodeNotFound` and return a user-safe 4xx response.
  - Add simulator guard for empty/invalid route stats.
- Verification:
  - API returns 422/400 for invalid inputs (not 500).
  - Valid requests still return simulation output.

### 3) Harden CORS and credential handling
- Issues covered: permissive CORS with credentials, insecure defaults.
- Files:
  - `src/api/main.py`
  - `src/config.py`
- Fix:
  - Replace wildcard CORS with environment-driven allowlist.
  - Keep `allow_credentials=True` only when explicit trusted origins are configured.
  - Remove insecure Neo4j password fallback; require env value in non-dev modes.
- Verification:
  - Preflight and GET succeed for allowed origins.
  - Disallowed origin gets blocked.
  - App startup behavior is explicit for missing secure credentials.

### 4) Secure ZIP extraction in GDELT ingestion
- Issues covered: potential Zip Slip path traversal.
- Files:
  - `src/ingestion/gdelt_client.py`
- Fix:
  - Validate every archive member path stays within target directory before extraction.
  - Skip or fail on unsafe entries.
- Verification:
  - Safe archives extract normally.
  - Malicious traversal entries are blocked.

### 5) Normalize feedback API contract
- Issues covered: backend/frontend rating mismatch and no validation.
- Files:
  - `src/api/main.py`
  - `frontend/src/components/ai/AIAssistantView.tsx`
  - `frontend/src/services/api.ts`
- Fix:
  - Pick one contract and enforce it end-to-end (recommended: `1` helpful, `-1` not helpful).
  - Add request validation to reject invalid rating values.
  - Update frontend button payloads accordingly.
- Verification:
  - Helpful/Not Useful map to valid values.
  - Invalid values return clear 4xx error.

## Phase 2 (`P1`) - Correctness and Operational Reliability

### 6) Pass alternative route into recommendation requests
- Issues covered: AI recommendation missing route context.
- Files:
  - `frontend/src/components/ai/AIAssistantView.tsx`
- Fix:
  - Send `simul.result.alternative_route` to `/api/recommend` instead of `[]`.
- Verification:
  - Backend receives and logs non-empty alt route when available.
  - Recommendation content reflects route alternatives.

### 7) Stop masking feedback storage failures
- Issues covered: false success when persistence fails.
- Files:
  - `src/api/main.py`
  - `src/ai/ollama_client.py`
- Fix:
  - Return `success: false` on storage failure and include error reason.
  - Keep graceful behavior but do not report false positives.
- Verification:
  - Simulated write failure returns `success: false`.
  - Success path remains unchanged.

### 8) Improve Neo4j connection lifecycle and fallback behavior
- Issues covered: repeated failed connection attempts, close-path risk, noisy logs.
- Files:
  - `src/api/main.py`
  - `src/graph/neo4j_client.py`
- Fix:
  - Centralize connection health checks with short TTL caching.
  - Ensure every created client closes on all paths.
  - Reduce repetitive warning spam while DB is unavailable.
- Verification:
  - Fewer repeated connection attempts during outage windows.
  - No leaked sessions/drivers in test runs.

### 9) Standardize resilience score scale
- Issues covered: mixed `0..1` vs `0..100` semantics.
- Files:
  - `src/prediction/network_model.py`
  - `src/api/main.py`
  - `frontend/src/services/api.ts`
- Fix:
  - Choose one canonical range (recommended: `0..1` for APIs).
  - Convert demo and computed values to the same unit.
  - Update UI formatting where displayed.
- Verification:
  - Demo and live data use identical units.
  - API contract documented and consistent.

### 10) Make UI data-source status truthful
- Issues covered: UI saying “Neo4j Live” while on fallback/demo.
- Files:
  - `src/api/main.py`
  - `frontend/src/components/dashboard/DashboardView.tsx`
  - `frontend/src/components/dashboard/GlobalMapView.tsx`
- Fix:
  - Include source metadata in API responses (`live` vs `fallback`).
  - Render accurate labels in dashboard/map views.
- Verification:
  - Disconnecting Neo4j clearly shows fallback state in UI.

## Phase 3 (`P2`) - Performance and Developer Experience

### 11) Reduce frontend bundle size
- Issues covered: large JS chunk warning (~949 KB).
- Files:
  - `frontend/src/App.tsx`
  - `frontend/vite.config.ts`
  - heavy view components (`GlobalMapView`, charts, AI view)
- Fix:
  - Route/view-level lazy loading for non-default panels.
  - Split heavy chart/map dependencies into separate chunks.
  - Rebuild and confirm chunk size improvements.
- Verification:
  - Build warning resolved or materially reduced.
  - Initial load bundle significantly smaller.

### 12) Remove unused deps and align docs/config
- Issues covered: Gemini/Express/dotenv/template drift.
- Files:
  - `frontend/package.json`
  - `frontend/README.md`
  - `frontend/vite.config.ts`
- Fix:
  - Remove unused dependencies and stale `GEMINI_API_KEY` wiring if not used.
  - Update README to ATLAS-specific setup (`VITE_API_URL`, backend URL).
- Verification:
  - `npm install`, `npm run lint`, `npm run build` succeed after cleanup.
  - README matches real run flow.

### 13) Harden weather key test script
- Issues covered: null-slice bug, insecure HTTP.
- Files:
  - `scripts/test_key.py`
- Fix:
  - Null-check key before slicing.
  - Switch to HTTPS and safe request timeout/error handling.
- Verification:
  - Script handles missing key gracefully.
  - Script works for valid/invalid keys without crash.

## Phase 4 (`P3`) - Test Coverage and Regression Prevention

### 14) Add automated backend tests
- Issues covered: lack of repeatable tests.
- Files:
  - `tests/` (new)
  - `src/api/main.py`, prediction modules (covered via tests)
- Fix:
  - Add FastAPI tests for health/events/metrics/simulate/recommend/feedback.
  - Add unit tests for simulation validation and route errors.
  - Add tests for feedback validation and persistence failure behavior.
- Verification:
  - `pytest` suite passes locally and in CI.
  - Core failure cases are covered.

### 15) Add minimal frontend integration checks
- Issues covered: UI contract regressions.
- Files:
  - `frontend/src/**`
  - `frontend` test setup (new)
- Fix:
  - Add smoke/integration tests for AI workflow (select event -> simulate -> recommend -> feedback).
  - Add tests for source status display (live vs fallback).
- Verification:
  - Frontend tests pass and catch contract breakages.

## Recommended Execution Order
1. `P0` items 1-5 (blockers/security/runtime).
2. `P1` items 6-10 (correctness and operational trust).
3. `P2` items 11-13 (performance and maintainability).
4. `P3` items 14-15 (coverage and regression safety).

## Suggested Milestones
- Milestone A (Day 1): Complete all `P0` items and release patch.
- Milestone B (Day 2-3): Complete all `P1` items with API/UI contract updates.
- Milestone C (Day 4): Complete `P2` optimization and docs alignment.
- Milestone D (Day 5): Add tests (`P3`) and finalize CI gate.

## Exit Criteria
- No known `P0` or `P1` issues remain open.
- Build/lint checks pass for backend and frontend.
- Core API flows return deterministic, validated responses.
- UI accurately reflects data source state.
- Test suite exists for critical paths and failure scenarios.
