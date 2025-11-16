# image_handler.py
# Always returns a usable image URL & mime type
# Supports: Pexels (PEXELS_API_KEY), Unsplash (UNSPLASH_ACCESS_KEY)
# Falls back to AI-generated placeholder if needed

import os
import requests
from typing import Optional, Tuple


# -----------------------------------
# 🔍 MASTER FUNCTION CALLED BY SCRIPT
# -----------------------------------

def fetch_image_for_topic(topic: str) -> Tuple[Optional[str], str, str]:
    """
    Returns: (image_url, alt_text, mime_type)
    """

    # 1) Try Pexels
    img = fetch_from_pexels(topic)
    if img:
        return img

    # 2) Try Unsplash
    img = fetch_from_unsplash(topic)
    if img:
        return img

    # 3) Fallback AI-generated placeholder (ALWAYS WORKS)
    return fallback_placeholder(topic)


# --------------------------
# ⭐ PEXELS IMAGE PROVIDER
# --------------------------

def fetch_from_pexels(topic: str) -> Optional[Tuple[str, str, str]]:
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        return None

    headers = {"Authorization": api_key}
    url = "https://api.pexels.com/v1/search"
    params = {"query": topic, "per_page": 1}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=12)
        r.raise_for_status()
        data = r.json()

        photos = data.get("photos")
        if not photos:
            return None

        photo = photos[0]
        image_url = photo["src"]["large"]
        alt = photo.get("alt") or topic

        return image_url, alt, "image/jpeg"

    except Exception:
        return None


# ------------------------------
# ⭐ UNSPLASH IMAGE PROVIDER
# ------------------------------

def fetch_from_unsplash(topic: str) -> Optional[Tuple[str, str, str]]:
    api_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not api_key:
        return None

    url = "https://api.unsplash.com/search/photos"
    params = {"query": topic, "per_page": 1, "client_id": api_key}

    try:
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        data = r.json()

        results = data.get("results")
        if not results:
            return None

        photo = results[0]
        image_url = photo["urls"]["regular"]
        alt = photo.get("alt_description") or topic

        return image_url, alt, "image/jpeg"

    except Exception:
        return None


# --------------------------------------------
# 🟢 GUARANTEED FALLBACK (NEVER RETURNS NONE)
# --------------------------------------------

def fallback_placeholder(topic: str) -> Tuple[str, str, str]:
    """
    Always returns an image URL — even if APIs fail.
    """
    safe = topic.replace(" ", "+")
    url = f"https://source.unsplash.com/featured/?{safe}"
    return url, topic, "image/jpeg"
