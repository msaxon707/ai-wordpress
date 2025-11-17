import os
import logging
import requests

logger = logging.getLogger(__name__)


class WordPressClient:
    def __init__(self, base_url=None, username=None, password=None):
        self.base_url = (base_url or os.getenv("WP_BASE_URL", "")).rstrip("/")
        self.username = username or os.getenv("WP_USERNAME")
        self.password = password or os.getenv("WP_APP_PASSWORD")

        if not (self.base_url and self.username and self.password):
            logger.error("WordPressClient initialization failed due to missing credentials or base_url.")
            raise ValueError("WordPress base URL, username, or password not provided.")

        if not self.base_url.endswith("/wp-json/wp/v2"):
            self.api_base = self.base_url + "/wp-json/wp/v2"
        else:
            self.api_base = self.base_url

        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.timeout = 15
        logger.debug(f"Initialized WordPressClient for {self.base_url}")

    def upload_media(self, image_content, filename, alt_text=None):
        """Upload an image to WordPress media library."""
        if not image_content:
            return None

        url = f"{self.api_base}/media"
        headers = {
            "Content-Type": "image/jpeg",
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
        try:
            response = self.session.post(url, headers=headers, data=image_content, timeout=self.timeout)
            if response.status_code not in (200, 201):
                logger.error(f"Media upload failed: {response.status_code} {response.text}")
                return None

            media_id = response.json().get("id")
            if alt_text:
                meta_url = f"{self.api_base}/media/{media_id}"
                self.session.post(meta_url, json={"alt_text": alt_text}, timeout=self.timeout)
            return media_id

        except Exception as e:
            logger.error(f"Failed to upload media: {e}")
            return None

    def create_post(self, title, content, categories, featured_media_id=None, meta_description=None):
        """Create a new WordPress post with SEO metadata support."""
        url = f"{self.api_base}/posts"
        post_data = {
            "title": title,
            "content": content,
            "status": "publish",
            "categories": categories
        }

        if featured_media_id:
            post_data["featured_media"] = featured_media_id

        if meta_description:
            post_data["yoast_head_json"] = {"description": meta_description}

        try:
            response = self.session.post(url, json=post_data, timeout=self.timeout)
            if response.status_code not in (200, 201):
                logger.error(f"Post creation failed: {response.status_code} {response.text}")
                return None
            return response.json().get("id")

        except Exception as e:
            logger.error(f"Post creation error: {e}")
            return None


def post_to_wordpress(title, content, categories, image_bytes=None, image_filename=None, meta_description=None):
    client = WordPressClient()
    featured_media_id = None

    if image_bytes and image_filename:
        featured_media_id = client.upload_media(image_bytes, image_filename, alt_text=title)

    post_id = client.create_post(
        title=title,
        content=content,
        categories=categories,
        featured_media_id=featured_media_id,
        meta_description=meta_description
    )
    return post_id
