import requests
from urllib.parse import quote_plus
from datetime import datetime
from config import WP_URL, WP_USERNAME, WP_PASSWORD, AFFILIATE_TAG, CATEGORIES, SITE_BASE

def build_cta(category):
    url = f"https://www.amazon.com/s?k={quote_plus(category)}&tag={AFFILIATE_TAG}"
    return f'<p><strong>Recommended gear:</strong> <a href="{url}" target="_blank" rel="nofollow">Shop on Amazon</a></p>'

def post_to_wordpress(title, html, category, img_url, focus_keyword):
    """Publish post to WordPress."""
    payload = {
        "title": title,
        "content": f"{html}\n\n{build_cta(category)}",
        "status": "publish",
        "categories": [CATEGORIES.get(category, 38)],  # default = hunting
        "meta": {
            "fifu_image_url": img_url,
            "_aioseo_focus_keyphrase": focus_keyword,
        },
    }
    r = requests.post(WP_URL, json=payload, auth=(WP_USERNAME, WP_PASSWORD))
    if r.status_code not in (200, 201):
        print(f"❌ Error: {r.text[:200]}")
    else:
        print(f"✅ Posted: {title}")
