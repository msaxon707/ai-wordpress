import os
from dotenv import load_dotenv

# Load from environment automatically in Coolify
load_dotenv()

# ========== OPENAI CONFIG ==========
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Default if not set
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

# ========== WORDPRESS CONFIG ==========
WP_BASE_URL = os.getenv("WP_BASE_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

# derived WordPress API endpoint
WP_API_URL = f"{WP_BASE_URL}/wp-json/wp/v2"

# ========== IMAGE / AFFILIATE ==========
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# Amazon affiliate defaults
AMAZON_TAG = os.getenv("AMAZON_TAG", "megansaxon9-20")

# ========== GENERAL ==========
POST_INTERVAL_HOURS = int(os.getenv("POST_INTERVAL_HOURS", "1"))
TOPIC_TEMPERATURE = float(os.getenv("TOPIC_TEMPERATURE", "0.7"))

# Mode
IS_COOLIFY = True
print("[config] Environment loaded successfully. Running on Coolify mode.")
