import requests
from config import WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD
from logger_setup import setup_logger

logger = setup_logger()
auth = (WP_USERNAME, WP_APP_PASSWORD)

def get_recent_posts(limit=5):
    """Fetch recent published posts for internal linking."""
    try:
        url = f"{WP_BASE_URL}/wp-json/wp/v2/posts?per_page={limit}&status=publish"
        res = requests.get(url, auth=auth, timeout=15)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logger.warning(f"[WP Fetch] Failed: {e}")
        return []

def post_to_wordpress(title, content, category_id, featured_media_id, excerpt):
    """Publish a new post."""
    try:
        data = {
            "title": title,
            "content": content,
            "status": "publish",
            "categories": [category_id],
            "featured_media": featured_media_id,
            "excerpt": excerpt,
        }
        res = requests.post(f"{WP_BASE_URL}/wp-json/wp/v2/posts", auth=auth, json=data)
        res.raise_for_status()
        logger.info(f"✅ Post '{title}' published successfully (ID {res.json().get('id')})")
        return res.json().get("id")
    except Exception as e:
        logger.error(f"❌ WordPress Error: {e}")
        return None
