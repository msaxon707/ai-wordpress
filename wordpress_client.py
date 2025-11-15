# =========================
# path: wordpress_client.py  (FINAL FIXED VERSION)
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
        """
        Normalize base URL to strict form:
          https://example.com
        No trailing slash, no paths.
        """
        if not self.base_url:
            raise ValueError("WP_BASE_URL is empty (expected https://your-site.com)")

        raw = self.base_url.strip()
        if not raw.startswith(("http://", "https://")):
            raw = "https://" + raw

        parsed = urlparse(raw)

        # If the user passes "example.com/something", urlparse treats it as path only
        host = parsed.netloc or parsed.path.split("/")[0]
        if not host:
            raise ValueError(f"WP_BASE_URL looks invalid: {self.base_url!r}")

        scheme = parsed.scheme or "https"
        self.base_url = f"{scheme}://{host}"  # no trailing slash

    # --------------------------
    # ENDPOINTS
    # --------------------------
    @property
    def posts_endpoint(self) -> str:
        return f"{self.base_url}/wp-json/wp/v2/posts"

    @property
    def media_endpoint(self) -> str:
        return f"{self.base_url}/wp-json/wp/v2/media"

    # --------------------------
    # HEADERS / AUTH
    # --------------------------
    def _auth_header(self) -> Dict[str, str]:
        token = f"{self.username}:{self.application_password}".encode("utf-8")
        b64 = base64.b64encode(token).decode("utf-8")
        return {"Authorization": f"Basic {b64}"}

    def _json_headers(self) -> Dict[str, str]:
        return {
            **self._auth_header(),
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        }

    # --------------------------
    # SEARCH POSTS
    # --------------------------
    def search_posts(self, title: str, per_page: int = 5) -> List[Dict[str, Any]]:
        """
        Search posts by text. WordPress searches title/content/excerpt.
        """
        params = {"search": title, "per_page": per_page, "context": "edit"}
        url = f"{self.posts_endpoint}?{urlencode(params)}"

        resp = requests.get(url, headers=self._json_headers())
        if resp.status_code != 200:
            raise RuntimeError(f"[WP search_posts] {resp.status_code}\n{resp.text}")

        return resp.json()

    # --------------------------
    # CREATE POST
    # --------------------------
    def create_post(
        self,
        title: str,
        html_content: str,
        excerpt: str = "",
        status: str = "draft",
        categories: Optional[List[int]] = None,
        tags: Optional[List[int]] = None,
    ) -> int:

        payload = {
            "title": title,
            "content": html_content,
            "excerpt": excerpt,
            "status": status,
        }
        if categories:
            payload["categories"] = categories
        if tags:
            payload["tags"] = tags

        resp = requests.post(
            self.posts_endpoint,
            headers=self._json_headers(),
            data=json.dumps(payload),
        )

        if resp.status_code not in (200, 201):
            raise RuntimeError(f"[WP create_post] {resp.status_code}\n{resp.text}")

        data = resp.json()
        return int(data["id"])

    # --------------------------
    # UPDATE POST
    # --------------------------
    def update_post(
        self,
        post_id: int,
        title: Optional[str] = None,
        html_content: Optional[str] = None,
        excerpt: Optional[str] = None,
        status: Optional[str] = None,
        categories: Optional[List[int]] = None,
        tags: Optional[List[int]] = None,
    ) -> int:

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

        url = f"{self.posts_endpoint}/{post_id}"

        resp = requests.post(
            url,
            headers=self._json_headers(),
            data=json.dumps(payload),
        )

        if resp.status_code not in (200, 201):
            raise RuntimeError(f"[WP update_post] {resp.status_code}\n{resp.text}")

        return int(resp.json().get("id", post_id))

    # --------------------------
    # MEDIA UPLOAD (future use)
    # --------------------------
    def upload_image(self, image_bytes: bytes, filename: str) -> int:
        """
        Upload an image to WordPress media library.

        NOTE: The caller must pass image bytes (PNG/J
