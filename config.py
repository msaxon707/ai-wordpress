"""
config.py — Environment configuration for The Saxon Blog AutoPublisher
Compatible with Coolify environment variables and OpenAI >= 1.0
"""

import os

# === 🔐 Environment Variables (Loaded from Coolify) ===

# OpenAI Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# WordPress Connection
WP_BASE_URL = os.getenv("WP_BASE_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

# Affiliate & Media APIs
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
AMAZON_ASSOCIATE_TAG = os.getenv("AMAZON_ASSOCIATE_TAG", "yourtag-20")

# === ⚙️ AI Behavior & System Settings ===

# Temperature: Controls creativity for topic generation (0.7 = balanced)
TOPIC_TEMPERATURE = float(os.getenv("TOPIC_TEMPERATURE", 0.7))

# Posting interval (in seconds) — 1 hour = 3600
POST_INTERVAL_SECONDS = int(os.getenv("POST_INTERVAL_SECONDS", 3600))

# Storage paths
DATA_DIR = "/app/data"
IMAGE_DIR = "/app/images"

# === 🧠 Additional Behavior Flags ===
# These are optional toggles that you can set in Coolify environment variables

# Test Mode — if True, the script generates but does not post to WordPress
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# Debug Logging — enable to get more detailed console output
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# === ✅ Environment Summary (for log clarity) ===
print("[config] Environment loaded successfully. Running on Coolify mode.")
if TEST_MODE:
    print("[config] ⚠️ TEST MODE is active — posts will not be published.")
