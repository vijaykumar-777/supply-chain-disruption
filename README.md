# 🧠 ATLAS AI — Real-time Supply Chain Intelligence

ATLAS AI is a state-of-the-art, AI-powered supply chain monitoring and prediction platform. It leverages graph intelligence, natural language processing (NLP), and Monte Carlo simulations to provide real-time visibility into global supply chain disruptions and offer actionable strategic recommendations.

---

## 🚀 Core Features

- **Real-time Event Monitoring:** Continuous ingestion of global events via GDELT and weather data from OpenWeatherMap.
- **Graph Database Intelligence:** A high-performance Neo4j backend mapping relationships between companies, suppliers, locations, and logistics routes.
- **Predictive Risk Modeling:** Monte Carlo simulation engine to estimate lead-time delays and ripple effect impacts across the network.
- **AI-Driven Strategic Recommendations:** Integration with local LLMs (via Ollama) to provide context-aware mitigation strategies for identified disruptions.
- **Interactive Global Dashboard:** A premium React-based dashboard featuring interactive maps (Leaflet), real-time alert feeds, and complex network visualizations.

---

## 🏗 System Architecture

The project follows a modular, full-stack architecture designed for performance and scalability:

### 1. Frontend (React + TypeScript + Vite)
- **Styling:** Tailwind CSS with a premium dark-mode aesthetic.
- **Mapping:** Leaflet.js for geographic visualization.
- **Animations:** Framer Motion for smooth UI transitions and micro-animations.
- **State Management:** React Hooks and Context API.

### 2. Backend (FastAPI + Python)
- **API Engine:** FastAPI provides high-speed asynchronous endpoints for the frontend.
- **NLP Layer:** spaCy and HuggingFace Transformers for entity extraction (NER) and event classification.
- **Graph Layer:** Custom Neo4j client for managing complex supply chain relationships.
- **Simulation Engine:** NumPy and NetworkX for pathfinding and risk simulations.

### 3. Intelligence Layers
- **Knowledge Graph:** Neo4j Community Edition.
- **Local AI:** Ollama running LLaMA 3.2 for privacy-preserving, zero-cost strategic insights.
- **Data Ingestion:** Automated pipelines for GDELT (Global Database of Events, Language, and Tone) and OpenWeather.

---

## 🛠 Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Leaflet, Recharts, Lucide Icons |
| **Backend** | Python 3.14+, FastAPI, Uvicorn, Pydantic |
| **Database** | Neo4j (Graph), SQLite/JSON (Local Storage) |
| **AI/ML** | Ollama (LLaMA 3.2), spaCy, Transformers (DistilBERT), PyTorch |
| **Analysis** | NetworkX, NumPy, Pandas |

---

## 📋 Prerequisites

Ensure you have the following installed and running:

1.  **Python 3.10+**
2.  **Node.js 18+**
3.  **Neo4j Desktop/Community Edition** (Default: `bolt://localhost:7687`)
4.  **Ollama** (Required for AI recommendations)

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd "MAIN EL 2026"
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
# Edit the .env file with your API keys (OpenWeatherMap)
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

---

## 🏃‍♂️ Running the Application

### 1. Start External Services
- Ensure **Neo4j** is started.
- Ensure **Ollama** is running (`ollama serve`).

### 2. Launch Backend
```bash
# From the root directory
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Launch Frontend
```bash
cd frontend
npm run dev
```
The application will be available at **http://localhost:3000**.

---

## 💾 Data Seeding

To populate the graph with real supply chain routes and company data:

```bash
# Run the fast-seed script (Imports 300 companies and 600 routes)
python3 fast_seed.py
```

To ingest live disruption events:
```bash
# Use the API endpoint via curl
curl -X POST http://localhost:8000/api/ingest/events
```

---

## 📁 Project Structure

```text
.
├── src/
│   ├── ai/           # Ollama / LLM integration logic
│   ├── api/          # FastAPI routes and application entry point
│   ├── graph/        # Neo4j client and graph relationship logic
│   ├── ingestion/    # GDELT, Weather, and Company intelligence services
│   ├── nlp/          # Text cleaning and entity extraction
│   ├── prediction/   # Monte Carlo simulations and NetworkX models
│   └── monitoring/   # Continuous monitoring and alert generation
├── frontend/         # React + Vite + TypeScript application
├── data/             # Sample CSVs and local data storage
├── scripts/          # Maintenance and seeding utilities
└── fast_seed.py      # Automated database initialization script
```

---

## 💰 Design Philosophy

- **Zero-Cost Priority:** Designed to run on free or community-edition tools (Neo4j Community, Ollama, Open-source NLP).
- **Privacy-First:** All AI reasoning is performed locally via Ollama.
- **Resilience:** Built-in fallback mechanisms to demo data when live databases are disconnected.

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
