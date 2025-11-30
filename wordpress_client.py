"""
wordpress_client.py — Handles publishing posts to WordPress with SEO data.
"""

import requests
from config import WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD


def post_to_wordpress(title, content, category, featured_media_id, excerpt):
    """Publish post to WordPress via REST API."""
    data = {
        "title": title,
        "content": content,
        "status": "publish",
        "excerpt": excerpt,
        "categories": [],
        "featured_media": featured_media_id
    }

    response = requests.post(
        f"{WP_BASE_URL}/wp-json/wp/v2/posts",
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        json=data
    )

    if response.status_code in [200, 201]:
        post_id = response.json().get("id")
        print(f"[wordpress_client] ✅ Post '{title}' published successfully (ID: {post_id})")
        return post_id

    print(f"[wordpress_client] ❌ Failed to publish post: {response.status_code} - {response.text}")
    return None
