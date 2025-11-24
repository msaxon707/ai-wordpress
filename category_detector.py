# category_detector.py
def detect_category(content: str) -> str:
    """Simple category detector with weighted keyword matching."""
    content_lower = content.lower()
    if any(word in content_lower for word in ["hunt", "rifle", "bow", "deer"]):
        return "Outdoors"
    elif any(word in content_lower for word in ["decor", "wall", "farmhouse", "style"]):
        return "Home Decor"
    elif any(word in content_lower for word in ["recipe", "cook", "grill", "meal"]):
        return "Recipes"
    elif any(word in content_lower for word in ["garden", "soil", "harvest", "plant"]):
        return "Gardening"
    elif any(word in content_lower for word in ["farm", "homestead", "ranch"]):
        return "Country Living"
    else:
        return "General"
