import os
import requests
import json
import random
from urllib.parse import urlencode
from content_generator import generate_meta, extract_focus_keyword

WP_URL = os.getenv("WP_URL", "https://thesaxonblog.com/wp-json/wp/v2/posts")
WP_USER = os.getenv("WP_USERNAME")
WP_PASS = os.getenv("WP_PASSWORD")
SITE_BASE = os.getenv("SITE_BASE", "https://thesaxonblog.com")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

AUTH = (WP_USER, WP_PASS)
HEADERS = {"Content-Type": "application/json"}

def upload_featured_image(image_url, title):
    """Upload the image from Pexels to WordPress and return the attachment ID."""
    img_data = requests.get(image_url).content
    filename = f"{title[:40].replace(' ', '_')}.jpg"
    media_url = SITE_BASE + "/wp-json/wp/v2/media"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    res = requests.post(media_url, headers=headers, data=img_data, auth=AUTH)
    if res.status_code == 201:
        return res.json().get("id")
    return None

def get_internal_links(limit=3):
    """Fetch a few recent posts for internal linking."""
    res = requests.get(WP_URL, params={"per_page": 20, "status": "publish"})
    if res.status_code != 200:
        return []
    posts = res.json()
    if not posts:
        return []
    sample = random.sample(posts, min(limit, len(posts)))
    links = []
    for post in sample:
        title = post["title"]["rendered"]
        link = post["link"]
        links.append(f'<a href="{link}" target="_blank" rel="noopener">{title}</a>')
    return links

def build_internal_links_html(links):
    """Format internal links section."""
    if not links:
        return ""
    html = "<h3>Related Posts:</h3><ul>"
    for link in links:
        html += f"<li>{link}</li>"
    html += "</ul>"
    return html

def log_internal_links(post_title, links):
    """Log which links were used."""
    with open("internal_links_log.txt", "a") as f:
        f.write(f"\nPost: {post_title}\n")
        for l in links:
            f.write(f" - {l}\n")
        f.write("\n")

def post_to_wordpress(title, content, topic, category="Outdoors", tags=[]):
    """Main posting function."""
    focus_keyword = extract_focus_keyword(title)
    seo_title, meta_desc = generate_meta(title, topic)
    internal_links = get_internal_links()
    internal_html = build_internal_links_html(internal_links)
    content = content.replace("{internal_links}", internal_html)

    log_internal_links(title, internal_links)

    # Get featured image from Pexels
    query = urlencode({"query": topic, "per_page": 1})
    res = requests.get(f"https://api.pexels.com/v1/search?{query}",
                       headers={"Authorization": PEXELS_API_KEY})
    img_id = None
    if res.status_code == 200 and res.json().get("photos"):
        img_url = res.json()["photos"][0]["src"]["large"]
        img_id = upload_featured_image(img_url, title)

    data = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [category],
        "tags": tags,
        "meta": {
            "_aioseo_title": seo_title,
            "_aioseo_description": meta_desc,
            "_aioseo_keywords": focus_keyword
        }
    }

    if img_id:
        data["featured_media"] = img_id

    res = requests.post(WP_URL, headers=HEADERS, auth=AUTH, data=json.dumps(data))
    if res.status_code in [200, 201]:
        print(f"✅ Posted: {title}")
    else:
        print(f"❌ Failed to post: {title} | {res.text}")