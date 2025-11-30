"""
config.py — Centralized environment configuration for AI WordPress autoposter.
Compatible with Coolify (no .env file required).
"""

import os

# === OPENAI CONFIG ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# === AMAZON AFFILIATE CONFIG ===
# Amazon tag should be set in Coolify as: AMAZON_TAG=thesaxonblog01-20
AMAZON_TAG = os.getenv("AMAZON_TAG", "thesaxonblog01-20")

# === WORDPRESS CONFIG ===
WP_BASE_URL = os.getenv("WP_BASE_URL", "https://thesaxonblog.com")
WP_USERNAME = os.getenv("WP_USERNAME", "megansaxon9@gmail.com")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

# === SYSTEM CONFIG ===
POST_INTERVAL_HOURS = int(os.getenv("POST_INTERVAL_HOURS", 1))  # one post per hour
MAX_TOPIC_HISTORY = 200  # prevent repeats
IMAGE_STYLE = os.getenv("IMAGE_STYLE", "rustic country photography, natural lighting")

# === SANITY CHECK ===
if not all([OPENAI_API_KEY, WP_APP_PASSWORD]):
    raise EnvironmentError("❌ Missing critical environment variables. Please check Coolify settings.")

print("[config] Environment loaded successfully. Running on Coolify mode.")
