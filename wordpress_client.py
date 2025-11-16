# wordpress_client.py
# Minimal WordPress REST client with media upload support

from dataclasses import dataclass
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional

import base64
import requests


@dataclass
class WordPressClient:
    base_url: str
    username: str
    application_password: str

    def __post_init__(self) -> None:
        if not self.base_url:
            raise ValueError("WP_URL / base_url is empty (e.g. https://thesaxonblog.com).")

        raw = self.base_url.strip()
        if not raw.startswith(("http://", "https://")):
            raw = "https://" + raw

        p = urlparse(raw)
        scheme = p.scheme or "https"
        host = p.netloc or p.path.split("/")[0]

        if not host:
            raise ValueError(f"WP_URL looks invalid: {self.base_url!r}")

        self.base_url = f"{scheme}://{host}"

    # ----------- Endpoints -----------

    @property
    def posts_endpoint(self) -> str:
        return f"{self.base_url}/wp-json/wp/v2/posts"

    @property
    def media_endpoint(self) -> str:
        return f"{self.base_url}/wp-json/wp/v2/media"

    # ----------- Auth helpers -----------

    @property
    def _auth_header(self) -> Dict[str, str]:
        token = f"{self.username}:{self.application_password}"
        b64 = base64.b64encode(token.encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {b64}"}

    # ----------- Media upload -----------

    def upload_image_from_bytes(
        self,
        image_bytes: bytes,
        filename: str,
        mime_type: str = "image/jpeg",
        alt_text: Optional[str] = None,
    ) -> Optional[int]:
        files = {
            "file": (filename, image_bytes, mime_type),
        }
        headers = {
            **self._auth_header,
            "Content-Disposition": f'attachment; filename="{filename}"',
        }
        data: Dict[str, Any] = {}
        if alt_text:
            data["alt_text"] = alt_text

        resp = requests.post(self.media_endpoint, headers=headers, files=files, data=data, timeout=30)
        if resp.status_code not in (200, 201):
            print(f"⚠️ Failed to upload media: {resp.status_code} - {resp.text}")
            return None

        media = resp.json()
        media_id = media.get("id")
        print(f"🖼  Media uploaded. ID={media_id}")
        return media_id

    # ----------- Post creation -----------

    def create_post(
        self,
        title: str,
        html_content: str,
        excerpt: str = "",
        status: str = "publish",
        categories: Optional[List[int]] = None,
        featured_media: Optional[int] = None,
    ) -> Optional[int]:
        payload: Dict[str, Any] = {
            "title": title,
            "content": html_content,
            "excerpt": excerpt or "",
            "status": status,
        }

        if categories:
            payload["categories"] = categories
        if featured_media:
            payload["featured_media"] = featured_media

        resp = requests.post(self.posts_endpoint, headers=self._auth_header, json=payload, timeout=30)
        if resp.status_code not in (200, 201):
            print(f"⚠️ Failed to create post: {resp.status_code} - {resp.text}")
            return None

        post = resp.json()
        post_id = post.get("id")
        print(f"📝 Post created. ID={post_id}")
        return post_id
