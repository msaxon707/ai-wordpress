# wp_poster.py
"""
Post builder for The Saxon Blog.

Responsibilities:
- Map category names (Hunting, Dogs, Recipes, Outdoors, Gear Reviews) -> WP IDs
- Upload remote image (Pexels/Unsplash) to WP media and set as featured image
- Send AIOSEO focus keyword via post meta
- Publish post via WP REST API

Both `publish_post_to_wordpress` and `post_to_wordpress` are exposed so old
imports keep working.
"""

from __future__ import annotations

import logging
import mimetypes
import os
import re
from typing import Any, Dict, List, Optional

import requests

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Environment / endpoints
# ---------------------------------------------------------------------------

WP_POSTS_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USERNAME = os.environ.get("WP_USERNAME")
WP_PASSWORD = os.environ.get("WP_PASSWORD")
SITE_BASE = os.environ.get("SITE_BASE", "").rstrip("/")

if not WP_POSTS_URL.endswith("/posts"):
    # Safety: allow user to accidentally set /wp-json/wp/v2 instead of /posts
    if WP_POSTS_URL.endswith("/wp-json/wp/v2"):
        WP_POSTS_URL = WP_POSTS_URL + "/posts"

API_BASE = WP_POSTS_URL.rsplit("/posts", 1)[0]
WP_MEDIA_URL = API_BASE + "/media"
WP_CATEGORIES_URL = API_BASE + "/categories"
WP_TAGS_URL = API_BASE + "/tags"  # Not required, but might be useful later

AUTH = (WP_USERNAME, WP_PASSWORD)

if not WP_USERNAME or not WP_PASSWORD:
    log.error("Missing WP_USERNAME or WP_PASSWORD environment variables.")

# Cache category name -> ID so we don't hammer WP on every post
_category_cache: Dict[str, int] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugify(name: str) -> str:
    """Turn 'Gear Reviews' into 'gear-reviews'."""
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def _get_or_create_category_id(name: str) -> Optional[int]:
    """
    Look up a category ID by name, creating it if it doesn't exist.

    Returns None if it fails.
    """
    if not name:
        return None

    key = name.strip().lower()
    if key in _category_cache:
        return _category_cache[key]

    slug = _slugify(name)

    try:
        # 1) Try to find existing category by slug
        resp = requests.get(
            WP_CATEGORIES_URL,
            params={"slug": slug, "per_page": 1},
            auth=AUTH,
            timeout=20,
        )
        if resp.status_code == 200 and resp.json():
            cat_id = resp.json()[0]["id"]
            _category_cache[key] = cat_id
            log.info("Using existing category '%s' (ID %s)", name, cat_id)
            return cat_id

        # 2) Create category if not found
        create = requests.post(
            WP_CATEGORIES_URL,
            json={"name": name, "slug": slug},
            auth=AUTH,
            timeout=20,
        )
        if create.status_code in (200, 201):
            cat_id = create.json()["id"]
            _category_cache[key] = cat_id
            log.info("Created category '%s' (ID %s)", name, cat_id)
            return cat_id

        log.warning(
            "Could not create category '%s'. Status %s, body: %s",
            name,
            create.status_code,
            create.text[:500],
        )
    except Exception as exc:
        log.exception("Error while getting/creating category '%s': %s", name, exc)

    return None


def _download_image(image_url: str) -> Optional[bytes]:
    try:
        resp = requests.get(image_url, timeout=30)
        if resp.status_code != 200:
            log.warning(
                "Failed to download image %s (status %s)",
                image_url,
                resp.status_code,
            )
            return None
        return resp.content
    except Exception as exc:
        log.exception("Error downloading image %s: %s", image_url, exc)
        return None


def _upload_image_to_wordpress(image_url: str, alt_text: str = "") -> Optional[int]:
    """
    Download image from remote URL and upload it to WordPress media library.
    Returns the media ID, or None if upload fails.
    """
    if not image_url:
        return None

    img_bytes = _download_image(image_url)
    if not img_bytes:
        return None

    # Guess filename and MIME type
    filename = image_url.split("?")[0].rstrip("/").split("/")[-1] or "image.jpg"
    if "." not in filename:
        filename += ".jpg"

    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "image/jpeg"

    files = {
        "file": (filename, img_bytes, mime_type),
    }
    data = {}
    if alt_text:
        data["alt_text"] = alt_text

    try:
        resp = requests.post(
            WP_MEDIA_URL,
            files=files,
            data=data,
            auth=AUTH,
            timeout=40,
        )
        if resp.status_code not in (200, 201):
            log.warning(
                "Failed to upload media. Status %s, body: %s",
                resp.status_code,
                resp.text[:500],
            )
            return None

        media_id = resp.json().get("id")
        if not media_id:
            log.warning("Upload succeeded but no media ID in response.")
            return None

        log.info("Uploaded featured image (media ID %s) from %s", media_id, image_url)
        return media_id
    except Exception as exc:
        log.exception("Error uploading image to WordPress: %s", exc)
        return None


def _derive_focus_keyword(post: Dict[str, Any]) -> str:
    """
    Choose a focus keyword for AIOSEO.
    Priority: explicit 'focus_keyword' -> 'seo_keyword' -> title.
    """
    fk = (
        post.get("focus_keyword")
        or post.get("seo_keyword")
        or post.get("keyword")
        or post.get("title", "")
    )
    return fk.strip()


# ---------------------------------------------------------------------------
# Main publishing function
# ---------------------------------------------------------------------------

def publish_post_to_wordpress(post: Dict[str, Any]) -> Optional[int]:
    """
    Publish a post dict to WordPress.

    Expected keys in `post` (we're flexible and try to handle variations):
        title           (str)  - required
        content / content_html (str) - required
        excerpt         (str)  - optional
        category / categories (str or [str]) - maps to WP categories
        tags            ([str]) - optional (not required)
        image_url       (str)  - remote image URL from Pexels/Unsplash
        image_alt       (str)  - alt text for the image
        focus_keyword   (str)  - optional; falls back to title

    Returns the new post ID on success, None on failure.
    """
    if not WP_POSTS_URL or not WP_USERNAME or not WP_PASSWORD:
        log.error("Cannot publish: missing WP_URL/WP_USERNAME/WP_PASSWORD.")
        return None

    title = (post.get("title") or "").strip()
    content = post.get("content_html") or post.get("content") or ""
    excerpt = post.get("excerpt") or ""

    if not title or not content:
        log.error("Post missing title or content, not publishing: %s", post)
        return None

    # ----- Categories -----
    categories: List[int] = []
    raw_cats = []

    if isinstance(post.get("categories"), list):
        raw_cats = post["categories"]
    elif post.get("category"):
        raw_cats = [post["category"]]

    for cat_name in raw_cats:
        if not isinstance(cat_name, str):
            continue
        cat_id = _get_or_create_category_id(cat_name)
        if cat_id:
            categories.append(cat_id)

    # ----- Featured image -----
    image_url = post.get("image_url") or (post.get("image") or {}).get("url")
    image_alt = (
        post.get("image_alt")
        or (post.get("image") or {}).get("alt")
        or title
    )
    featured_media_id: Optional[int] = None
    if image_url:
        featured_media_id = _upload_image_to_wordpress(image_url, alt_text=image_alt)

    # ----- Focus keyword (AIOSEO) -----
    focus_kw = _derive_focus_keyword(post)

    meta: Dict[str, Any] = {}
    if focus_kw:
        # This is the key AIOSEO uses for focus keyword.
        meta["_aioseo_focuskw"] = focus_kw

    payload: Dict[str, Any] = {
        "title": title,
        "content": content,
        "status": "publish",
    }

    if excerpt:
        payload["excerpt"] = excerpt
    if categories:
        payload["categories"] = categories
    if featured_media_id:
        payload["featured_media"] = featured_media_id
    if meta:
        payload["meta"] = meta

    try:
        resp = requests.post(
            WP_POSTS_URL,
            json=payload,
            auth=AUTH,
            timeout=40,
        )
        if resp.status_code not in (200, 201):
            log.warning(
                "Failed to publish post '%s'. Status %s, body: %s",
                title,
                resp.status_code,
                resp.text[:500],
            )
            return None

        data = resp.json()
        post_id = data.get("id")
        log.info("✅ Published post %s: %s", post_id, title)
        return post_id
    except Exception as exc:
        log.exception("Error publishing post '%s': %s", title, exc)
        return None


# Backwards-compatible name, in case ai_script.py still imports this.
def post_to_wordpress(post: Dict[str, Any]) -> Optional[int]:
    """Thin wrapper so older code keeps working."""
    return publish_post_to_wordpress(post)