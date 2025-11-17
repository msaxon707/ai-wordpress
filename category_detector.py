def detect_category(topic: str) -> int:
    """
    Detects the WordPress category ID based on the topic content.
    Uses your site's category IDs:
      dogs=11, fishing=91, hunting=38, outdoor_gear=90, recipes=54, camping=92,
      deer_season=96, decor=93, uncategorized=1
    """

    topic_lower = topic.lower()

    CATEGORY_IDS = {
        "dogs": 11,
        "fishing": 91,
        "hunting": 38,
        "outdoor_gear": 90,
        "recipes": 54,
        "camping": 92,
        "deer_season": 96,
        "decor": 93,
        "uncategorized": 1,
    }

    # Simple keyword detection logic
    if any(word in topic_lower for word in ["dog", "retriever", "kennel"]):
        return CATEGORY_IDS["dogs"]
    elif any(word in topic_lower for word in ["fish", "fishing", "bass", "trout"]):
        return CATEGORY_IDS["fishing"]
    elif any(word in topic_lower for word in ["hunt", "deer", "duck", "turkey"]):
        return CATEGORY_IDS["hunting"]
    elif any(word in topic_lower for word in ["gear", "knife", "tool", "equipment"]):
        return CATEGORY_IDS["outdoor_gear"]
    elif any(word in topic_lower for word in ["cook", "recipe", "food"]):
        return CATEGORY_IDS["recipes"]
    elif any(word in topic_lower for word in ["camp", "tent", "outdoor"]):
        return CATEGORY_IDS["camping"]
    elif any(word in topic_lower for word in ["season", "buck", "rut"]):
        return CATEGORY_IDS["deer_season"]
    elif any(word in topic_lower for word in ["decor", "farmhouse", "home", "rustic", "design", "living room", "bedroom"]):
        return CATEGORY_IDS["decor"]
    else:
        return CATEGORY_IDS["uncategorized"]
