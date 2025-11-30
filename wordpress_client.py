import os
import base64
import httpx
from logger_setup import setup_logger

logger = setup_logger()

# === CONFIG ===
WP_BASE_URL = os.getenv("WP_BASE_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

AUTH_HEADER = base64.b64encode(f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()).decode()

COMMON_HEADERS = {
    "Authorization": f"Basic {AUTH_HEADER}",
    "Content-Type": "application/json",
}


# === UPLOAD IMAGE TO WORDPRESS ===
def upload_image_to_wordpress(image_path):
    """
    Uploads an image to WordPress Media Library and returns the image ID.
    """
    if not os.path.exists(image_path):
        logger.error(f"❌ Image not found: {image_path}")
        return None

    file_name = os.path.basename(image_path)
    mime_type = "image/png" if file_name.endswith(".png") else "image/jpeg"

    headers = {
        "Authorization": f"Basic {AUTH_HEADER}",
        "Content-Disposition": f'attachment; filename="{file_name}"',
        "Content-Type": mime_type,
    }

    try:
        with open(image_path, "rb") as f:
            response = httpx.post(
                f"{WP_BASE_URL}/wp-json/wp/v2/media",
                headers=headers,
                content=f.read(),
                timeout=60,
            )
        response.raise_for_status()

        media_id = response.json().get("id")
        if media_id:
            logger.info(f"🖼️ Uploaded featured image: {file_name} (ID {media_id})")
            return media_id
        else:
            logger.warning("⚠️ Upload succeeded but no media ID returned.")
            return None
    except Exception as e:
        logger.error(f"❌ Failed to upload image to WordPress: {e}")
        return None


# === PUBLISH POST TO WORDPRESS ===
def post_to_wordpress(title, content, category_id, featured_media_id=None, excerpt=None):
    """
    Publishes a blog post to WordPress.
    """
    logger.info(f"📰 Publishing post to WordPress: {title}")

    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [category_id] if isinstance(category_id, int) else [],
        "excerpt": excerpt or "",
    }

    if featured_media_id:
        post_data["featured_media"] = featured_media_id

    try:
        response = httpx.post(
            f"{WP_BASE_URL}/wp-json/wp/v2/posts",
            headers=COMMON_HEADERS,
            json=post_data,
            timeout=60,
        )
        response.raise_for_status()

        data = response.json()
        post_id = data.get("id")

        if post_id:
            logger.info(f"✅ Post '{title}' published successfully (ID {post_id})")
            return post_id
        else:
            logger.warning("⚠️ WordPress returned no post ID.")
            return None

    except httpx.HTTPStatusError as e:
        logger.error(f"❌ WordPress Error {e.response.status_code}: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error posting to WordPress: {e}")
        return None
