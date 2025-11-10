import os

# 🔑 API Keys and Site Info
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
WP_URL = os.getenv("WP_URL")  # e.g. https://thesaxonblog.com/wp-json/wp/v2/posts
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")

# 🧩 General Settings
MODEL = "gpt-3.5-turbo"
INTERVAL_MINUTES = 180  # Every 3 hours
SITE_BASE = "https://thesaxonblog.com"
AFFILIATE_TAG = "meganmcanespy-20"

# 📂 WordPress Categories
CATEGORIES = {
    "dogs": 11,
    "deer-season": 36,
    "hunting": 38,
    "recipes": 54,
    "fishing": 91,
    "outdoor-living": 90,
    "survival-bushcraft": 92,
}

# 🎯 Topics Pool (auto-post rotation)
TOPIC_POOL = [
    {"category": "recipes", "topic": "Smoked duck breast at home"},
    {"category": "dogs", "topic": "Training your GSP for hunting season"},
    {"category": "hunting", "topic": "Best early-season deer tactics"},
    {"category": "fishing", "topic": "Bank fishing gear every angler needs"},
    {"category": "outdoor-living", "topic": "Top camping cookware for families"},
    {"category": "survival-bushcraft", "topic": "How to start a fire in wet weather"},
]
