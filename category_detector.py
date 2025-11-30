"""
category_detector.py — Assigns categories and tags automatically based on article content.
"""

import re

CATEGORY_MAP = {
    "Hunting Tips & Tactics": ["deer", "turkey", "rut", "trail", "bow", "rifle"],
    "Hunting Gear & Guns": ["optics", "scope", "gun", "ammo", "camo", "backpack"],
    "Hunting Dogs & Training": ["dog", "hound", "kennel", "training"],
    "Fishing & Lakes": ["fish", "bass", "catfish", "lure", "boat", "lake"],
    "Camping & Outdoor Adventures": ["camp", "tent", "stove", "lantern", "fire"],
    "Country Recipes & Cooking": ["recipe", "venison", "cast iron", "cooking", "grill"],
    "Country Home Decor & Lifestyle": ["decor", "farmhouse", "rustic", "home", "bedding"],
    "Clothing, Boots & Camo": ["boots", "clothing", "jacket", "carhartt"],
    "Tools & Outdoor Equipment": ["tool", "chainsaw", "knife", "gear"],
    "Gifts & Holiday Ideas": ["gift", "Christmas", "Father’s Day", "holiday"],
    "Scouting & Trailing Deer": ["scout", "camera", "trail", "deer"],
    "Nature & Country Living": ["garden", "nature", "homestead", "yard", "land"]
}


def detect_category(article_text):
    """Detect best-fit category based on keyword mapping."""
    lower_text = article_text.lower()
    for category, keywords in CATEGORY_MAP.items():
        if any(re.search(rf"\\b{k}\\b", lower_text) for k in keywords):
            return category
    return "Nature & Country Living"
