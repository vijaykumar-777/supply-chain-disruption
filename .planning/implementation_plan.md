# Implement ATLAS AI V2 Roadmap

This plan covers the implementation of `FUTURE_PLANNING_V2.md` and rectification of identified technical debt. Due to the scale of the roadmap (4 Phases), I propose we execute this in logical batches, starting with Phase 1 and the critical bug fixes.

## User Review Required

> [!WARNING]
> Implementing the entire roadmap at once is a massive set of changes. To ensure stability and allow for testing, I recommend executing **Technical Debt Fixes + Phase 1 (Frontend Workflows)** first, verifying, and then proceeding to subsequent phases. Do you agree to this phased execution, or would you prefer I attempt to implement everything in one massive run?

## Proposed Changes: Step 1 (Tech Debt + Phase 1)

### Tech Debt & Quick Wins

#### [MODIFY] src/config.py and src/ingestion/weather_client.py
- Normalize the `OPENWEATHERMAP_API_KEY` environment variable so both files use the same name, fixing the silent mismatch.

#### [MODIFY] src/api/main.py
- Expand `GET /api/graph/nodes`. Instantiate the graph network and call `sc_network.calculate_resilience_score(node_id)` to include `resilience_score` in the node payload.
- Expand `GET /api/events` to accept optional query parameters for filtering (needed for Live Feed styling and eventual pagination).

### Phase 1: Frontend Completion

#### [NEW] frontend/src/components/ai/AIAssistantView.tsx
- Build the multi-step AI workflow using existing `useSimulation` and a new `useRecommendation` hook.
- **Workflow Steps:**
  1. Select Event (from live events)
  2. Define Route (source, target nodes)
  3. Run Simulation (displays stats like p50, mean delay)
  4. Get AI AI Recommendation (displays Ollama response)
  5. Submit Feedback rating.

#### [NEW] frontend/src/components/feed/LiveFeedView.tsx
- Build a dedicated, full-page event feed component using the `useEvents` hook.
- Implement client-side filtering for category, severity, and text search to allow logistics operators to sift through disruptions.

#### [NEW] frontend/src/components/analytics/AnalyticsView.tsx
- Build the Analytics layout shell to replace the placeholder.
- Add live charts (e.g., category breakdown pie chart, top severity bar chart) using the live events array.

#### [MODIFY] frontend/src/hooks/useAtlasData.ts
- Expand with a `useRecommendation` and `useFeedback` hook to complement the existing `useSimulation` hook.

#### [MODIFY] frontend/src/App.tsx
- Import the new `AIAssistantView`, `LiveFeedView`, and `AnalyticsView` components.
- Replace the inline placeholder `<div>` components.

## Proposed Changes: Step 2 (Data Foundation - Phase 2)

*(To be executed after Phase 1 is confirmed working)*
- Add SQLite persistence to capture events historically (`event_store.py`).
- Create `/api/analytics` endpoints to hit the SQLite store for trend graphs.
- Plumb `WeatherScorer` fully into the `/api/metrics` and risk calculation logic.
- Add `/api/search` endpoints.

## Open Questions

1. **Execution Scope:** Shall I begin by executing just **Tech Debt + Phase 1** (Frontend Views)?
2. **Design Language:** I will use Tailwind classes matching the project's existing glassmorphic theme. Are there any specific UI libraries you want me to introduce, or stick to raw React + Tailwind?

## Verification Plan

### Automated Tests
- Ensure the backend REST API doesn't regress.

### Manual Verification
- Start the frontend `npm run dev` and navigate through the new screens: Live Feed, Analytics, and AI Assistant.
