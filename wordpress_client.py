# ======================================================================
# File: wordpress_client.py  (REPLACE ENTIRE FILE)
# ======================================================================
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import requests


@dataclass
class WordPressClient:
    base_url: str
    username: str
    application_password: str

    def __post_init__(self) -> None:
        """
        Normalize and validate base_url to avoid MissingSchema and stray slashes.
        """
        if not self.base_url:
            raise ValueError(
                "WP_BASE_URL is empty. Example: https://your-site.com"
            )

        url = self.base_url.strip()
        # Add scheme if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # Remove trailing slash
        while url.endswith("/"):
            url = url[:-1]

        # Validate
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(
                f"WP_BASE_URL looks invalid: '{self.base_url}'. "
                "Expected like 'https://your-site.com'"
            )

        self.base_url = url

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

    def create_post(
        self,
        title: str,
        html_content: str,
        excerpt: str = "",
        status: str = "draft",
        categories: Optional[list[int]] = None,
        tags: Optional[list[int]] = None,
    ) -> int:
        """
        Send HTML as-is. WordPress expects HTML in 'content'.
        """
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

        url = f"{self.base_url}/wp-json/wp/v2/posts"
        resp = requests.post(url, headers=self._json_headers(), data=json.dumps(payload))
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"WP create_post failed: {resp.status_code} {resp.text}")
        data = resp.json()
        return int(data["id"])
