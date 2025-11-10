import requests
import random
import os

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

def get_featured_image_url(topic: str):
    """
    Fetch a featured image URL from Pexels or Unsplash based on topic.
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

        # Try Unsplash if no images found yet
        if not image_urls and UNSPLASH_ACCESS_KEY:
            unsplash_url = f"https://api.unsplash.com/search/photos?query={topic}&per_page=10&client_id={UNSPLASH_ACCESS_KEY}"
            response = requests.get(unsplash_url, timeout=10)
            if response.ok:
                results = response.json().get("results", [])
                image_urls.extend([r["urls"]["regular"] for r in results])

        # Choose one random image
        if image_urls:
            return random.choice(image_urls)

        print("⚠️ No image found for:", topic)
        return None

    except Exception as e:
        print(f"❌ Image fetch error: {e}")
        return None