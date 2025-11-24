# wordpress_client.py
import requests
from requests.auth import HTTPBasicAuth
import time
from logger_setup import setup_logger

logger = setup_logger()

def create_post(title, content, category, featured_image_id, seo_meta, wp_base_url, wp_user, wp_pass):
    """Create and publish a post to WordPress with SEO metadata."""
    category_endpoint = f"{wp_base_url}/wp-json/wp/v2/categories"
    post_endpoint = f"{wp_base_url}/wp-json/wp/v2/posts"

    try:
        # Resolve category name to ID
        cat_res = requests.get(category_endpoint, auth=HTTPBasicAuth(wp_user, wp_pass), timeout=30)
        cat_res.raise_for_status()
        categories = cat_res.json()
        category_id = next((c["id"] for c in categories if c["name"].lower() == category.lower()), None)

        if not category_id:
            logger.warning(f"⚠️ Category '{category}' not found. Defaulting to 'General'.")
            category_id = next((c["id"] for c in categories if c["name"].lower() == "general"), 1)

        payload = {
            "title": title,
            "content": content,
            "status": "publish",
            "categories": [category_id],
            "featured_media": featured_image_id,
            "meta": {
                "_aioseo_title": seo_meta["title"],
                "_aioseo_description": seo_meta["description"],
                "_aioseo_focuskw": seo_meta["focus_keyphrase"],
            }
        }

        post_res = requests.post(
            post_endpoint,
            auth=HTTPBasicAuth(wp_user, wp_pass),
            json=payload,
            timeout=60
        )

        if post_res.status_code == 201:
            logger.info(f"✅ Post '{title}' published successfully.")
        else:
            logger.error(f"❌ Failed to post: {post_res.status_code} | {post_res.text}")

    except Exception as e:
        logger.error(f"Error creating WordPress post: {e}")
        time.sleep(10)
