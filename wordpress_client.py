import re
import requests
from requests.auth import HTTPBasicAuth
from config import WP_API_URL, WP_USERNAME, WP_APP_PASSWORD
from logger_setup import setup_logger

logger = setup_logger()


def sanitize_filename(name: str) -> str:
    """Cleans up filenames for safe uploads to WordPress."""
    safe = re.sub(r'[^a-zA-Z0-9_\-\. ]+', '', name)  # remove invalid chars
    safe = re.sub(r'\s+', '_', safe).strip("_")
    return safe[:150] + ".png"  # limit filename length and add extension


def upload_featured_image(image_bytes, filename="featured_image.png"):
    """Uploads generated image to WordPress media library safely."""
    try:
        filename = sanitize_filename(filename)
        media_url = f"{WP_API_URL}/media"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "image/png",
        }
        auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)

        logger.info(f"🖼️ Uploading featured image as '{filename}'...")
        response = requests.post(media_url, headers=headers, data=image_bytes, auth=auth, timeout=30)

        if response.status_code == 201:
            media_id = response.json().get("id")
            logger.info(f"✅ Uploaded featured image (ID: {media_id})")
            return media_id
        else:
            logger.error(f"[Upload] Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"⚠️ Image upload failed: {e}")
        return None


def post_to_wordpress(title, content, category_id=None, featured_media_id=None, excerpt=None):
    """Publishes the generated post to WordPress."""
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
            post_id = response.json().get("id")
            logger.info(f"✅ Post '{title}' published successfully (ID {post_id})")
            return post_id
        else:
            logger.error(f"[Publish] Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"⚠️ Failed to publish post: {e}")
        return None


def refresh_aioseo(post_id):
    """Force All-in-One SEO plugin to refresh its analysis for the post."""
    try:
        auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)

        # 🔁 Step 1: Try AIOSEO endpoint if available
        refresh_url = f"{WP_API_URL}/aioseo/v1/refresh/{post_id}"
        refresh_response = requests.post(refresh_url, auth=auth, timeout=15)

        if refresh_response.status_code in [200, 204]:
            logger.info(f"🔁 AIOSEO refresh endpoint succeeded for post {post_id}")
        else:
            logger.warning(f"[AIOSEO] Refresh endpoint returned {refresh_response.status_code}")

        # 🔁 Step 2: Resave post to trigger recalculation
        post_url = f"{WP_API_URL}/posts/{post_id}"
        resave_response = requests.post(post_url, auth=auth, json={"status": "publish"}, timeout=15)

        if resave_response.status_code in [200, 201]:
            logger.info(f"🧾 Post re-saved successfully to trigger SEO for {post_id}")
        else:
            logger.warning(f"[AIOSEO] Post re-save returned {resave_response.status_code}")

    except Exception as e:
        logger.warning(f"⚠️ Could not refresh AIOSEO: {e}")
