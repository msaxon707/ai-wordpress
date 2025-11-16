# =========================
# wordpress_client.py
# CLEAN / WITH MEDIA SUPPORT
# =========================

from dataclasses import dataclass
from urllib.parse import urlparse, urlencode
import base64
import json
import requests
from typing import Optional, List, Dict, Any


@dataclass
class WordPressClient:
    base_url: str
    username: str
    application_password: str

    def __post_init__(self) -> None:
        if not self.base_url:
            raise ValueError("WP_BASE_URL is empty (e.g., https://your-site.com).")

        raw = self.base_url.strip()
        if not raw.startswith(("http://", "https://")):
            raw = "https://" + raw

        p = urlparse(raw)
        scheme = p.scheme or "https"
        host = p.netloc or p.path.split("/")[0]
        if not host:
            raise ValueError(f"WP_BASE_URL looks invalid: {self.base_url!r}")

        # Normalize: only scheme + host
        self.base_url = f"{scheme}://{host}"

    @property
    def posts_endpoint(self) -> str:
        return f"{self.base_url}/wp-json/wp/v2/posts"

    @property
    def media_endpoint(self) -> str:
        return f"{self.base_url}/wp-json/wp/v2/media"

    # ----------------------
    # AUTH HEADERS
    # ----------------------
    def _auth_header(self) -> dict[str, str]:
        token = f"{self.username}:{self.application_password}".encode("utf-8")
        b64 = base64.b64encode(token).decode("utf-8")
        return {"Authorization": f"Basic {b64}"}

    def _json_headers(self) -> dict[str, str]:
        return {
            **self._auth_header(),
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        }

    # ----------------------
    # SEARCH POSTS
    # ----------------------
    def search_posts(self, title: str, per_page: int = 5) -> List[Dict[str, Any]]:
        """Search posts by title text."""
        params = {"search": title, "per_page": per_page, "context": "edit"}
        url = f"{self.posts_endpoint}?{urlencode(params)}"
        resp = requests.get(url, headers=self._json_headers())

        if resp.status_code != 200:
            raise RuntimeError(f"WP search_posts failed: {resp.status_code} {resp.text}")

        return resp.json()

    # ----------------------
    # MEDIA UPLOAD
    # ----------------------
    def upload_image_from_bytes(
        self,
        image_bytes: bytes,
        filename: str,
        mime_type: str = "image/jpeg",
        alt_text: str = "",
    ) -> int:
        """
        Upload an image to WordPress and return the media ID.
        """
        headers = self._auth_header().copy()
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'

        files = {
            "file": (filename, image_bytes, mime_type),
        }
        data: Dict[str, Any] = {}
        if alt_text:
            data["alt_text"] = alt_text
            data["title"] = alt_text

        resp = requests.post(
            self.media_endpoint,
            headers=headers,
            files=files,
            data=data,
        )

        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"WP upload_image failed: {resp.status_code} {resp.text}"
            )

        media = resp.json()
        return int(media["id"])

    # ----------------------
    # CREATE POST
    # ----------------------
    def create_post(
        self,
        title: str,
        html_content: str,
        excerpt: str = "",
        status: str = "draft",
        categories: Optional[list[int]] = None,
        tags: Optional[list[int]] = None,
        featured_media: Optional[int] = None,
    ) -> int:
        """Create a new WordPress post."""
        payload: Dict[str, Any] = {
            "title": title,
            "content": html_content,
            "excerpt": excerpt,
            "status": status,
        }

        if categories:
            payload["categories"] = categories
        if tags:
            payload["tags"] = tags
        if featured_media is not None:
            payload["featured_media"] = featured_media

        resp = requests.post(
            self.posts_endpoint,
            headers=self._json_headers(),
            data=json.dumps(payload),
        )

        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"WP create_post failed: {resp.status_code} {resp.text}"
            )

        return int(resp.json()["id"])

    # ----------------------
    # UPDATE POST
    # ----------------------
    def update_post(
        self,
        post_id: int,
        title: Optional[str] = None,
        html_content: Optional[str] = None,
        excerpt: Optional[str] = None,
        status: Optional[str] = None,
        categories: Optional[list[int]] = None,
        tags: Optional[list[int]] = None,
        featured_media: Optional[int] = None,
    ) -> int:
        """
        Update an existing WordPress post by ID.
        Only fields you provide will be updated.
        """
        payload: Dict[str, Any] = {}

        if title is not None:
            payload["title"] = title
        if html_content is not None:
            payload["content"] = html_content
        if excerpt is not None:
            payload["excerpt"] = excerpt
        if status is not None:
            payload["status"] = status
        if categories:
            payload["categories"] = categories
        if tags:
            payload["tags"] = tags
        if featured_media is not None:
            payload["featured_media"] = featured_media

        url = f"{self.posts_endpoint}/{post_id}"
        resp = requests.post(url, headers=self._json_headers(), data=json.dumps(payload))

        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"WP update_post failed: {resp.status_code} {resp.text}"
            )

        return int(resp.json()["id"])
