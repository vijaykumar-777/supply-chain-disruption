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

# ─── Disaster Relief Data Source Placeholders ────────────────────────────────
# Add real API keys/feed URLs in .env when you get access. The app reports these
# sources as unavailable until configured, so simulated data never appears live.
IMD_API_KEY = os.getenv("IMD_API_KEY")
IMD_ALERT_FEED_URL = os.getenv("IMD_ALERT_FEED_URL")

KSNDMC_API_KEY = os.getenv("KSNDMC_API_KEY")
KSNDMC_RAINFALL_FEED_URL = os.getenv("KSNDMC_RAINFALL_FEED_URL")

KSDMA_API_KEY = os.getenv("KSDMA_API_KEY")
KSDMA_BULLETIN_FEED_URL = os.getenv("KSDMA_BULLETIN_FEED_URL")

CWC_API_KEY = os.getenv("CWC_API_KEY")
CWC_FLOODWATCH_FEED_URL = os.getenv("CWC_FLOODWATCH_FEED_URL")

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
NEWSAPI_BASE_URL = os.getenv("NEWSAPI_BASE_URL", "https://newsapi.org/v2/everything")

NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
NEWSDATA_BASE_URL = os.getenv("NEWSDATA_BASE_URL", "https://newsdata.io/api/1/latest")

THENEWSAPI_TOKEN = os.getenv("THENEWSAPI_TOKEN")
THENEWSAPI_BASE_URL = os.getenv("THENEWSAPI_BASE_URL", "https://api.thenewsapi.com/v1/news/all")

MEDIASTACK_API_KEY = os.getenv("MEDIASTACK_API_KEY")
MEDIASTACK_BASE_URL = os.getenv("MEDIASTACK_BASE_URL", "https://api.mediastack.com/v1/news")

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
GNEWS_BASE_URL = os.getenv("GNEWS_BASE_URL", "https://gnews.io/api/v4/search")

WORLDNEWSAPI_KEY = os.getenv("WORLDNEWSAPI_KEY")
WORLDNEWSAPI_BASE_URL = os.getenv("WORLDNEWSAPI_BASE_URL", "https://api.worldnewsapi.com/search-news")

FREENEWSAPI_KEY = os.getenv("FREENEWSAPI_KEY")
FREENEWSAPI_BASE_URL = os.getenv("FREENEWSAPI_BASE_URL", "https://api.freenewsapi.io/v1/news")

GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
GUARDIAN_BASE_URL = os.getenv("GUARDIAN_BASE_URL", "https://content.guardianapis.com/search")

GOOGLE_NEWS_RSS_ENABLED = os.getenv("GOOGLE_NEWS_RSS_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
BING_NEWS_RSS_ENABLED = os.getenv("BING_NEWS_RSS_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
PIB_RSS_URL = os.getenv("PIB_RSS_URL", "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=6")
NEWS_LOOKBACK_DAYS = int(os.getenv("NEWS_LOOKBACK_DAYS", "30"))

OSRM_BASE_URL = os.getenv("OSRM_BASE_URL")
MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY")

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
