import requests
import random
import io
from config import PEXELS_API_KEY, WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD, ENABLE_LOGGING

def log(msg):
    if ENABLE_LOGGING:
        print(f"[ImageHandler] {msg}")

def get_pexels_image_url(query):
    """
    Searches Pexels for an image matching the query.
    Returns the URL of a random image result.
    """
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 10}
    response = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params)

    if response.status_code != 200:
        log(f"Pexels API error: {response.status_code}")
        return None

    data = response.json()
    photos = data.get("photos", [])
    if not photos:
        log("No Pexels images found for query.")
        return None

    chosen = random.choice(photos)
    return chosen["src"].get("original")

def upload_to_wordpress(image_url, title):
    """
    Uploads an image from URL to WordPress Media Library.
    Returns media ID if successful.
    """
    log(f"Uploading featured image for: {title}")

    img_data = requests.get(image_url).content
    filename = f"{title.replace(' ', '_')}.jpg"

    media_url = f"{WP_BASE_URL}/wp-json/wp/v2/media"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "image/jpeg",
    }

    response = requests.post(
        media_url,
        headers=headers,
        data=img_data,
        auth=(WP_USERNAME, WP_APP_PASSWORD),
    )

    if response.status_code not in [200, 201]:
        log(f"Failed to upload image: {response.status_code}, {response.text}")
        return None

    media_id = response.json().get("id")
    log(f"Image uploaded successfully. Media ID: {media_id}")
    return media_id

def get_featured_image_id(title):
    """
    Complete pipeline: fetch from Pexels → upload to WP → return media ID.
    """
    search_term = title.split(":")[0].split(" ")[0]  # basic keyword for image
    img_url = get_pexels_image_url(search_term)
    if not img_url:
        log("No image URL found, skipping featured image.")
        return None

    return upload_to_wordpress(img_url, title)
