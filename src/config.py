import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# ─── Environment Mode ─────────────────────────────────────────────────────────
ATLAS_ENV = os.getenv("ATLAS_ENV", "development")
ATLAS_MODE = os.getenv("ATLAS_MODE", "live").strip().lower()
if ATLAS_MODE not in {"live", "demo"}:
    logger.warning("Invalid ATLAS_MODE=%s. Falling back to live mode.", ATLAS_MODE)
    ATLAS_MODE = "live"

# OpenWeatherMap API Key
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
NOMINATIM_USER_AGENT = os.getenv("NOMINATIM_USER_AGENT", "reliefroute-karnataka/1.0")
SEC_API_USER_AGENT = os.getenv(
    "SEC_API_USER_AGENT",
    "reliefroute-karnataka/1.0 (disaster-relief-logistics; admin@localhost)"
)

# ─── Neo4j Database Settings (Fix #3: no insecure fallback in production) ────
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")

_neo4j_password = os.getenv("NEO4J_PASSWORD")
if not _neo4j_password and ATLAS_ENV != "development":
    logger.critical("NEO4J_PASSWORD is not set. Required in non-development environments.")
    raise EnvironmentError("NEO4J_PASSWORD must be set via environment variable in production.")
NEO4J_PASSWORD = _neo4j_password or "password"  # Fallback only in dev mode

# ─── CORS Settings (Fix #3) ──────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
)

# Ollama Setting
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")  # Lightweight model optimized for M2 Air

# Data Directories
RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")

# Ensure the raw data directory exists
os.makedirs(RAW_DATA_DIR, exist_ok=True)
