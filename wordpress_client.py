import os
import logging
import requests

logger = logging.getLogger(__name__)


class WordPressClient:
    """
    WordPress REST API client using Application Passwords.
    Supports creating posts, uploading media, and managing categories.
    """

    def __init__(self, base_url=None, username=None, password=None):
        # ✅ Match Coolify env names exactly
        self.base_url = (base_url or os.getenv("WP_BASE_URL", "")).rstrip("/")
        self.username = username or os.getenv("WP_USERNAME")
        self.password = password or os.getenv("WP_APP_PASSWORD")

        if not (self.base_url and self.username and self.password):
            logger.error("WordPressClient initialization failed due to missing credentials or base_url.")
            raise ValueError("WordPress base URL, username, or password not provided.")

        # Build API endpoint
        if not self.base_url.endswith("/wp-json/wp/v2"):
            self.api_base = f"{self.base_url}/wp-json/wp/v2"
        else:
            self.api_base = self.base_url

        # Configure session
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.timeout = 15
        logger.info(f"✅ WordPressClient initialized for {self.base_url}")

    # ================= POST CREATION =====================

    def create_post(self, title, content, category_ids=None, featured_media_id=None, status="publish"):
        """
        Create and publish a WordPress post.
        """
        url = f"{self.api_base}/posts"
        post_data = {
            "title": title,
            "content": content,
            "status": status,
        }

        if category_ids:
            post_data["categories"] = category_ids if isinstance(category_ids, list) else [category_ids]
        if featured_media_id:
            post_data["featured_media"] = featured_media_id

        try:
            response = self.session.post(url, json=post_data, timeout=self.timeout)
            response.raise_for_status()
            post_id = response.json().get("id")
            logger.info(f"✅ Post created successfully: '{title}' (ID: {post_id})")
            return post_id
        except requests.RequestException as e:
            logger.error(f"❌ Failed to create post: {e}")
            if response is not None:
                logger.error(response.text)
            return None

    # ================= MEDIA UPLOAD =====================

    def upload_media(self, image_content, filename, alt_text=None):
        """
        Upload an image and return its media ID.
        """
        url = f"{self.api_base}/media"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "image/jpeg",
        }

        try:
            response = self.session.post(url, headers=headers, data=image_content, timeout=self.timeout)
            response.raise_for_status()
            media_id = response.json().get("id")
            logger.info(f"✅ Uploaded image: {filename} (Media ID: {media_id})")

            # Optional alt text update
            if media_id and alt_text:
                self.session.post(
                    f"{self.api_base}/media/{media_id}",
                    json={"alt_text": alt_text, "title": alt_text},
                    timeout=self.timeout,
                )

            return media_id
        except requests.RequestException as e:
            logger.error(f"❌ Failed to upload image: {e}")
            if response is not None:
                logger.error(response.text)
            return None

    # ================= CATEGORY HANDLER =====================

    def get_or_create_category(self, category_name):
        """
        Fetch a category ID by name or create it if missing.
        """
        if not category_name:
            return None

        slug = category_name.strip().lower().replace(" ", "-")
        get_url = f"{self.api_base}/categories?slug={slug}"

        try:
            resp = self.session.get(get_url, timeout=self.timeout)
            if resp.status_code == 200 and resp.json():
                return resp.json()[0]["id"]

            # Create category if not found
            cat_data = {"name": category_name, "slug": slug}
            resp = self.session.post(f"{self.api_base}/categories", json=cat_data, timeout=self.timeout)
            if resp.status_code in (200, 201):
                cat_id = resp.json().get("id")
                logger.info(f"✅ Created new category '{category_name}' (ID: {cat_id})")
                return cat_id

            logger.error(f"❌ Failed to create category: {resp.text}")
            return None

        except requests.RequestException as e:
            logger.error(f"❌ Error in get_or_create_category: {e}")
            return None


# ===============================================================
# ✅ Simple wrapper for easy posting
# ===============================================================

def post_to_wordpress(title, content, categories=None, image_bytes=None, image_filename=None):
    """
    High-level helper that handles post creation + optional featured image.
    """
    client = WordPressClient()
    media_id = None

    # Upload image if available
    if image_bytes and image_filename:
        media_id = client.upload_media(image_bytes, image_filename, alt_text=title)

    # Get category IDs
    category_ids = []
    if categories:
        for c in categories:
            cat_id = client.get_or_create_category(c)
            if cat_id:
                category_ids.append(cat_id)

    # Create the post
    return client.create_post(title, content, category_ids, featured_media_id=media_id)
