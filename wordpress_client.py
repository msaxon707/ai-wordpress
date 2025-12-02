import requests
from requests.auth import HTTPBasicAuth
from config import WP_API_URL, WP_USERNAME, WP_APP_PASSWORD
from logger_setup import setup_logger

logger = setup_logger()

def post_to_wordpress(title, content, category_id=None, featured_media_id=None, excerpt=""):
    """Publish a post to WordPress."""
    headers = {"Content-Type": "application/json"}
    data = {
        "title": title.strip(),
        "content": content.strip(),
        "status": "publish",
        "excerpt": excerpt.strip(),
    }

    if category_id:
        data["categories"] = [int(category_id)] if isinstance(category_id, (int, str)) and str(category_id).isdigit() else []
    if featured_media_id:
        data["featured_media"] = featured_media_id

    response = requests.post(
        f"{WP_API_URL}/posts",
        auth=HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD),
        headers=headers,
        json=data,
        timeout=60,
    )

    if response.status_code == 201:
        post_id = response.json().get("id")
        logger.info(f"✅ Post '{title}' published successfully (ID {post_id})")
        refresh_aioseo(post_id)
        return post_id
    else:
        logger.error(f"❌ WordPress Error {response.status_code}: {response.text}")
        return None


def upload_image_to_wordpress(image_bytes, filename="featured.png"):
    """Upload image to WordPress media library."""
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    response = requests.post(
        f"{WP_API_URL}/media",
        auth=HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD),
        headers=headers,
        data=image_bytes,
        timeout=60,
    )

    if response.status_code == 201:
        image_id = response.json()["id"]
        logger.info(f"🖼️ Uploaded featured image: {filename} (ID {image_id})")
        return image_id
    else:
        logger.error(f"[Upload] Failed: {response.text}")
        return None


def refresh_aioseo(post_id):
    """Trigger All-in-One SEO to re-analyze the post for scoring."""
    try:
        url = f"{WP_API_URL}/aioseo/v1/refresh/{post_id}"
        requests.post(url, auth=HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD), timeout=15)
        logger.info(f"🔁 AIOSEO refresh triggered for post {post_id}")
    except Exception as e:
        logger.warning(f"⚠️ Could not refresh AIOSEO: {e}")
