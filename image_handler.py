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
    api_key = os.getenv("PEXELS_

                        
