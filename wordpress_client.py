import base64
import requests
from requests.auth import HTTPBasicAuth
from config import WP_API_URL, WP_USERNAME, WP_APP_PASSWORD
from logger_setup import setup_logger

logger = setup_logger()

def upload_featured_image(image_bytes, filename="featured_image.png"):
    """Uploads generated image to WordPress media library."""
    try:
        media_url = f"{WP_API_URL}/media"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "image/png",  # ✅ Fix: specify MIME type
        }
        auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)
        response = requests.post(media_url, headers=headers, data=image_bytes, auth=auth, timeout=30)

        if response.status_code == 201:
            media_id = response.json()["id"]
            logger.info(f"🖼️ Uploaded featured image (ID: {media_id})")
            return media_id
        else:
            logger.error(f"[Upload] Failed: {response.text}")
            return None
    except Exception as e:
        logger.error(f"⚠️ Image upload failed: {e}")
        return None


def post_to_wordpress(title, content, category_id=None, featured_media_id=None, excerpt=None):
    """Posts the generated article to WordPress."""
    try:
        post_data = {
            "title": title,
            "content": content,
            "status": "publish",
            "excerpt": excerpt or "",
        }

        if category_id:
            post_data["categories"] = [category_id]
        if featured_media_id:
            post_data["featured_media"] = featured_media_id

        auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)
        response = requests.post(f"{WP_API_URL}/posts", json=post_data, auth=auth, timeout=30)

        if response.status_code == 201:
            post_id = response.json()["id"]
            logger.info(f"✅ Post '{title}' published successfully (ID {post_id})")
            return post_id
        else:
            logger.error(f"[Publish] Failed: {response.text}")
            return None
    except Exception as e:
        logger.error(f"⚠️ Failed to publish post: {e}")
        return None


def refresh_aioseo(post_id):
    """Force All-in-One SEO plugin to refresh its score for the new post."""
    try:
        auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)

        # 🔁 Trigger AIOSEO refresh endpoint if available
        refresh_url = f"{WP_API_URL}/aioseo/v1/refresh/{post_id}"
        requests.post(refresh_url, auth=auth, timeout=15)

        # 🧾 Re-save post to trigger SEO recalculation
        post_url = f"{WP_API_URL}/posts/{post_id}"
        requests.post(post_url, auth=auth, json={"status": "publish"}, timeout=15)

        logger.info(f"🔁 AIOSEO refresh fully triggered for post {post_id}")
    except Exception as e:
        logger.warning(f"⚠️ Could not refresh AIOSEO: {e}")
