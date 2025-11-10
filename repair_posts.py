import os
import logging
import textwrap
import json

import requests
import openai

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4o-mini")
SITE_BASE = (os.getenv("SITE_BASE") or "").rstrip("/")
WP_URL_ENV = (os.getenv("WP_URL") or "").rstrip("/")

if not SITE_BASE and WP_URL_ENV:
    if "/wp-json" in WP_URL_ENV:
        SITE_BASE = WP_URL_ENV.split("/wp-json")[0]
    else:
        SITE_BASE = WP_URL_ENV

WP_USER = os.getenv("WP_USERNAME") or os.getenv("WORDPRESS_USER")
WP_PASS = os.getenv("WP_PASSWORD") or os.getenv("WORDPRESS_APP_PASSWORD")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

if not (OPENAI_API_KEY and SITE_BASE and WP_USER and WP_PASS):
    logging.error("Missing one of: OPENAI_API_KEY, SITE_BASE, WP_USERNAME/WP_PASSWORD")
    raise SystemExit(1)

openai.api_key = OPENAI_API_KEY

POSTS_URL = f"{SITE_BASE}/wp-json/wp/v2/posts"
MEDIA_URL = f"{SITE_BASE}/wp-json/wp/v2/media"
CATEGORIES_URL = f"{SITE_BASE}/wp-json/wp/v2/categories"

CATEGORY_OPTIONS = ["Hunting", "Dogs", "Recipes", "Outdoors", "Gear Reviews"]

session = requests.Session()
session.auth = (WP_USER, WP_PASS)


def ensure_category_id(name: str) -> int:
    name = (name or "").strip()
    if not name or name not in CATEGORY_OPTIONS:
        name = "Hunting"

    r = session.get(CATEGORIES_URL, params={"search": name, "per_page": 50})
    r.raise_for_status()
    for cat in r.json():
        if cat["name"].lower() == name.lower():
            return cat["id"]

    r = session.post(CATEGORIES_URL, json={"name": name})
    r.raise_for_status()
    logging.info(f"Created category '{name}' (id={r.json()['id']})")
    return r.json()["id"]


def search_pexels_image(query: str) -> str | None:
    if not PEXELS_API_KEY:
        return None
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query or "hunting", "per_page": 1, "orientation": "landscape"}
    r = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params)
    if r.status_code != 200:
        logging.warning(f"Pexels error {r.status_code}: {r.text}")
        return None
    data = r.json()
    if not data.get("photos"):
        return None
    photo = data["photos"][0]
    return photo["src"].get("large") or photo["src"].get("original")


def upload_featured_image(image_url: str, title: str) -> int | None:
    try:
        img_resp = requests.get(image_url, timeout=20)
        img_resp.raise_for_status()
    except Exception as e:
        logging.warning(f"Error downloading image: {e}")
        return None

    filename = "repaired-featured.jpg"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": img_resp.headers.get("Content-Type", "image/jpeg"),
    }
    params = {"alt_text": title[:180]}
    r = session.post(MEDIA_URL, params=params, headers=headers, data=img_resp.content)
    if r.status_code not in (200, 201):
        logging.warning(f"Failed to upload media: {r.status_code} {r.text}")
        return None

    media = r.json()
    return media.get("id")


def guess_category_and_focus(title: str, content: str) -> tuple[str, str]:
    """Ask OpenAI for a category + focus keyword based on an existing post."""
    prompt = textwrap.dedent(f"""
        You are helping clean up old WordPress posts about hunting, fishing,
        dogs, recipes and outdoor life.

        Post title: "{title}"

        Content (snippet):
        {content[:800]}

        Choose the BEST matching category from exactly:
        {", ".join(CATEGORY_OPTIONS)}

        Also pick one natural focus keyword for SEO.

        Return ONLY JSON like:
        {{
          "category": "...",
          "focus_keyword": "..."
        }}
    """)
    resp = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=200,
    )
    text = resp.choices[0].message["content"]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return "Hunting", title.split(":")[0][:60]
    return (
        data.get("category", "Hunting"),
        data.get("focus_keyword") or title.split(":")[0][:60],
    )


def fetch_all_posts() -> list[dict]:
    posts = []
    page = 1
    while True:
        r = session.get(
            POSTS_URL,
            params={"per_page": 100, "page": page, "status": "publish"},
        )
        if r.status_code == 400 and "rest_post_invalid_page_number" in r.text:
            break
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        posts.extend(batch)
        page += 1
    return posts


def repair_post(post: dict):
    post_id = post["id"]
    title = post["title"]["rendered"]
    logging.info(f"🔧 Checking post {post_id}: {title}")

    # We only see content as HTML string
    content = post.get("content", {}).get("rendered", "")

    # Ask AI for category + focus keyword
    cat_name, focus_keyword = guess_category_and_focus(title, content)
    cat_id = ensure_category_id(cat_name)

    patch: dict = {}
    meta_updates: dict = {}

    # Category missing?
    if not post.get("categories"):
        patch["categories"] = [cat_id]
        logging.info(f"  → Category set to {cat_name}")

    # Featured image missing?
    if not post.get("featured_media"):
        img_url = search_pexels_image(title)
        if img_url:
            media_id = upload_featured_image(img_url, title)
            if media_id:
                patch["featured_media"] = media_id
                logging.info(f"  → Added featured image (media id {media_id})")
        else:
            logging.info("  → No image found for this post")

    # Always (re)set AIOSEO meta
    meta_updates["_aioseo_focus_keyphrase"] = focus_keyword
    meta_updates["_aioseo_title"] = title[:60]
    meta_updates["_aioseo_description"] = (content.replace("\n", " ")[:155])

    if meta_updates:
        patch["meta"] = meta_updates
        logging.info(f"  → SEO keyword set: {focus_keyword}")

    if not patch:
        logging.info("  → No change for this post.")
        return

    r = session.post(f"{POSTS_URL}/{post_id}", json=patch)
    if r.status_code not in (200, 201):
        logging.error(f"  ✖ Failed to update post {post_id}: {r.status_code} {r.text}")
    else:
        logging.info(f"  ✅ Updated post {post_id}")


def main():
    logging.info("🔧 Repairing all posts on The Saxon Blog...")
    posts = fetch_all_posts()
    logging.info(f"Found {len(posts)} posts.")

    for p in posts:
        try:
            repair_post(p)
        except Exception as e:
            logging.exception(f"Error repairing post {p.get('id')}: {e}")

    logging.info("✅ All posts checked.")


if __name__ == "__main__":
    main()
