# category_detector.py
def detect_category(content: str) -> str:
    """Detect category from article content."""
    content_lower = content.lower()
    if any(w in content_lower for w in ["hunt", "rifle", "bow", "deer"]):
        return "Outdoors"
    if any(w in content_lower for w in ["decor", "farmhouse", "wall", "style"]):
        return "Home Decor"
    if any(w in content_lower for w in ["recipe", "cook", "meal", "kitchen"]):
        return "Recipes"
    if any(w in content_lower for w in ["garden", "soil", "plants", "harvest"]):
        return "Gardening"
    if any(w in content_lower for w in ["farm", "ranch", "homestead"]):
        return "Country Living"
    return "General"