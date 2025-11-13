import requests
import random
import os

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

def get_featured_image_url(topic: str):
    """
    Fetch a featured image URL + ALT TEXT from Pexels or Unsplash.
    Always returns exactly (image_url, alt_text).
    """
    try:
        images = []

        # Try Pexels first
        if PEXELS_API_KEY:
            pexels_url = f"https://api.pexels.com/v1/search?query={topic}&per_page=10"
            headers = {"Authorization": PEXELS_API_KEY}
            response = requests.get(pexels_url, headers=headers, timeout=10)
            if response.ok:
                photos = response.json().get("photos", [])
                for p in photos:
                    images.append((p["src"]["large"], p.get("alt") or topic))

        # Try Unsplash if no images found yet
        if not images and UNSPLASH_ACCESS_KEY:
            unsplash_url = (
                f"https://api.unsplash.com/search/photos?query={topic}"
                f"&per_page=10&client_id={UNSPLASH_ACCESS_KEY}"
            )
            response = requests.get(unsplash_url, timeout=10)
            if response.ok:
                results = response.json().get("results", [])
                for r in results:
                    alt = r.get("alt_description") or topic
                    images.append((r["urls"]["regular"], alt))

        # Choose one random image
        if images:
            return random.choice(images)  # returns (url, alt)

        print("⚠️ No image found for:", topic)
        return None, topic  # return two values even if empty

    except Exception as e:
        print(f"❌ Image fetch error: {e}")
        return None, topic
