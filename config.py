# config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """
    Central configuration for AI WordPress automation.
    Pulls all keys from .env or environment variables on your Coolify server.
    """

    # --- OpenAI Configuration ---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # --- WordPress Configuration ---
    WP_BASE_URL = os.getenv("WP_BASE_URL", "https://thesaxonblog.com")
    WP_USERNAME = os.getenv("WP_USERNAME", "")
    WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")

    # --- Affiliate Config ---
    AMAZON_TAG = os.getenv("AMAZON_TAG", "affiliatecode-20")

    # --- Optional: External Image APIs (if fallback needed) ---
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

    # --- Logging & Directory Settings ---
    LOG_DIR = os.getenv("LOG_DIR", "./logs")
    DATA_DIR = os.getenv("DATA_DIR", "./data")

    @classmethod
    def ensure_directories(cls):
        """Ensure required folders exist."""
        os.makedirs(cls.LOG_DIR, exist_ok=True)
        os.makedirs(cls.DATA_DIR, exist_ok=True)