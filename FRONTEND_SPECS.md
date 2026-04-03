# ATLAS AI: Frontend Specification & UI Requirements

This document outlines the frontend goals, tech stack, and component requirements for the **ATLAS AI Supply Chain Resilience Dashboard**.

## 🎨 Design Vision
*   **Aesthetic:** "Glassmorphism" meets "Dark Mode Strategy." High-contrast data visualization on a deep charcoal/navy background.
*   **Theme:** Industrial, high-tech, and real-time. Use vibrant "status" colors (Success Emerald, Warning Amber, Critical Crimson).
*   **Typography:** Modern sans-serif (e.g., Inter or Roboto) for high readability in data-dense areas.

---

## 🛠 Tech Stack
*   **Framework:** React (Vite-based for speed).
*   **Styling:** Vanilla CSS (for performance and low overhead) or Tailwind (if requested).
*   **Mapping:** Leaflet.js (Open-source mapping engine) - NO Google Maps API to maintain zero-cost constraint.
*   **Charts:** Recharts or Chart.js for supply chain trend analysis.
*   **Icons:** Lucide-React or FontAwesome (Free tier).

---

## 🏗 Key Pages & Modules

### 1. The Global Resilience Map (Primary View)
*   **Map Layer:** Interactive world map using OpenStreetMap tiles.
*   **Dynamic Markers:** 
    *   Pulsing red dots for active "Critical" disruptions.
    *   Blue dots for standard supply chain nodes (Ports, Hubs).
*   **Popups:** On-click details showing:
    *   Event Type (e.g., Strike, Hurricane).
    *   Confidence Score from NLP (e.g., "94% Accuracy").
    *   Impact assessment summary.

### 2. Real-Time "Live Feed" Sidebar
*   **Ingestion Feed:** Chronological list of processed GDELT news events.
*   **Filtering:** Filter by event type (Disaster, Strike, Bankruptcy).
*   **Search:** Natural language search bar integrated with backend.

### 3. Supply Chain Impact Analysis (Modal/Detail View)
*   **Graph Visualization:** A mini-view of the Neo4j relationships (e.g., "Port of LA" -> "Blocked" -> "Retailer X").
*   **Weather Overlay:** Layer showing current weather patterns at specific port locations via OpenWeatherMap.

### 4. AI Recommendation Panel (Phase 4 Integration)
*   **Chat Interface:** Floating widget to interact with our local LLM (Ollama).
*   **Predictive Log:** High-level summary of "Predicted Disruptions in next 48h."

---

## 📊 Component Requirements

| Component | Description | Data Dependency |
| :--- | :--- | :--- |
| **Status Cards** | Top-row metrics (Total Active Events, High Risk Nodes, Weather Alerts). | Backend `/metrics` |
| **Disruption Map** | Interactive Leaflet map with geo-clustered markers. | Backend `/events` (Geo-JSON) |
| **Trend Chart** | Logistics delay vs Time line graph. | NLP Extracted timestamps |
| **Audit Logs** | Table view of all raw news ingested today for transparency. | GDELT Raw Ingestion |

---

## ⚡ Functional Requirements (UX)
1.  **Zero-Latency Feel:** Use skeleton loaders while NLP classification is running.
2.  **Responsive Design:** Mobile-friendly view for "on-the-go" logistics monitoring.
3.  **Local Offline Capability:** Frontend should warn if local backend (Ollama/Neo4j) is unreachable.
4.  **Export Data:** Single button to export filtered event data to CSV.

---

## 📅 Frontend Roadmap (Estimated)
*   **Phase 2:** Base setup, Mapping integration, and Mock data connection.
*   **Phase 3:** Real-time data binding with Classifier output.
*   **Phase 4:** AI Chat integration for resilience recommendations.
