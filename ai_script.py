#!/usr/bin/env python3
"""
Auto-publisher for The Saxon Blog

Features:
- Rotates through hunting / dogs / bass fishing / recipes / outdoors topics
- Uses OpenAI to write natural, expert-sounding posts
- Creates a DALL·E image, uploads it to WordPress Media, and sets featured image
- Assigns the correct WordPress category ID
- Sets a simple AIOSEO focus keyword + meta title + meta description
- Prevents duplicate titles
- Runs forever with a sleep between posts (SLEEP_MINUTES env var)
"""

import os
import time
import logging
import random
import re
from base64 import b64decode
from typing import Dict, Any, Optional

import requests
from openai import OpenAI

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WORDPRESS_URL = os.getenv("WORDPRESS_URL", "https://thesaxonblog.com").rstrip("/")
WORDPRESS_USER = os.getenv("WORDPRESS_USER")
WORDPRESS_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")
SLEEP_MINUTES = int(os.getenv("SLEEP_MINUTES", "180"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SITE_NAME = os.getenv("SITE_NAME", "The Saxon Blog")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

if not OPENAI_API_KEY:
    raise SystemExit("Missing OPENAI_API_KEY")
if not WORDPRESS_USER or not WORDPRESS_APP_PASSWORD:
    raise SystemExit("Missing WORDPRESS_USER or WORDPRESS_APP_PASSWORD")

client = OpenAI(api_key=OPENAI_API_KEY)

# Category IDs from your site (same as before)
CATEGORY_IDS = {
    "deer season": 31,
    "dogs": 32,
    "bass fishing": 29,
    "recipes": 21,
    "outdoors": 19,
}

TOPIC_CONFIG = [
    {
        "category": "deer season",
        "ideas": [
            "Top deer hunting strategies for this season",
            "Morning vs evening deer hunts: what really works",
            "How weather fronts actually change deer movement",
            "Scent control myths bowhunters still believe",
        ],
    },
    {
        "category": "dogs",
        "ideas": [
            "Training your bird dog to retrieve: tips from the field",
            "How to start a reliable recall with a gun dog",
            "Best off-season drills to keep your dog sharp",
        ],
    },
    {
        "category": "bass fishing",
        "ideas": [
            "Top bass fishing tips for beginners",
            "Cold-water bass strategies that really produce",
            "Bank fishing bass when you don’t own a boat",
        ],
    },
    {
        "category": "recipes",
        "ideas": [
            "How to make smoked duck breast at home",
            "Easy venison chili recipe for busy nights",
            "Crowd-pleasing campfire breakfast ideas",
        ],
    },
    {
        "category": "outdoors",
        "ideas": [
            "Simple ways to get kids excited about the outdoors",
            "Essential gear for your first backcountry trip",
            "How to pack a safe and efficient hunting daypack",
        ],
    },
]

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
log = logging.getLogger("saxon-autoposter")

auth = (WORDPRESS_USER, WORDPRESS_APP_PASSWORD)

# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------


def choose_topic() -> Dict[str, str]:
    """Pick a random category + topic idea."""
    cfg = random.choice(TOPIC_CONFIG)
    topic = random.choice(cfg["ideas"])
    return {"category": cfg["category"], "topic": topic}


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:190]  # WP slug max length safety


def derive_focus_keyword(title: str) -> str:
    words = re.findall(r"[A-Za-z]+", title.lower())
    stop = {"the", "a", "an", "and", "for", "of", "in", "to", "your", "this"}
    core = [w for w in words if w not in stop]
    if not core:
        return title.lower()
    return " ".join(core[:4])


def wp_get_posts_by_slug(slug: str) -> list:
    url = f"{WORDPRESS_URL}/wp-json/wp/v2/posts"
    r = requests.get(url, params={"slug": slug}, auth=auth, timeout=30)
    r.raise_for_status()
    return r.json()


def wp_create_post(payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{WORDPRESS_URL}/wp-json/wp/v2/posts"
    r = requests.post(url, json=payload, auth=auth, timeout=60)
    r.raise_for_status()
    return r.json()


def wp_update_aioseo(post_id: int, focus_kw: str, seo_title: str, seo_desc: str) -> None:
    """
    All in One SEO stores meta in its own table, but it exposes a REST endpoint.
    If the endpoint isn't available, we just silently ignore failures.
    """
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
            log.warning("AIOSEO update failed for %s: %s", post_id, r.text[:200])
    except Exception as e:
        log.warning("AIOSEO update exception for %s: %s", post_id, e)


def generate_article(topic: str, category: str) -> Dict[str, str]:
    """
    Ask OpenAI for a natural, expert-sounding hunting/outdoors article.
    Returns title + HTML content (already formatted with headings, etc.).
    """
    system_prompt = (
        "You are an expert outdoor writer for a friendly hunting and fishing blog "
        "called The Saxon Blog. You write in a natural, conversational tone, "
        "with practical tips and clear headings. You never mention that you are an AI."
    )

    user_prompt = f"""
Write a detailed blog post about:

Topic: "{topic}"
Category: {category}

Requirements:
- Audience: everyday hunters, anglers, dog owners, and home cooks
- Tone: friendly, experienced, never salesy, never robotic
- Structure:
  - Start with a short hook paragraph (no heading)
  - Use H2 and H3 headings (no H1 – the title is separate)
  - Include at least one bullet list
  - Add a short, encouraging conclusion
- Do NOT include any HTML or markdown outside of the article body.
Return the article as HTML only (no title, no <html> or <body> tags).
"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.8,
    )

    body_html = resp.choices[0].message.content.strip()

    # Second call for a tight, human title
    title_resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Write short, catchy blog post titles."},
            {
                "role": "user",
                "content": f"Write a natural sounding title (max 70 characters) for a post about: {topic}",
            },
        ],
        temperature=0.7,
    )
    title = title_resp.choices[0].message.content.strip().strip('"')

    # Short excerpt
    excerpt_resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You write short meta descriptions."},
            {
                "role": "user",
                "content": f"Write a natural 1-sentence meta description (max 155 characters) for this post title: {title}",
            },
        ],
        temperature=0.7,
    )
    excerpt = excerpt_resp.choices[0].message.content.strip()

    return {"title": title, "body_html": body_html, "excerpt": excerpt}


def generate_image_file(title: str) -> Optional[str]:
    """
    Use DALL·E (gpt-image-1) to generate an image file on disk.
    Returns the local file path or None on failure.
    """
    try:
        prompt = (
            f"Photo-realistic outdoor themed image that fits this blog post title: '{title}'. "
            f"Style: natural hunting / fishing / outdoors photography, no text."
        )
        img_resp = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            n=1,
        )
        b64 = img_resp.data[0].b64_json
        img_bytes = b64decode(b64)
        slug = slugify(title)
        filename = f"/tmp/{slug or 'image'}.png"
        with open(filename, "wb") as f:
            f.write(img_bytes)
        return filename
    except Exception as e:
        log.warning("Image generation failed: %s", e)
        return None


def upload_image_to_wp(file_path: str, title: str) -> Optional[Dict[str, Any]]:
    """
    Uploads a local image file to WordPress media library.
    Returns the full media JSON or None.
    """
    try:
        url = f"{WORDPRESS_URL}/wp-json/wp/v2/media"
        filename = os.path.basename(file_path)
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "image/png",
        }
        with open(file_path, "rb") as f:
            r = requests.post(url, headers=headers, data=f, auth=auth, timeout=120)
        r.raise_for_status()
        media = r.json()
        log.info("Uploaded image to media library (ID %s)", media.get("id"))
        return media
    except Exception as e:
        log.warning("Media upload failed: %s", e)
        return None


def build_json_ld(post: Dict[str, Any]) -> str:
    """
    Very simple Article JSON-LD.
    """
    slug = post.get("slug", "")
    url = f"{WORDPRESS_URL}/{slug}/"
    title = post.get("title", {}).get("rendered", "")
    desc = post.get("excerpt", {}).get("rendered", "")
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": re.sub("<.*?>", "", desc)[:220],
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "author": {"@type": "Person", "name": "The Saxon Blog"},
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
        },
    }
    import json

    return json.dumps(data, ensure_ascii=False)


# -------------------------------------------------------------------
# MAIN LOOP
# -------------------------------------------------------------------


def publish_one_post() -> None:
    choice = choose_topic()
    category_name = choice["category"]
    topic = choice["topic"]
    category_id = CATEGORY_IDS.get(category_name)

    if not category_id:
        log.error("Unknown category %s – check CATEGORY_IDS", category_name)
        return

    log.info("🦌 Generating %s: %s", category_name, topic)
    article = generate_article(topic, category_name)
    title = article["title"]
    body_html = article["body_html"]
    excerpt = article["excerpt"]
    slug = slugify(title)

    # Prevent duplicate titles / slugs
    existing = wp_get_posts_by_slug(slug)
    if existing:
        log.warning("Duplicate slug '%s' – skipping post", slug)
        return

    focus_kw = derive_focus_keyword(title)
    seo_title = f"{title} | {SITE_NAME}"
    seo_desc = excerpt

    # Generate + upload image
    featured_media_id = None
    first_image_html = ""
    img_path = generate_image_file(title)
    if img_path:
        media = upload_image_to_wp(img_path, title)
        if media and media.get("id"):
            featured_media_id = media["id"]
            img_url = media.get("source_url")
            alt = focus_kw.capitalize()
            first_image_html = (
                f'<figure class="wp-block-image">'
                f'<img src="{img_url}" alt="{alt}" loading="lazy" />'
                f"</figure>\n"
            )

    content_html = first_image_html + body_html

    payload = {
        "title": title,
        "slug": slug,
        "status": "publish",
        "content": content_html,
        "excerpt": excerpt,
        "categories": [category_id],
        "featured_media": featured_media_id or 0,
        # You can add tags here if you want – WP expects tag IDs.
        "meta": {
            # AIOSEO sometimes reads from generic customs too:
            "_aioseo_focus_keyword": focus_kw,
            "_aioseo_title": seo_title,
            "_aioseo_description": seo_desc,
            # JSON-LD blob (theme/plugins can pick this up)
            "saxon_json_ld": build_json_ld(
                {"slug": slug, "title": {"rendered": title}, "excerpt": {"rendered": excerpt}}
            ),
        },
    }

    post = wp_create_post(payload)
    post_id = post.get("id")
    log.info("✅ Published post %s: %s", post_id, title)

    # Best-effort AIOSEO REST update (if endpoint exists)
    wp_update_aioseo(post_id, focus_kw, seo_title, seo_desc)


def main_loop() -> None:
    log.info("Starting auto-publisher for %s", SITE_NAME)
    log.info("Model: %s | Interval: %s minutes", MODEL, SLEEP_MINUTES)
    while True:
        try:
            publish_one_post()
        except Exception as e:
            log.error("Error while publishing post: %s", e)
        log.info("Sleeping for %s minutes…", SLEEP_MINUTES)
        time.sleep(SLEEP_MINUTES * 60)


if __name__ == "__main__":
    main_loop()
