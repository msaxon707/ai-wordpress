import os
import logging
import requests

logger = logging.getLogger(__name__)

class WordPressClient:
    def __init__(self):
        self.base_url = os.getenv("WP_BASE_URL")
        self.username = os.getenv("WP_USERNAME")
        self.password = os.getenv("WP_APP_PASSWORD")

        if not all([self.base_url, self.username, self.password]):
            raise ValueError("[ERROR] Missing WordPress credentials or base URL.")

        self.api_url = f"{self.base_url.rstrip('/')}/wp-json/wp/v2"
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.timeout = 20

    def upload_media(self, image_bytes, filename, alt_text=None):
        """Upload an image to WordPress media library."""
        if not image_bytes:
            return None

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "image/jpeg",
        }

        try:
            response = self.session.post(f"{self.api_url}/media", headers=headers, data=image_bytes, timeout=self.timeout)
            if response.status_code not in (200, 201):
                logger.error(f"Media upload failed: {response.status_code} {response.text}")
                return None

            media_id = response.json().get("id")
            if alt_text:
                self.session.post(f"{self.api_url}/media/{media_id}", json={"alt_text": alt_text, "title": alt_text}, timeout=self.timeout)
            return media_id
        except Exception as e:
            logger.error(f"Media upload error: {e}")
            return None

    def create_post(self, title, content, category_id=None, featured_media_id=None, excerpt=None, status="publish"):
        """Create WordPress post with SEO excerpt."""
        url = f"{self.api_url}/posts"
        post_data = {
            "title": title.strip(),
            "content": content.strip(),
            "status": status,
            "excerpt": excerpt or "",
            "categories": [category_id] if category_id else [],
        }

        if featured_media_id:
            post_data["featured_media"] = featured_media_id

        try:
            response = self.session.post(url, json=post_data, timeout=self.timeout)
            if response.status_code not in (200, 201):
                logger.error(f"Post creation failed: {response.status_code} {response.text}")
                return None
            return response.json().get("id")
        except Exception as e:
            logger.error(f"Post creation error: {e}")
            return None


def post_to_wordpress(title, content, category_id=None, featured_media_id=None, excerpt=None):
    """Simple wrapper for posting to WordPress."""
    client = WordPressClient()
    return client.create_post(
        title=title,
        content=content,
        category_id=category_id,
        featured_media_id=featured_media_id,
        excerpt=excerpt
    )
