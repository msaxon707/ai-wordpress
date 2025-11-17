from config import CATEGORY_IDS

CATEGORY_KEYWORDS = {
    "dogs": ["dog", "training", "retriever", "kennel", "hunting dog"],
    "fishing": ["fish", "fishing", "angler", "bait", "reel"],
    "hunting": ["hunt", "rifle", "deer", "duck", "season", "shotgun"],
    "outdoor_gear": ["gear", "equipment", "backpack", "tools", "knife"],
    "recipes": ["recipe", "cook", "grill", "smoke", "food", "venison"],
    "camping": ["camp", "tent", "sleeping bag", "campfire", "hike"],
    "deer_season": ["deer", "buck", "antlers", "rut", "stand"],
    "uncategorized": []
}

def detect_category(topic):
    """Detect the correct category ID based on keywords in the topic/title."""
    topic_lower = topic.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in topic_lower for keyword in keywords):
            return CATEGORY_IDS.get(category, 1)
    return CATEGORY_IDS.get("uncategorized", 1)
