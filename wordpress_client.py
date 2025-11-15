# =========================
# path: wordpress_client.py  (REPLACE FILE)
# =========================
from dataclasses import dataclass
from urllib.parse import urlparse, urlencode
import base64, json, requests
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
        self.base_url = f"{scheme}://{host}"

    @property
    def posts_endpoint(self) -> str:
        return f"{self.base_url}/wp-json/wp/v2/posts"

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

    # ---- Read/Search ----
    def search_posts(self, title: str, per_page: int = 5) -> List[Dict[str, Any]]:
        """
        Returns recent posts whose title matches the search term.
        """
        params = {"search": title, "per_page": per_page, "context": "edit"}
        url = f"{self.posts_endpoint}?{urlencode(params)}"
        resp = requests.get(url, headers=self._json_headers())
        if resp.status_code != 200:
            raise RuntimeError(f"WP search_posts failed: {resp.status_code} {resp.text}")
        return resp.json()

    # ---- Create ----
    def create_post(
        self,
        title: str,
        html_content: str,
        excerpt: str = "",
        status: str = "draft",
        categories: Optional[list[int]] = None,
        tags: Optional[list[int]] = None,
    ) -> int:
        payload = {"title": title, "content": html_content, "excerpt": excerpt, "status": status}
        if categories: payload["categories"] = categories
        if tags: payload["tags"] = tags
        resp = requests.post(self.posts_endpoint, headers=self._json_headers(), data=json.dumps(payload))
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"WP create_post failed: {resp.status_code} {resp.text}")
        return int(resp.json()["id"])

    # ---- Update ----
    def update_post(
        self,
        post_id: int,
        title: Optional[str] = None,
        html_content: Optional[str] = None,
        excerpt: Optional[str] = None,
        status: Optional[str] = None,
        categories: Optional[list[int]] = None,
        tags: Optional[list[int]] = None,
    ) -> int:
        payload: Dict[str, Any] = {}
        if title is not None: payload["title"] = title
        if html_content is not None: payload["content"] = html_content
        if excerpt is not None: payload["excerpt"] = excerpt
        if status is not None: payload["status"] = status
        if categories: payload["categories"]
