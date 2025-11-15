# ======================================================================
# File: wordpress_client.py
# Path: ./wordpress_client.py
# Purpose: Minimal REST client to publish clean HTML to WordPress
# ======================================================================
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class WordPressClient:
    base_url: str
    username: str
    application_password: str

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
        Send HTML as-is. Do not escape or re-encode; WP expects HTML here.
        """
        payload = {
            "title": title,
            "content": html_content,  # already HTML; keep untouched
            "excerpt": excerpt,
            "status": status,
        }
        if categories:
            payload["categories"] = categories
        if tags:
            payload["tags"] = tags

        url = self.base_url.rstrip("/") + "/wp-json/wp/v2/posts"
        resp = requests.post(url, headers=self._json_headers(), data=json.dumps(payload))
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"WP create_post failed: {resp.status_code} {resp.text}")
        data = resp.json()
        return int(data["id"])
