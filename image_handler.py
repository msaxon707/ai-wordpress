import os
import requests
import random
from wordpress_client import WordPressClient

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")


def get_pexels_image(query):
    """Fetches an image from Pexels based on the query."""
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=10"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200 and r.json().get("photos"):
            photos = r.json()["photos"]
            photo = random.choice(photos)
            return photo["src"]["large"]
        else:
            print(f"[ImageHandler] No Pexels images found for query: {query}")
            return None
    except Exception as e:
        print(f"[ImageHandler] Pexels API error: {e}")
        return None


def get_unsplash_image(query):
    """Fetches an image from Unsplash based on the query."""
    url = f"https://api.unsplash.com/search/photos?query={query}&per_page=10&client_id={UNSPLASH_ACCESS_KEY}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and r.json().get("results"):
            photos = r.json()["results"]
            photo = random.choice(photos)
            return photo["urls"]["regular"]
        else:
            print(f"[ImageHandler] No Unsplash images found for query: {query}")
            return None
    except Exception as e:
        print(f"[ImageHandler] Unsplash API error: {e}")
        return None


def get_featured_image_id(topic):
    """
    Fetches and uploads a featured image for the given topic.
    Tries Pexels first, then Unsplash as a fallback.
    """
    print(f"[ImageHandler] Uploading featured image for: {topic}")
    image_url = get_pexels_image(topic) or get_unsplash_image(topic)
    if not image_url:
        print("[ImageHandler] ❌ No image URL found, skipping featured image.")
        return None

    try:
        image_bytes = requests.get(image_url, timeout=10).content
        filename = topic.replace(" ", "_")[:40] + ".jpg"
        client = WordPressClient()
        media_id = client.upload_media(image_bytes, filename, alt_text=topic)
        if media_id:
            print(f"[ImageHandler] ✅ Image uploaded successfully. Media ID: {media_id}")
        else:
            print("[ImageHandler] ❌ Failed to upload image to WordPress.")
        return media_id
    except Exception as e:
        print(f"[ImageHandler] ❌ Image upload failed: {e}")
        return None
