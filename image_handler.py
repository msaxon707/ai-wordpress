import os
import logging
import requests

logger = logging.getLogger(__name__)

def search_image(topic):
    """
    Search for an image related to the given topic using Pexels or Unsplash API.
    Returns a tuple (image_content, filename, alt_text) if successful, otherwise (None, None, None).
    """
    query = topic if topic else "outdoors"
    # Try Pexels first if API key is available
    pexels_api_key = os.getenv('PEXELS_API_KEY')
    if pexels_api_key:
        try:
            headers = {"Authorization": pexels_api_key}
            params = {"query": query, "per_page": 1}
            logger.info(f"Searching Pexels for an image of '{query}'")
            resp = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                photos = data.get("photos")
                if photos:
                    photo = photos[0]
                    src = photo.get("src", {})
                    image_url = src.get("large2x") or src.get("original") or src.get("large")
                    alt_text = photo.get("alt") or f"{topic} image"
                    if image_url:
                        logger.debug(f"Pexels image found: {image_url}")
                        try:
                            img_resp = requests.get(image_url, timeout=10)
                            if img_resp.status_code == 200:
                                image_content = img_resp.content
                                filename = image_url.split('/')[-1].split('?')[0] or f"{query}.jpg"
                                return image_content, filename, alt_text
                        except requests.RequestException as e:
                            logger.warning(f"Failed to download image from Pexels URL: {e}")
            else:
                logger.warning(f"Pexels API request failed with status {resp.status_code}: {resp.text}")
        except requests.RequestException as e:
            logger.error(f"Pexels API request error: {e}")
    # Try Unsplash if Pexels didn't return an image and Unsplash key is available
    unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY')
    if unsplash_key:
        try:
            logger.info(f"Searching Unsplash for an image of '{query}'")
            params = {"query": query}
            resp = requests.get("https://api.unsplash.com/photos/random", params=params,
                                headers={"Authorization": f"Client-ID {unsplash_key}"}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                image_url = data.get("urls", {}).get("regular") or data.get("urls", {}).get("full")
                alt_text = data.get("alt_description") or f"{topic} image"
                if image_url:
                    logger.debug(f"Unsplash image found: {image_url}")
                    try:
                        img_resp = requests.get(image_url, timeout=10)
                        if img_resp.status_code == 200:
                            image_content = img_resp.content
                            filename = image_url.split('/')[-1].split('?')[0] or f"{query}.jpg"
                            return image_content, filename, alt_text
                    except requests.RequestException as e:
                        logger.warning(f"Failed to download image from Unsplash URL: {e}")
            else:
                logger.warning(f"Unsplash API request failed with status {resp.status_code}: {resp.text}")
        except requests.RequestException as e:
            logger.error(f"Unsplash API request error: {e}")
    # If no image found via APIs, use a placeholder
    try:
        placeholder_url = f"https://via.placeholder.com/1200x800.png?text={query.replace(' ', '+')}"
        logger.info("Using placeholder image")
        img_resp = requests.get(placeholder_url, timeout=5)
        if img_resp.status_code == 200:
            image_content = img_resp.content
            filename = "placeholder.png"
            alt_text = f"{topic} image"
            return image_content, filename, alt_text
    except requests.RequestException as e:
        logger.error(f"Placeholder image request failed: {e}")
    # If everything fails, return None
    return None, None, None
