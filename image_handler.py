import requests
import random
import os

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")


def get_featured_image_url(topic: str):
    """
    Returns:
        (image_url, alt_text, mime_type)
    """
    try:
        image_urls = []
        mime_type = "image/jpeg"

        # ------- PEXELS -------
        if PEXELS_API_KEY:
            pexels_url = f"https://api.pexels.com/v1/search?query={topic}&per_page=10"
            response = requests.get(pexels_url, headers={"Authorization": PEXELS_API_KEY}, timeout=10)

            if response.ok:
                photos = response.json().get("photos", [])
                for p in photos:
                    url = p["src"].get("large") or p["src"].get("original")
                    if url:
                        image_urls.append((url, "image/jpeg"))

        # ------- UNSPLASH -------
        if not image_urls and UNSPLASH_ACCESS_KEY:
            unsplash_url = f"https://api.unsplash.com/search/photos?query={topic}&per_page=10&client_id={UNSPLASH_ACCESS_KEY}"
            response = requests.get(unsplash_url, timeout=10)

            if response.ok:
                results = response.json().get("results", [])
                for r in results:
                    url = r["urls"].get("regular")
                    if url:
                        # detect mime from url ending
                        if url.endswith(".png"):
                            image_urls.append((url, "image/png"))
                        else:
                            image_urls.append((url, "image/jpeg"))

        if image_urls:
            selected = random.choice(image_urls)
            url, mime = selected
            alt = f"{topic.title()} photo"
            return url, alt, mime

        print("⚠️ No image found for:", topic)
        return None, None, None

    except Exception as e:
        print(f"❌ Image fetch error: {e}")
        return None, None, None