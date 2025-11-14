# wordpress_client.py
import os
import re
import base64
import requests

from config import CATEGORIES

SITE_BASE = os.getenv("SITE_BASE", "")


def _slugify(text: str) -> str:
    """Return a WordPress-friendly slug for duplicate detection and tags."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def _resolve_category_id(category):
    """Translate a category key or ID into the numeric ID expected by WordPress."""
    if category is None:
        return None
    if isinstance(category, int):
        return category
    return CATEGORIES.get(str(category))


def _ensure_tag_ids(wp_url: str, headers: dict, tag_names):
    """
    Given a list of tag names, fetch or create them in WordPress and
    return a list of numeric tag IDs.
    """
    if not tag_names:
        return None

    tags_endpoint = wp_url.replace("/posts", "/tags")
    tag_ids = []

    for name in tag_names:
        if not name:
            continue

        slug = _slugify(name)

        # 1) Try to find existing tag
        try:
            resp = requests.get(
                tags_endpoint,
                headers=headers,
                params={"search": name, "per_page": 1},
                timeout=10,
            )
            if resp.ok:
                results = resp.json()
                if results:
                    tag_ids.append(results[0]["id"])
                    continue
        except Exception as e:
            print(f"⚠️ Error looking up tag '{name}': {e}")

        # 2) Create tag if not found
        try:
            create_resp = requests.post(
                tags_endpoint,
                headers=headers,
                json={"name": name, "slug": slug},
                timeout=10,
            )
            if create_resp.status_code in (200, 201):
                tag_ids.append(create_resp.json().get("id"))
            else:
                print(
                    f"⚠️ Failed to create tag '{name}': "
                    f"{create_resp.status_code} - {create_resp.text}"
                )
        except Exception as e:
            print(f"⚠️ Error creating tag '{name}': {e}")

    return tag_ids or None


def create_wordpress_post(
    wp_url,
    username,
    password,
    title,
    content,
    image_url=None,
    image_alt=None,
    affiliate_tag=None,
    focus_keyword=None,
    category=None,
    tags=None,
):
    """
    Creates a post on WordPress with optional featured image, affiliate tag,
    SEO focus keyword, categories, and tags.
    """

    # Affiliate call-to-action block
    if affiliate_tag and SITE_BASE:
        affiliate_section = f"""
        <p><strong>Looking for gear?</strong>
        <a href="{SITE_BASE}?tag={affiliate_tag}" target="_blank" rel="noopener">
        Shop our recommended products here.</a></p>
        """
        content += affiliate_section

    # SEO meta (non-breaking even if theme ignores it)
    if focus_keyword:
        seo_meta = f"""
        <!-- SEO Focus Keyword: {focus_keyword} -->
        <meta name="keywords" content="{focus_keyword}">
        """
        content += seo_meta

    # Basic auth header used for everything
    auth_header = (
        "Basic "
        + base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
    )
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
    }

    # Upload featured image (if any)
    featured_media_id = None
    if image_url:
        try:
            print("📸 Downloading featured image...")
            img_resp = requests.get(image_url, timeout=15)
            img_resp.raise_for_status()
            img_data = img_resp.content

            media_endpoint = wp_url.replace("/posts", "/media")
            media_headers = {
                "Authorization": auth_header,
                "Content-Disposition": f"attachment; filename={os.path.basename(image_url)}",
                "Content-Type": "image/jpeg",
            }

            print("📤 Uploading featured image to WordPress...")
            media_response = requests.post(
                media_endpoint, headers=media_headers, data=img_data, timeout=20
            )

            if media_response.status_code == 201:
                featured_media_id = media_response.json().get("id")
                print(f"✅ Featured image uploaded with ID: {featured_media_id}")

                # Set alt text if provided
                if featured_media_id and image_alt:
                    alt_headers = {
                        "Authorization": auth_header,
                        "Content-Type": "application/json",
                    }
                    requests.post(
                        f"{media_endpoint}/{featured_media_id}",
                        headers=alt_headers,
                        json={"alt_text": image_alt},
                        timeout=10,
                    )
            else:
                print(
                    f"⚠️ Failed to upload image: "
                    f"{media_response.status_code} - {media_response.text}"
                )
        except Exception as e:
            print(f"❌ Error uploading image: {e}")

    # Base post payload
    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
    }

    if featured_media_id:
        post_data["featured_media"] = featured_media_id

    resolved_category = _resolve_category_id(category)
    if resolved_category:
        post_data["categories"] = [resolved_category]

    # Build tag IDs (may be None)
    tag_ids = _ensure_tag_ids(wp_url, headers, tags)
    if tag_ids:
        post_data["tags"] = tag_ids

    # Prevent duplicates based on slug
    try:
        slug = _slugify(title)
        check_response = requests.get(
            wp_url,
            headers=headers,
            params={"slug": slug, "per_page": 1},
            timeout=10,
        )
        if check_response.ok and check_response.json():
            print(f"⚠️ Post with slug '{slug}' already exists. Skipping publish.")
            return None
    except Exception as e:
        print(f"⚠️ Could not verify duplicate post by slug: {e}")

    # Publish post
    try:
        print("📰 Publishing post to WordPress...")
        response = requests.post(wp_url, headers=headers, json=post_data, timeout=30)

        if response.status_code in (200, 201):
            post_id = response.json().get("id")
            print(f"🎉 Successfully published post: {title} (ID: {post_id})")
            return post_id
        else:
            print(
                f"❌ Failed to publish post: "
                f"{response.status_code} - {response.text}"
            )
            return None
    except Exception as e:
        print(f"❌ Error posting to WordPress: {e}")
        return None
