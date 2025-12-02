import os
from dotenv import load_dotenv

# Load env automatically (Coolify or local)
load_dotenv()

# --- OPENAI CONFIG ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TOPIC_TEMPERATURE = float(os.getenv("TOPIC_TEMPERATURE", 0.7))

# --- WORDPRESS CONFIG ---
WP_BASE_URL = os.getenv("WP_BASE_URL", "https://thesaxonblog.com")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

# --- AFFILIATE CONFIG ---
AMAZON_TAG = os.getenv("AMAZON_TAG", "thesaxonblog-20")

# --- GENERAL SETTINGS ---
POST_INTERVAL_HOURS = int(os.getenv("POST_INTERVAL_HOURS", 1))
DATA_DIR = os.getenv("DATA_DIR", "/app/data")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)

print("[config] Environment loaded successfully. Running on Coolify mode.")
