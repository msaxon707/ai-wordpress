# wordpress_client.py
import requests
from requests.auth import HTTPBasicAuth
from logger_setup import setup_logger
import time

logger = setup_logger()

def post_to_wordpress(title, content, category_id, featured_media_id, excerpt):
    """Publish article to WordPress."""
    from config import Config
    wp_base_url = Config.WP_BASE_URL
    wp_user = Config.WP_USERNAME
    wp_pass = Config.WP_APP_PASSWORD

    endpoint = f"{wp_base_url}/wp-json/wp/v2/posts"
    payload = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [category_id],
        "featured_media": featured_media_id,
        "excerpt": excerpt,
    }

    try:
        response = requests.post(
            endpoint,
            auth=HTTPBasicAuth(wp_user, wp_pass),
            json=payload,
            timeout=60
        )

        if response.status_code == 201:
            post_id = response.json()["id"]
            logger.info(f"✅ Post published: {title} (ID {post_id})")
            return post_id
        else:
            logger.error(f"❌ WordPress Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error posting to WordPress: {e}")
        time.sleep(5)
        return None