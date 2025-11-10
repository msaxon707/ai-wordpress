import os
import time
import json
import logging
import random
import textwrap
import base64
from datetime import datetime

import requests
import openai

# ---------- CONFIG & LOGGING ---------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4o-mini")

SITE_BASE = (os.getenv("SITE_BASE") or "").rstrip("/")
WP_URL_ENV = (os.getenv("WP_URL") or "").rstrip("/")

# Prefer SITE_BASE. If missing, derive from WP_URL.
if not SITE_BASE and WP_URL_ENV:
    if "/wp-json" in WP_URL_ENV:
        SITE_BASE = WP_URL_ENV.split("/wp-json")[0]
    else:
        SITE_BASE = WP_URL_ENV

WP_USER = os.getenv("WP_USERNAME") or os.getenv("WORDPRESS_USER")
WP_PASS = os.getenv("WP_PASSWORD") or os.getenv("WORDPRESS_APP_PASSWORD")

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
AFFILIATE_TAG = os.getenv("AFFILIATE_TAG", "").strip()
INTERVAL_MINUTES = int(os.getenv("INTERVAL_MINUTES", "180"))

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


# ---------- HELPERS ---------- #

def call_openai_blog(topic: str) -> dict:
    """
    Ask OpenAI to return a JSON object with:
      title, focus_keyword, category, tags, excerpt,
      content_html, image_query, product_ideas
    """
    system_msg = (
        "You are an expert outdoor blogger writing for a casual, friendly audience. "
        "Write like a real human hunter / outdoorsy person: simple, natural, helpful. "
        "No AI disclaimers."
    )

    user_msg = textwrap.dedent(f"""
        Write a detailed blog post about:

        TOPIC: "{topic}"

        Requirements:
        - Tone: expert but natural and conversational (like a friendly hunting buddy).
        - Use clear headings (H2/H3), short paragraphs and bullet points where helpful.
        - Include practical tips and real-world examples.
        - Naturally mention related topics like scouting, safety, ethics when relevant.
        - Include at least 2 internal link placeholders like:
          [INTERNAL_LINK: deer-season], [INTERNAL_LINK: dog-training], etc.
        - Include at least 2 spots where Amazon-style product mentions fit naturally.

        SEO + structure:
        - Choose ONE main focus keyword.
        - Choose ONE category from exactly this list:
          {", ".join(CATEGORY_OPTIONS)}
        - Suggest 3–6 tags.
        - Write a short SEO title and meta description (for search results).
        - Pick a single, rich image idea that would look good as the featured image.

        Amazon:
        - Suggest 2–4 product ideas (gear, tools, accessories) that could link to Amazon.
          Each with a short name and what it’s for (no ASIN needed).

        Return ONLY valid JSON with this structure (no extra text):

        {{
          "title": "...",
          "focus_keyword": "...",
          "seo_title": "...",
          "meta_description": "...",
          "category": "...",
          "tags": ["...", "..."],
          "excerpt": "...",
          "content_html": "<p>Full HTML post here...</p>",
          "image_query": "...",
          "product_ideas": [
            {{"name": "...", "description": "..."}},
            ...
          ]
        }}
    """)

    resp = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        temperature=0.8,
        max_tokens=1800,
    )
    text = resp.choices[0].message["content"]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logging.error("OpenAI response was not valid JSON")
        raise
    return data


def ensure_category_id(name: str) -> int:
    """Find or create a category by name and return its ID."""
    name = name.strip()
    if not name:
        name = "Hunting"

    # Make sure it’s one of our allowed ones
    if name not in CATEGORY_OPTIONS:
        name = "Hunting"

    # Try to find existing
    r = session.get(CATEGORIES_URL, params={"search": name, "per_page": 50})
    r.raise_for_status()
    for cat in r.json():
        if cat["name"].lower() == name.lower():
            return cat["id"]

    # Create if missing
    r = session.post(CATEGORIES_URL, json={"name": name})
    r.raise_for_status()
    logging.info(f"Created new category '{name}' (id={r.json()['id']})")
    return r.json()["id"]


def search_pexels_image(query: str) -> str | None:
    """Return a direct image URL from Pexels (or None)."""
    if not PEXELS_API_KEY:
        logging.warning("PEXELS_API_KEY not set; skipping featured image.")
        return None

    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query or "deer hunting", "per_page": 1, "orientation": "landscape"}
    r = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params)
    if r.status_code != 200:
        logging.warning(f"Pexels error {r.status_code}: {r.text}")
        return None

    data = r.json()
    if not data.get("photos"):
        logging.warning("Pexels returned no photos")
        return None

    photo = data["photos"][0]
    return photo["src"].get("large") or photo["src"].get("original")


def upload_featured_image(image_url: str, title: str) -> int | None:
    """Download image from Pexels and upload to WordPress media, returning media ID."""
    try:
        img_resp = requests.get(image_url, timeout=20)
        img_resp.raise_for_status()
    except Exception as e:
        logging.warning(f"Error downloading image: {e}")
        return None

    filename = "featured-pexels.jpg"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": img_resp.headers.get("Content-Type", "image/jpeg"),
    }
    params = {"alt_text": title[:180]}

    r = session.post(
        MEDIA_URL,
        params=params,
        headers=headers,
        data=img_resp.content,
    )
    if r.status_code not in (200, 201):
        logging.warning(f"Failed to upload media: {r.status_code} {r.text}")
        return None

    media = r.json()
    logging.info(f"Uploaded featured image {media.get('id')} from Pexels")
    return media.get("id")


def build_amazon_links(product_ideas: list[dict]) -> str:
    """Create a small HTML block with Amazon affiliate links."""
    if not product_ideas:
        return ""

    items_html = []
    for p in product_ideas:
        name = p.get("name", "Product").strip()
        desc = p.get("description", "").strip()
        # Simple search URL with affiliate tag
        url = f"https://www.amazon.com/s?k={requests.utils.quote(name)}"
        if AFFILIATE_TAG:
            join = "&" if "?" in url else "?"
            url = f"{url}{join}tag={AFFILIATE_TAG}"

        items_html.append(
            f"<li><strong>{name}</strong> – {desc} "
            f'<a href="{url}" target="_blank" rel="nofollow sponsored">Buy on Amazon</a></li>'
        )

    return (
        "<h2>Recommended Gear</h2>"
        "<ul>" + "\n".join(items_html) + "</ul>"
    )


def replace_internal_placeholders(html: str) -> str:
    """
    Replace [INTERNAL_LINK: slug] placeholders with simple links
    to your own posts (site base).
    """
    for slug in ["deer-season", "dog-training", "recipes", "outdoors", "gear-reviews"]:
        placeholder = f"[INTERNAL_LINK: {slug}]"
        url = f"{SITE_BASE.rstrip('/')}/{slug.strip('/')}/"
        link_html = f'<a href="{url}">{slug.replace("-", " ").title()}</a>'
        html = html.replace(placeholder, link_html)
    return html


def create_wp_post(data: dict) -> None:
    """Create a new post in WordPress based on OpenAI output."""
    title = data.get("title", "New Post").strip()
    focus_keyword = data.get("focus_keyword") or title.split(":")[0][:60]
    seo_title = data.get("seo_title") or title[:60]
    meta_desc = data.get("meta_description") or data.get("excerpt", "")[:155]
    category_name = data.get("category", "Hunting")
    tags = data.get("tags") or []
    excerpt = data.get("excerpt") or ""
    content_html = data.get("content_html") or ""
    image_query = data.get("image_query") or title
    product_ideas = data.get("product_ideas") or []

    # Build category + tag IDs
    cat_id = ensure_category_id(category_name)

    # Get featured image from Pexels
    image_url = search_pexels_image(image_query)
    featured_id = upload_featured_image(image_url, title) if image_url else None

    # Replace internal link placeholders
    content_html = replace_internal_placeholders(content_html)

    # Add Amazon block at the bottom
    content_html += "\n\n" + build_amazon_links(product_ideas)

    # AIOSEO meta
    meta = {
        "_aioseo_focus_keyphrase": focus_keyword,
        "_aioseo_title": seo_title,
        "_aioseo_description": meta_desc,
    }

    payload = {
        "title": title,
        "content": content_html,
        "excerpt": excerpt,
        "status": "publish",
        "categories": [cat_id],
        "tags": [],  # you can map tag names to IDs if you like later
        "featured_media": featured_id or 0,
        "meta": meta,
    }

    r = session.post(POSTS_URL, json=payload)
    if r.status_code not in (200, 201):
        logging.error(f"Failed to create post: {r.status_code} {r.text}")
        return

    post = r.json()
    logging.info(f"✅ Published post {post['id']}: {post['title']['rendered']}")


def choose_next_topic() -> str:
    """Simple rotation between your main themes."""
    topic_buckets = [
        ("Hunting", [
            "Morning vs evening deer hunts: what really works",
            "Top deer hunting strategies for this season",
            "How to scout a new whitetail property",
        ]),
        ("Dogs", [
            "How to train your bird dog to retrieve",
            "Gun dog obedience basics for the field",
        ]),
        ("Recipes", [
            "How to make smoked duck breast at home",
            "Delicious campfire breakfast ideas to wow your morning gatherings",
        ]),
        ("Outdoors", [
            "Backcountry camping gear checklist for beginners",
            "Simple ways to get kids excited about the outdoors",
        ]),
        ("Gear Reviews", [
            "Best budget deer hunting gear that actually holds up",
            "Top dog training tools every bird hunter should own",
        ]),
    ]
    bucket = random.choice(topic_buckets)
    return random.choice(bucket[1])


def main_loop():
    logging.info("Starting The Saxon Blog auto-publisher.")
    logging.info(f"Model: {MODEL} | Interval: {INTERVAL_MINUTES} minutes")

    while True:
        try:
            topic = choose_next_topic()
            logging.info(f"🦌 Generating post on topic: {topic}")
            data = call_openai_blog(topic)
            create_wp_post(data)
        except Exception as e:
            logging.exception(f"Error while generating post: {e}")

        logging.info(f"Sleeping for {INTERVAL_MINUTES} minutes...")
        time.sleep(INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main_loop()
