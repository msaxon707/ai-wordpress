import os
import sys

# === OpenAI Settings ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# === WordPress Settings ===
WP_BASE_URL = os.getenv("WP_BASE_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

# === Image API Keys ===
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# === Validation ===
missing = []
if not OPENAI_API_KEY:
    missing.append("OPENAI_API_KEY")
if not WP_BASE_URL:
    missing.append("WP_BASE_URL")
if not WP_USERNAME:
    missing.append("WP_USERNAME")
if not WP_APP_PASSWORD:
    missing.append("WP_APP_PASSWORD")

if missing:
    print(f"[config] ❌ Missing environment variables: {', '.join(missing)}")
    sys.exit(1)

print("[config] ✅ Environment variables loaded successfully.")
