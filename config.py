# =======================================
# ai-wordpress Configuration (Final Build)
# =======================================

import os

# --- Helper: Normalize WordPress URL ---
def _norm_base_url(url: str) -> str:
    """Ensure no trailing slash in base URL."""
    return url.rstrip("/")

# --- API KEYS (keep private) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-proj-xxxx")       # your OpenAI key
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "JLoA2xxxx")
WP_BASE_URL = _norm_base_url(os.getenv("WP_BASE_URL", "https://thesaxonblog.com"))
WP_USERNAME = os.getenv("WP_USERNAME", "megansaxon9@gmail.com")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "ligxxxxxx")

# --- General Settings ---
RUN_MODE = "once"   # safe for cron-based runs
POST_CACHE_FILE = "posted_titles.json"
MAX_PARAGRAPHS = 8
AFFILIATE_LINK_FREQUENCY = 3  # every 2–3 paragraphs

# --- Affiliate Settings ---
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

# --- Helper Print for Verification (optional) ---
if __name__ == "__main__":
    print(f"✅ Config loaded for: {WP_BASE_URL}")
