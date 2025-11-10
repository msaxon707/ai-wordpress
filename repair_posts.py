import os
import sys
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# ------------ CONFIG FROM ENV ------------

WP_POSTS_URL = os.getenv("WP_URL", "").rstrip("/")
if not WP_POSTS_URL.endswith("/posts"):
    print("❌ WP_URL must point to /wp-json/wp/v2/posts in your .env")
    sys.exit(1)

WP_API_BASE = WP_POSTS_URL.rsplit("/wp/v2/posts", 1)[0]
SITE_BASE = os.getenv("SITE_BASE", "").rstrip("/")
WP_USER = os.getenv("WP_USERNAME")
WP_PASS = os.getenv("WP_PASSWORD")

AUTH = (WP_USER, WP_PASS)


# ------------ HELPERS ------------

def wp_get(url, **params):
    resp = requests.get(url, auth=AUTH, params=params, timeout=30)
    resp.raise_for_status()
    return resp


def wp_post(url, json=None, data=None, headers=None, method="POST"):
    method = method.upper()
    func = {"POST": requests.post, "PUT": requests.put, "PATCH": requests.patch}.get(method, requests.post)
    resp = func(url, auth=AUTH, json=json, data=data, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp


def fetch_all_posts():
    """Fetch all published posts with meta + content."""
    print("🔍 Fetching all posts from WordPress...")
    all_posts = []
    page = 1
    while True:
        resp = wp_get(
            WP_POSTS_URL,
            per_page=20,
            page=page,
            status="publish",
            context="edit",  # include meta
        )
        posts = resp.json()
        if not posts:
            break
        all_posts.extend(posts)
        page += 1
    print(f"✅ Found {len(all_posts)} posts.")
    return all_posts


def fetch_categories():
    """Return dicts mapping slug/name -> id for easy lookup."""
    url = f"{WP_API_BASE}/wp/v2/categories"
    resp = wp_get(url, per_page=100)
    cats = resp.json()
    by_slug = {c["slug"].lower(): c["id"] for c in cats}
    by_name = {c["name"].lower(): c["id"] for c in cats}
    return by_slug, by_name


def ensure_category_ids(post, cat_map_slug, cat_map_name):
    """Assign categories if missing/uncategorized."""
    current_ids = post.get("categories") or []
    title = post.get("title", {}).get("rendered", "")

    # If it already has categories other than 'uncategorized', leave it.
    if current_ids:
        return None  # no change

    wanted = []

    lower_title = title.lower()

    def add_by_slug(slug):
        cid = cat_map_slug.get(slug)
        if cid and cid not in wanted:
            wanted.append(cid)

    def add_by_name(name):
        cid = cat_map_name.get(name.lower())
        if cid and cid not in wanted:
            wanted.append(cid)

    # Simple keyword-based mapping
    if any(w in lower_title for w in ["dog", "bird dog", "retriever", "gsp", "puppy"]):
        add_by_slug("dogs")
        add_by_name("Dogs")

    if any(w in lower_title for w in ["recipe", "campfire", "smoked", "grill", "cook", "breakfast", "dinner"]):
        add_by_slug("recipes")
        add_by_name("Recipes")

    if any(w in lower_title for w in ["gear", "review", "scope", "rifle", "shotgun", "boots", "pack"]):
        add_by_slug("gear-reviews")
        add_by_name("Gear Reviews")

    if any(w in lower_title for w in ["deer", "duck", "turkey", "hunting", "hunt", "fishing"]):
        add_by_slug("hunting")
        add_by_name("Hunting")

    if any(w in lower_title for w in ["camping", "outdoors", "outdoor", "backcountry", "bushcraft", "survival"]):
        add_by_slug("outdoors")
        add_by_name("Outdoors")

    if not wanted:
        return None

    return wanted


def download_image(url):
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp


def upload_media_from_url(image_url, alt_text, title):
    """Download an image from Pexels and upload it into WP media."""
    try:
        img_resp = download_image(image_url)
    except Exception as e:
        print(f"   ⚠️ Failed to download image {image_url}: {e}")
        return None

    filename = urlparse(image_url).path.split("/")[-1] or "image.jpg"
    mime = img_resp.headers.get("Content-Type", "image/jpeg")

    media_endpoint = f"{WP_API_BASE}/wp/v2/media"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": mime,
    }

    try:
        resp = wp_post(media_endpoint, data=img_resp.content, headers=headers, method="POST")
        media = resp.json()
        media_id = media.get("id")
        if not media_id:
            print(f"   ⚠️ Upload returned no media id for {image_url}")
            return None

        # Update alt text if provided
        if alt_text:
            wp_post(f"{media_endpoint}/{media_id}", json={"alt_text": alt_text}, method="POST")

        return media_id
    except Exception as e:
        print(f"   ⚠️ Failed to upload media to WordPress: {e}")
        return None


def ensure_featured_image(post):
    """
    If the post has a FIFU 'remote' image URL but no normal WP featured_media,
    download the image and set featured_media, while keeping the FIFU meta.
    """
    post_id = post["id"]
    if post.get("featured_media"):
        return False  # already has featured image

    meta = post.get("meta") or {}
    fifu_url = meta.get("fifu_image_url") or meta.get("fifu_image")
    if not fifu_url:
        return False  # nothing we can do

    alt_text = meta.get("fifu_image_alt") or post.get("title", {}).get("rendered", "")

    print(f"   🖼  Setting real featured image from FIFU URL for post {post_id}...")
    media_id = upload_media_from_url(fifu_url, alt_text, post.get("title", {}).get("rendered", ""))
    if not media_id:
        return False

    try:
        wp_post(f"{WP_POSTS_URL}/{post_id}", json={"featured_media": media_id}, method="POST")
        print(f"   ✅ Featured image set (media id {media_id}).")
        return True
    except Exception as e:
        print(f"   ⚠️ Failed to update featured_media for post {post_id}: {e}")
        return False


def ensure_links(post):
    """
    Make sure each post has at least 2 internal and 2 external links.
    Internal = links to thesaxonblog.com.
    External = links to trusted outdoor resources.
    """
    content_html = post.get("content", {}).get("rendered") or ""
    if not content_html:
        return False

    soup = BeautifulSoup(content_html, "html.parser")
    links = soup.find_all("a", href=True)

    internal = []
    external = []

    for a in links:
        href = a["href"]
        if href.startswith("#"):
            continue
        if href.startswith("/") or (SITE_BASE and href.startswith(SITE_BASE)):
            internal.append(href)
        elif href.startswith("http://") or href.startswith("https://"):
            if not SITE_BASE or not href.startswith(SITE_BASE):
                external.append(href)

    changed = False

    # Simple internal link targets: link to a couple of other recent posts
    needed_internal = max(0, 2 - len(internal))
    needed_external = max(0, 2 - len(external))

    if needed_internal > 0 or needed_external > 0:
        # We'll append a little "Further reading" section at the end.
        extra_html = '<h3>Further Reading</h3><ul>'

        # INTERNAL links: we'll just link to home & blog page if we don't
        # have specific posts pre-fetched here. (Safer & simpler.)
        if needed_internal > 0:
            extra_html += f'<li><a href="{SITE_BASE}/blog/">More stories from The Saxon Blog</a></li>'
            extra_html += f'<li><a href="{SITE_BASE}/">Visit the home page</a></li>'

        # EXTERNAL links: a couple of safe outdoor resources
        if needed_external > 0:
            extra_html += (
                '<li><a href="https://www.fs.usda.gov/visit/know-before-you-go" target="_blank" rel="nofollow">'
                "US Forest Service – Know Before You Go</a></li>"
            )
            extra_html += (
                '<li><a href="https://www.nwf.org/Outdoor-Activities" target="_blank" rel="nofollow">'
                "National Wildlife Federation – Outdoor Activities</a></li>"
            )

        extra_html += "</ul>"

        # Append to content
        new_tail = BeautifulSoup(extra_html, "html.parser")
        soup.append(new_tail)
        changed = True

    if not changed:
        return False

    new_content_html = str(soup)
    try:
        wp_post(
            f"{WP_POSTS_URL}/{post['id']}",
            json={"content": new_content_html},
            method="POST",
        )
        print("   🔗 Added extra internal/external links.")
        return True
    except Exception as e:
        print(f"   ⚠️ Failed to update links for post {post['id']}: {e}")
        return False


def suggest_focus_and_meta(post):
    """Return (focus_keyword, meta_description) suggestion for logging only."""
    title = post.get("title", {}).get("rendered", "")
    soup = BeautifulSoup(post.get("content", {}).get("rendered") or "", "html.parser")
    text = soup.get_text(" ", strip=True)

    # Focus keyword: first 4–5 words of title without 'How to'
    base = title.replace("How to", "").replace("how to", "").strip()
    words = base.split()
    focus = " ".join(words[:5]) if words else title

    # Meta description: first ~160 chars from body text
    MAX_DESC = 160
    desc = text[:MAX_DESC]
    if len(text) > MAX_DESC:
        last_space = desc.rfind(" ")
        if last_space > 40:
            desc = desc[:last_space]
    return focus.strip(), desc.strip()


# ------------ MAIN REPAIR LOOP ------------

def main():
    if not (WP_USER and WP_PASS and SITE_BASE):
        print("❌ Missing WP_USERNAME, WP_PASSWORD or SITE_BASE env vars.")
        sys.exit(1)

    posts = fetch_all_posts()
    cat_slug_map, cat_name_map = fetch_categories()

    print("🔧 Starting repair sweep...\n")

    for idx, post in enumerate(posts, start=1):
        post_id = post["id"]
        title = post.get("title", {}).get("rendered", f"(no title #{post_id})")
        print(f"==============================")
        print(f"📝 Post {idx}/{len(posts)}: {title} (ID {post_id})")

        changed_any = False

        # 1) Featured image
        try:
            if ensure_featured_image(post):
                changed_any = True
        except Exception as e:
            print(f"   ⚠️ Error in featured image step: {e}")

        # 2) Categories
        try:
            new_cats = ensure_category_ids(post, cat_slug_map, cat_name_map)
            if new_cats:
                wp_post(f"{WP_POSTS_URL}/{post_id}", json={"categories": new_cats}, method="POST")
                print(f"   🏷  Categories updated to IDs: {new_cats}")
                changed_any = True
        except Exception as e:
            print(f"   ⚠️ Error updating categories: {e}")

        # 3) Links
        try:
            if ensure_links(post):
                changed_any = True
        except Exception as e:
            print(f"   ⚠️ Error updating links: {e}")

        # 4) Focus keyword & meta suggestion (log only)
        focus, meta_desc = suggest_focus_and_meta(post)
        print(f"   🔍 Suggested focus keyword: {focus!r}")
        print(f"   📝 Suggested meta description ({len(meta_desc)} chars): {meta_desc}")

        if not changed_any:
            print("   ➖ No structural changes needed (just suggestions above).")

        time.sleep(0.3)  # be gentle with the API

    print("\n✅ Repair sweep finished. Review the suggestions above for AIOSEO focus keyword + meta description.")


if __name__ == "__main__":
    main()