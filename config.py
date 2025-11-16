# ==========================
# ai-wordpress Configuration
# ==========================

class Settings:
    # WordPress
    WP_BASE_URL: str = _norm_base_url(os.getenv("WP_BASE_URL", ""))
    WP_USERNAME: str = os.getenv("WP_USERNAME", "")
    WP_APP_PASSWORD: str = os.getenv("WP_APP_PASSWORD", "")

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

# --- General Settings ---
RUN_MODE = "once"   # 'once' for cron-based runs
POST_CACHE_FILE = "posted_titles.json"
MAX_PARAGRAPHS = 8
AFFILIATE_LINK_FREQUENCY = 3  # every 2–3 paragraphs

# --- Affiliate ---
AMAZON_TAG = "thesaxonblog01-20"

# --- Category Mapping ---
CATEGORY_IDS = {
    "dogs": 11,
    "fishing": 91,
    "hunting": 38,
    "outdoor_gear": 90,
    "recipes": 54,
    "camping": 92,
    "deer_season": 96,
    "uncategorized": 1,
}

# --- Keywords for Category Detection ---
CATEGORY_KEYWORDS = {
    "dogs": ["dog", "retriever", "hound", "kennel"],
    "fishing": ["fish", "angler", "rod", "bait", "lake", "bass"],
    "hunting": ["hunt", "rifle", "bow", "deer", "turkey", "duck"],
    "outdoor_gear": ["gear", "knife", "flashlight", "jacket", "tent"],
    "recipes": ["recipe", "cook", "grill", "venison", "smoke", "barbecue"],
    "camping": ["camp", "hike", "trail", "fire", "tent", "backpack"],
    "deer_season": ["deer", "buck", "rut", "doe"],
}

# --- WordPress Posting ---
WP_TIMEOUT = 30  # seconds for requests
MAX_RETRIES = 3

# --- Logging ---
ENABLE_LOGGING = True
LOG_FILE = "ai_wordpress.log"
