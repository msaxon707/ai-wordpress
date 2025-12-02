import requests
from config import WP_API_URL, WP_USERNAME, WP_APP_PASSWORD
from logger_setup import setup_logger

logger = setup_logger()
auth = (WP_USERNAME, WP_APP_PASSWORD)

def upload_image_to_wordpress(image_path: str):
    """Upload image to WordPress and return its ID."""
    try:
        with open(image_path, "rb") as img:
            filename = image_path.split("/")[-1]
            headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
            response = requests.post(
                f"{WP_API_URL}/media",
                headers=headers,
                auth=auth,
                files={"file": img}
            )
        response.raise_for_status()
        image_id = response.json().get("id")
        logger.info(f"🖼️ Uploaded featured image '{filename}' (ID: {image_id})")
        return image_id
    except Exception as e:
        logger.error(f"[Upload] Failed: {e}")
        return None

def post_to_wordpress(title, content, category_id, featured_media_id=None, excerpt=""):
    """Publish post to WordPress."""
    payload = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [category_id] if isinstance(category_id, int) else [],
        "excerpt": excerpt,
    }
    if featured_media_id:
        payload["featured_media"] = featured_media_id

    try:
        response = requests.post(f"{WP_API_URL}/posts", auth=auth, json=payload)
        response.raise_for_status()
        post = response.json()
        post_id = post.get("id")
        logger.info(f"✅ Post '{title}' published successfully (ID {post_id})")

        # 🔄 Trigger AIOSEO reindex
        try:
            requests.post(f"{WP_API_URL}/posts/{post_id}", auth=auth, json={"aioseo_trigger_update": True})
            logger.info(f"🔄 AIOSEO triggered for post ID {post_id}")
        except Exception as seo_error:
            logger.warning(f"AIOSEO refresh skipped: {seo_error}")

        return post_id
    except Exception as e:
        logger.error(f"❌ WordPress upload failed: {e}")
        return None
