# ===========================
# CONFIG.PY — TOPICS + CATEGORIES
# ===========================

# WordPress categories (slug → numeric ID)
# Make sure these slugs match your WordPress categories
CATEGORIES = {
    "hunting": 2,
    "dogs": 3,
    "recipes": 4,
    "camping": 5,
    "photography": 6,
    "outdoors": 7,
    "gear": 8,
    "guns": 9,
    "fishing": 10
}

# MASTER TOPIC POOL WITH OPTIONAL MANUAL CATEGORIES
TOPIC_POOL = [
    {"topic": "duck hunting gear", "category": "hunting"},
    {"topic": "best duck decoys 2025", "category": "hunting"},
    {"topic": "deer hunting tips for beginners", "category": "hunting"},
    {"topic": "how to train a hunting dog", "category": "dogs"},
    {"topic": "training German shorthaired pointers", "category": "dogs"},
    {"topic": "homemade venison recipes", "category": "recipes"},
    {"topic": "family camping essentials", "category": "camping"},
    {"topic": "outdoor survival basics", "category": "camping"},
    {"topic": "outdoor photography for beginners", "category": "photography"},
    {"topic": "how to photograph wildlife", "category": "photography"},
    {"topic": "country living tips", "category": "outdoors"},
    {"topic": "best outdoor gear for families", "category": "gear"},
    {"topic": "top hunting boots review", "category": "gear"},
    {"topic": "best pocket knives 2025", "category": "gear"},
    {"topic": "rifle safety basics", "category": "guns"},
    {"topic": "how to clean your rifle", "category": "guns"},
    {"topic": "bass fishing tips", "category": "fishing"},
    {"topic": "catfish rigs and baits", "category": "fishing"},
]

# If a topic doesn't have a category, we assign one automatically:
AUTO_CATEGORY_MAP = {
    "duck": "hunting",
    "deer": "hunting",
    "hunt": "hunting",
    "recipe": "recipes",
    "venison": "recipes",
    "camp": "camping",
    "photo": "photography",
    "dog": "dogs",
    "gsp": "dogs",
    "gear": "gear",
    "knife": "gear",
    "boot": "gear",
    "rifle": "guns",
    "gun": "guns",
    "fish": "fishing",
}