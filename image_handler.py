# image_handler.py
import requests
import random
import os

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")


def get_featured_image_url(topic: str):
    """
    Fetch a featured image URL (plus simple alt text) from Pexels or Unsplash.
    Returns: (image_url, alt_text) or (None, None)
    """
    try:
        image_urls = []

        # Try Pexels
        if PEXELS_API_KEY:
            pexels_url = f"https://api.pexels.com/v1/search?query={topic}&per_page=10"
            headers = {"Authorization": PEXELS_API_KEY}
            response = requests.get(pexels_url, headers=headers, timeout=10)
            if response.ok:
                photos = response.json().get("photos", [])
                image_urls.extend([p["src"]["large"] for p in photos])

        # Try Unsplash if no images yet
        if not image_urls and UNSPLASH_ACCESS_KEY:
            unsplash_url = (
                f"https://api.unsplash.com/search/photos"
                f"?query={topic}&per_page=10&client_id={UNSPLASH_ACCESS_KEY}"
            )
            response = requests.get(unsplash_url, timeout=10)
            if response.ok:
                results = response.json().get("results", [])
                image_urls.extend([r["urls"]["regular"] for r in results])

        if image_urls:
            url = random.choice(image_urls)
            alt = f"Photo related to {topic}"
            return url, alt

        print("⚠️ No image found for:", topic)
        return None, None

    except Exception as e:
        print(f"❌ Image fetch error: {e}")
        return None, None
