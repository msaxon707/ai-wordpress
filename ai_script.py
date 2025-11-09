import os
import time
import random
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import requests
import schedule
from openai import OpenAI

# ----------------- Basic config -----------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MODEL = os.getenv("MODEL", "gpt-3.5-turbo").strip()

WP_POSTS_URL = os.getenv("WP_URL", "").rstrip("/")  # e.g. https://thesaxonblog.com/wp-json/wp/v2/posts
WP_USERNAME = os.getenv("WP_USERNAME", "")
WP_PASSWORD = os.getenv("WP_PASSWORD", "")

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()
AFFILIATE_TAG = os.getenv("AFFILIATE_TAG", "meganmcanespy-20")
POST_INTERVAL_MINUTES = int(os.getenv("POST_INTERVAL_MINUTES", "180"))  # default 3 hours

if not OPENAI_API_KEY:
    raise SystemExit("Missing OPENAI_API_KEY")
if not WP_POSTS_URL or "/wp-json/" not in WP_POSTS_URL:
    raise SystemExit("WP_URL must be the posts endpoint, e.g. https://thesaxonblog.com/wp-json/wp/v2/posts")
if not WP_USERNAME or not WP_PASSWORD:
    raise SystemExit("Missing WP_USERNAME or WP_PASSWORD")
if not UNSPLASH_ACCESS_KEY:
    print("WARNING: UNSPLASH_ACCESS_KEY not set. Posts will publish without featured images.")

WP_BASE = WP_POSTS_URL.split("/wp-json/")[0].rstrip("/")
WP_MEDIA_URL = f"{WP_BASE}/wp-json/wp/v2/media"

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("saxon-blog")

# ------------- Categories & topics -------------

CATEGORIES: Dict[str, int] = {
    "dogs": 11,
    "deer season": 36,
    "hunting": 38,
    "recipes": 54,
    "fishing": 91,
    "outdoor living": 90,
    "survival-bushcraft": 92,
}

TOPIC_BUCKETS: Dict[str, list[str]] = {
    "deer season": [
        "Top deer hunting strategies for this season",
        "How to pattern whitetails on pressured public land",
        "Morning vs evening deer hunts: what really works",
        "Scent control mistakes that ruin your deer hunt",
    ],
    "hunting": [
        "Beginner-friendly gear list for your first hunting season",
        "How to sight in a rifle the simple way",
        "How to stay safe and confident on solo hunts",
        "Cold-weather hunting tips to stay warm and focused",
    ],
    "dogs": [
        "How to start training a hunting dog at home",
        "Gun shyness in hunting dogs and how to prevent it",
        "Daily routine to keep your hunting dog in peak shape",
        "Crate training tips for active sporting dogs",
    ],
    "fishing": [
        "Bank fishing tips when you don’t have a boat",
        "Simple trout fishing setups that just work",
        "Budget-friendly bass fishing gear for beginners",
        "How to choose the right fishing line for any trip",
    ],
    "recipes": [
        "Simple campfire trout recipe for your next trip",
        "Easy venison skillet dinner for busy weeknights",
        "Freezer-friendly wild game meal prep ideas",
        "Cast iron breakfast hash for hunting camp",
    ],
    "outdoor living": [
        "Family-friendly backyard camping ideas",
        "How to start a small home garden for beginners",
        "Budget camping hacks for big families",
        "How to pack your truck for a weekend outdoors",
    ],
    "survival-bushcraft": [
        "Beginner bushcraft skills every hunter should know",
        "Simple shelter-building tips using what’s around you",
        "Basic fire-starting methods that still work when it’s wet",
        "What to keep in a small ‘just in case’ daypack kit",
    ],
}

BUCKET_ORDER = list(TOPIC_BUCKETS.keys())
bucket_index = 0

# ------------- Helper functions -------------


def pick_topic() -> tuple[str, str, int]:
    """Pick a category + topic + category_id in a rotating way."""
    global bucket_index
    bucket = BUCKET_ORDER[bucket_index % len(BUCKET_ORDER)]
    bucket_index += 1
    topics = TOPIC_BUCKETS[bucket]
    topic = random.choice(topics)
    cat_id = CATEGORIES[bucket]
    return bucket, topic, cat_id


def get_unsplash_image_url(topic: str) -> Optional[str]:
    if not UNSPLASH_ACCESS_KEY:
        return None
    try:
        resp = requests.get(
            "https://api.unsplash.com/photos/random",
            params={
                "query": topic,
                "orientation": "landscape",
                "content_filter": "high",
            },
            headers={"Accept-Version": "v1"},
            timeout=20,
        )
        if resp.status_code != 200:
            log.warning("Unsplash error %s: %s", resp.status_code, resp.text[:200])
            return None
        data = resp.json()
        return data.get("urls", {}).get("regular")
    except Exception as e:
        log.warning("Unsplash exception: %s", e)
        return None


def upload_image_to_wp(image_url: str, title: str) -> Optional[int]:
    """Download an image and upload it to WordPress media. Return media ID or None."""
    if not image_url:
        return None
    try:
        img_resp = requests.get(image_url, timeout=30)
        if img_resp.status_code != 200:
            log.warning("Image download failed %s: %s", img_resp.status_code, image_url)
            return None

        filename = (title.lower().replace(" ", "-")[:40] or "image") + ".jpg"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "image/jpeg",
        }

        media_resp = requests.post(
            WP_MEDIA_URL,
            headers=headers,
            data=img_resp.content,
            auth=(WP_USERNAME, WP_PASSWORD),
            timeout=30,
        )
        if media_resp.status_code not in (200, 201):
            log.warning("Media upload failed %s: %s", media_resp.status_code, media_resp.text[:200])
            return None

        media_id = media_resp.json().get("id")
        if not media_id:
            return None

        # Optional: set alt text
        try:
            requests.post(
                f"{WP_MEDIA_URL}/{media_id}",
                json={"alt_text": title},
                auth=(WP_USERNAME, WP_PASSWORD),
                timeout=15,
            )
        except Exception:
            pass

        return media_id
    except Exception as e:
        log.warning("upload_image_to_wp exception: %s", e)
        return None


def generate_post(topic: str, category_name: str) -> Dict[str, Any]:
    """Ask OpenAI for title, HTML body, focus keyword, and tags."""
    system_prompt = (
        "You are an expert outdoor blogger writing for 'The Saxon Blog'. "
        "You sound human, conversational, and experienced, but still clear and easy to follow. "
        "You understand SEO, monetization, and Google AdSense content policies."
    )

    user_prompt = f"""
Write a blog post for the category "{category_name}" on the topic "{topic}" for The Saxon Blog.

Audience: everyday hunters, anglers, outdoor families, and dog owners in the U.S.

Requirements:
- 900–1200 words, natural and human sounding, like a friendly expert.
- Use clear headings (H2/H3), short paragraphs, and bullet or numbered lists where helpful.
- SEO: weave the main idea and related phrases naturally throughout the post.
- Include at least 2 internal links to https://thesaxonblog.com/ (invent realistic slugs).
- Include at least 2 external links to trustworthy, high-authority sites (no Amazon links).
- Include soft, income-focused language (recommend helpful gear, tools, or supplies) but never sound pushy or spammy.
- AdSense-safe: no graphic details, no illegal advice, no hate, no extreme content.
- Body must be PURE HTML using only: <p>, <h2>, <h3>, <ul>, <ol>, <li>, <strong>, <em>, <a>. 
  Do NOT include <html>, <head>, <body>, <script>, or inline CSS/JS.

Also provide:
- a short focus keyword (3–5 words) that best describes the post for SEO
- 5–10 short SEO tags, lowercase, no #.

Respond ONLY with valid JSON in this exact structure:

{{
  "title": "Post title",
  "content_html": "<p>...HTML content...</p>",
  "focus_keyword": "focus keyword here",
  "tags": ["tag one", "tag two", "tag three"]
}}
"""
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()

    import json

    try:
        data = json.loads(raw)
    except Exception:
        # Fallback if JSON is slightly broken: treat all as HTML content
        data = {
            "title": topic,
            "content_html": raw,
            "focus_keyword": topic.lower(),
            "tags": [],
        }

    title = (data.get("title") or topic).strip()
    content_html = (data.get("content_html") or data.get("content") or "").strip()
    focus_keyword = (data.get("focus_keyword") or topic).strip()
    tags = data.get("tags") or []

    return {
        "title": title,
        "content_html": content_html,
        "focus_keyword": focus_keyword,
        "tags": tags,
    }


def add_amazon_cta(content_html: str, category_name: str) -> str:
    """Append a gentle Amazon CTA using your affiliate tag."""
    base_query = {
        "deer season": "deer+hunting+gear",
        "hunting": "hunting+gear",
        "dogs": "hunting+dog+gear",
        "fishing": "fishing+gear",
        "recipes": "cast+iron+cookware+camp",
        "outdoor living": "camping+gear",
        "survival-bushcraft": "survival+kit",
    }.get(category_name, "outdoor+gear")

    amazon_url = f"https://www.amazon.com/s?k={base_query}&tag={AFFILIATE_TAG}"

    cta_html = f"""
<div class="affiliate-cta">
  <p><strong>Recommended gear:</strong> Want to upgrade your setup? Take a look at 
  <a href="{amazon_url}" target="_blank" rel="nofollow sponsored noopener">our favorite {category_name} picks on Amazon</a>
  before your next trip.</p>
</div>
"""
    return content_html + "\n\n" + cta_html


def create_wordpress_post(
    title: str,
    content_html: str,
    category_id: int,
    focus_keyword: str,
    topic: str,
) -> Optional[int]:
    """Create a new published post in WordPress."""
    # Try to get a category-appropriate Unsplash image & upload it
    image_url = get_unsplash_image_url(topic)
    media_id = upload_image_to_wp(image_url, title) if image_url else None

    # Store focus keyword in post meta (even if AIOSEO uses different internal keys,
    # this will at least be available as a custom field).
    meta = {
        "focus_keyword": focus_keyword,
        "_aioseo_focus_keyphrase": focus_keyword,
        "_aioseop_keywords": focus_keyword,
    }

    payload = {
        "title": title,
        "content": content_html,
        "status": "publish",
        "categories": [category_id],
        "meta": meta,
    }
    if media_id:
        payload["featured_media"] = media_id

    resp = requests.post(
        WP_POSTS_URL,
        json=payload,
        auth=(WP_USERNAME, WP_PASSWORD),
        timeout=30,
    )

    if resp.status_code not in (200, 201):
        log.error("Post publish failed %s: %s", resp.status_code, resp.text[:400])
        return None

    post_id = resp.json().get("id")
    log.info("Published post %s: %s", post_id, title)
    return post_id


def job():
    """One scheduled job: pick topic, generate content, publish."""
    try:
        category_name, topic, category_id = pick_topic()
        log.info("🦌 Generating post in category '%s' on topic: %s", category_name, topic)

        post_data = generate_post(topic, category_name)
        title = post_data["title"]
        content_html = post_data["content_html"]
        focus_keyword = post_data["focus_keyword"]

        # Append Amazon CTA
        content_with_cta = add_amazon_cta(content_html, category_name)

        post_id = create_wordpress_post(
            title=title,
            content_html=content_with_cta,
            category_id=category_id,
            focus_keyword=focus_keyword,
            topic=topic,
        )

        if post_id:
            log.info("✅ Published: %s (ID %s)", title, post_id)
        else:
            log.error("❌ Failed to publish: %s", title)

    except Exception as e:
        log.exception("Unexpected error in job(): %s", e)


def main():
    log.info("Starting The Saxon Blog auto-publisher.")
    log.info("Model: %s | Interval: %s minutes", MODEL, POST_INTERVAL_MINUTES)

    # Run once at startup
    job()

    # Schedule every N minutes
    schedule.every(POST_INTERVAL_MINUTES).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(20)


if __name__ == "__main__":
    main()
