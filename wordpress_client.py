# wordpress_client.py
import requests
import time
from requests.auth import HTTPBasicAuth
from logger_setup import setup_logger
from config import Config

logger = setup_logger()

def post_to_wordpress(title, content, category_id, featured_media_id, excerpt):
    """Publish article to WordPress with retry support for 503/429 errors."""
    wp_base_url = Config.WP_BASE_URL
    wp_user = Config.WP_USERNAME
    wp_pass = Config.WP_APP_PASSWORD
    endpoint = f"{wp_base_url}/wp-json/wp/v2/posts"

    payload = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [_get_category_id(category_id, wp_base_url, wp_user, wp_pass)],
        "featured_media": featured_media_id,
        "excerpt": excerpt,
    }

    for attempt in range(3):
        try:
            response = requests.post(
                endpoint,
                auth=HTTPBasicAuth(wp_user, wp_pass),
                json=payload,
                timeout=60
            )

            if response.status_code == 201:
                post_id = response.json()["id"]
                logger.info(f"✅ Post published successfully: {title} (ID {post_id})")
                return post_id

            elif response.status_code in [429, 503]:
                wait_time = (attempt + 1) * 30
                logger.warning(f"⚠️ WordPress busy (HTTP {response.status_code}). Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            else:
                logger.error(f"❌ WordPress Error {response.status_code}: {response.text}")
                return None

        except Exception as e:
            logger.error(f"❌ Exception during post_to_wordpress: {e}")
            time.sleep(5)

    logger.error("❌ Failed to publish post after 3 retries.")
    return None
