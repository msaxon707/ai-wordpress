def detect_category(topic: str):
    """Simple keyword-based category detection."""
    topic_lower = topic.lower()

    if "decor" in topic_lower or "home" in topic_lower:
        return 7  # Home Decor
    if "hunt" in topic_lower:
        return 5  # Hunting
    if "cook" in topic_lower or "recipe" in topic_lower:
        return 8  # Country Recipes
    if "gift" in topic_lower or "holiday" in topic_lower:
        return 9  # Gift Ideas
    if "camp" in topic_lower:
        return 6  # Outdoors / Camping
    if "fish" in topic_lower:
        return 10  # Fishing
    return 1  # General fallback
