#!/usr/bin/env python3
"""
repair_posts.py

One-time fixer for The Saxon Blog.

- Converts remote FIFU images into real WordPress featured images
- If no image is found there, uses the first <img> in the content
- Sets AIOSEO focus keyword / title / description when missing
"""

import os
import re
import logging
from typing import Optional, Dict, Any
from base64 import b64decode

import requests

WORDPRESS_URL = os.getenv("WORDPRESS_URL", "https://thesaxonblog.com").rstrip("/")
WORDPRESS_USER = os.getenv("WORDPRESS_USER")
WORDPRESS_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")
SITE_NAME = os.getenv("SITE_NAME", "The Saxon Blog")

if not WORDPRESS_USER or not WORDPRESS_APP_PASSWORD:
    raise SystemExit("Missing WORDPRESS_USER or WORDPRESS_APP_PASSWORD")

auth = (WORDPRESS_USER, WORDPRESS_APP_PASSWORD)

logging.basicConfig(level="INFO", format="%(message)s")
log = logging.getLogger("repair")


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:190]


def derive_focus_keyword(title: str) -> str:
    words = re.findall(r"[A-Za-z]+", title.lower())
    stop = {"the", "a", "an", "and", "for", "of", "in", "to", "your", "this"}
    core = [w for w in words if w not in stop]
    if not core:
        return title.lower()
    return " ".join(core[:4])


def wp_get_posts(page: int) -> list:
    url = f"{WORDPRESS_URL}/wp-json/wp/v2/posts"
    params = {
        "per_page": 100,
        "page": page,
        "status": "publish",
        "context": "edit",  # include meta if plugin exposes it
    }
    r = requests.get(url, params=params, auth=auth, timeout=60)
    if r.status_code == 400:
        return []
    r.raise_for_status()
    return r.json()


def wp_get_post(post_id: int) -> Dict[str, Any]:
    url = f"{WORDPRESS_URL}/wp-json/wp/v2/posts/{post_id}"
    r = requests.get(url, params={"context": "edit"}, auth=auth, timeout=60)
    r.raise_for_status()
    return r.json()


def wp_update_post(post_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{WORDPRESS_URL}/wp-json/wp/v2/posts/{post_id}"
    r = requests.post(url, json=payload, auth=auth, timeout=60)
    r.raise_for_status()
    return r.json()


def upload_image_from_url(img_url: str, title: str) -> Optional[int]:
    try:
        r = requests.get(img_url, timeout=120)
        r.raise_for_status()
        data = r.content
        filename = slugify(title) or "image"
        if ".png" in img_url.lower():
            ext, ctype = "png", "image/png"
        else:
            ext, ctype = "jpg", "image/jpeg"
        filename = f"{filename}.{ext}"

        media_url = f"{WORDPRESS_URL}/wp-json/wp/v2/media"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": ctype,
        }
        r2 = requests.post(media_url, headers=headers, data=data, auth=auth, timeout=120)
        r2.raise_for_status()
        media = r2.json()
        return media.get("id")
    except Exception as e:
        log.warning(f"  ⚠️  Failed to upload {img_url}: {e}")
        return None


def find_first_image_url(post: Dict[str, Any]) -> Optional[str]:
    # Try FIFU meta first
    meta = post.get("meta") or {}
    fifu_url = meta.get("fifu_image_url") or meta.get("_fifu_image_url")
    if isinstance(fifu_url, list):
        fifu_url = fifu_url[0] if fifu_url else None
    if fifu_url:
        return fifu_url

    # Fallback: parse first <img> from content
    content = post.get("content", {}).get("rendered", "")
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def wp_update_aioseo(post_id: int, focus_kw: str, seo_title: str, seo_desc: str) -> None:
    try:
        url = f"{WORDPRESS_URL}/wp-json/aioseo/v1/posts/{post_id}"
        payload = {
            "postId": post_id,
            "postType": "post",
            "title": seo_title,
            "description": seo_desc,
            "keywords": [focus_kw],
            "focusKeyphrase": focus_kw,
        }
        r = requests.post(url, json=payload, auth=auth, timeout=30)
        if r.status_code >= 400:
            log.warning(f"  ⚠️  AIOSEO update failed ({post_id}): {r.text[:150]}")
    except Exception as e:
        log.warning(f"  ⚠️  AIOSEO update exception ({post_id}): {e}")


def has_aioseo_meta(post: Dict[str, Any]) -> bool:
    meta = post.get("meta") or {}
    for key in ("_aioseo_focus_keyword", "_aioseo_title", "_aioseo_description"):
        if meta.get(key):
            return True
    return False


def repair() -> None:
    page = 1
    total_processed = 0
    log.info("🔧 Checking existing posts…")

    while True:
        posts = wp_get_posts(page)
        if not posts:
            break
        for post in posts:
            post_id = post["id"]
            title = post["title"]["rendered"]
            total_processed += 1
            log.info(f"\nPost {post_id}: {title}")

            changed = False
            update_payload: Dict[str, Any] = {}

            # 1) Fix featured image if missing
            if not post.get("featured_media"):
                img_url = find_first_image_url(post)
                if img_url:
                    log.info(f"  🖼  Found image URL: {img_url}")
                    media_id = upload_image_from_url(img_url, title)
                    if media_id:
                        update_payload["featured_media"] = media_id
                        log.info(f"  ✅ Set featured image ID {media_id}")
                        changed = True
                else:
                    log.info("  🖼  No image found to set as featured.")

            # 2) Add basic AIOSEO meta if missing
            if not has_aioseo_meta(post):
                focus_kw = derive_focus_keyword(title)
                seo_title = f"{title} | {SITE_NAME}"
                excerpt = post.get("excerpt", {}).get("rendered", "")
                plain_excerpt = re.sub("<.*?>", "", excerpt)[:155]
                seo_desc = plain_excerpt or f"Tips about {focus_kw}."

                meta = post.get("meta") or {}
                meta.update(
                    {
                        "_aioseo_focus_keyword": focus_kw,
                        "_aioseo_title": seo_title,
                        "_aioseo_description": seo_desc,
                    }
                )
                update_payload["meta"] = meta
                log.info(f"  🔑 SEO keyword added: {focus_kw}")
                changed = True

                # Also try real AIOSEO endpoint (best effort)
                wp_update_aioseo(post_id, focus_kw, seo_title, seo_desc)
            else:
                log.info("  🔑 AIOSEO meta already present – leaving as is.")

            if changed:
                wp_update_post(post_id, update_payload)
            else:
                log.info("  ℹ️  No changes needed for this post.")

        page += 1

    log.info(f"\nDone. Checked {total_processed} posts.")


if __name__ == "__main__":
    repair()
