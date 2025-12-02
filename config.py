\import os
from dotenv import load_dotenv

# Load environment variables (Coolify or local)
load_dotenv()

# === OPENAI SETTINGS ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TOPIC_TEMPERATURE = float(os.getenv("TOPIC_TEMPERATURE", 0.7))

# === WORDPRESS SETTINGS ===
# Make sure these are defined in Coolify’s environment tab:
WP_BASE_URL = os.getenv("WP_BASE_URL", "https://thesaxonblog.com")
WP_API_URL = f"{WP_BASE_URL}/wp-json/wp/v2"
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

# === AMAZON AFFILIATE SETTINGS ===
AMAZON_TAG = os.getenv("AMAZON_TAG", "thesaxonblog01-20")

# === IMAGE GENERATION SETTINGS ===
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gpt-image-1")

# === GENERAL BEHAVIOR SETTINGS ===
COOLIFY_MODE = os.getenv("COOLIFY_MODE", "true").lower() == "true"
POST_INTERVAL_HOURS = float(os.getenv("POST_INTERVAL_HOURS", 1.0))
MAX_TOPICS = int(os.getenv("MAX_TOPICS", 50))

print("[config] Environment loaded successfully. Running on Coolify mode." if COOLIFY_MODE else "[config] Local environment loaded.")
