# config.py
"""
Configuration for topics, categories and tags.

👉 IMPORTANT:
- Update the numeric IDs in CATEGORIES to match your real WordPress category IDs.
- The keys (like "hunting-ducks") should match the `category` fields in TOPIC_POOL.
"""

# Map logical category keys -> WordPress category IDs
# ⚠️ Replace the numbers with the real IDs from your WP admin.
CATEGORIES = {
    "hunting-ducks": 2,          # e.g. "Duck Hunting"
    "hunting-deer": 3,           # e.g. "Deer Hunting"
    "hunting-dogs": 4,           # e.g. "Hunting Dogs"
    "recipes-venison": 5,        # e.g. "Recipes"
    "camping-family": 6,         # e.g. "Camping"
    "photography-outdoors": 7,   # e.g. "Photography"
    "gear-general": 8,           # e.g. "Gear"
}

# Topic pool: each item can have a category key + optional tag words
TOPIC_POOL = [
    {
        "topic": "duck hunting gear",
        "category": "gear-general",
        "tags": ["duck hunting", "hunting gear", "waterfowl"]
    },
    {
        "topic": "best duck decoys 2025",
        "category": "hunting-ducks",
        "tags": ["duck decoys", "duck hunting", "decoy spread"]
    },
    {
        "topic": "deer hunting tips",
        "category": "hunting-deer",
        "tags": ["deer hunting", "rut tactics", "tree stands"]
    },
    {
        "topic": "training German shorthaired pointers",
        "category": "hunting-dogs",
        "tags": ["german shorthaired pointer", "bird dog training"]
    },
    {
        "topic": "how to train a hunting dog",
        "category": "hunting-dogs",
        "tags": ["hunting dog", "obedience", "gun dog"]
    },
    {
        "topic": "homemade venison recipes",
        "category": "recipes-venison",
        "tags": ["venison", "wild game recipes", "cooking"]
    },
    {
        "topic": "family camping essentials",
        "category": "camping-family",
        "tags": ["family camping", "camping checklist", "gear list"]
    },
    {
        "topic": "outdoor photography for beginners",
        "category": "photography-outdoors",
        "tags": ["outdoor photography", "camera settings", "nature photos"]
    },
]
