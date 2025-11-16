#!/usr/bin/env python3
# ai_script.py - AI → WordPress autoposter with affiliate links

import os
import sys
import json
import random
import re
from typing import Optional, List, Dict, Any

import requests
from openai import OpenAI

from wordpress_client import WordPressClient
from content_normalizer import normalize_html
from image_handler import fetch_image_for_topic

# Store recent topics (optional, helps avoid repeats)
TOPIC_HISTORY_FILE = "topic_history.json"
MAX_TOPIC_HISTORY = 30

# WordPress category IDs
CATEGORY_IDS = {
    "dogs": 11,
    "fishing": 91,
    "hunting": 38,
    "outdoor_gear": 90,
    "recipes": 54,
    "camping": 92,
    "deer_season": 96,
    "uncategorized": 1,
}

AFFILIATE_FILE = "affiliate_products.json"


# ---------------- Topic history helpers ----------------
def load_recent_topics() -> List[str]:
    try:
        if not os.path.exists(TOPIC_HISTORY_FILE):
            return []
        with open(TOPIC_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(x) for x in data]
    except Exception:
        pass
    return []


def save_topic(topic: str) -> None:
    try:
        topics = load_recent_topics()
        topics.append(topic)
        topics = topics[-MAX_TOPIC_HISTORY:]
        with open(TOPIC_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(topics, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Could not save topic history: {e}")


# ---------------- Category selection ----------------
def choose_categories(topic: str) -> List[int]:
    t = topic.lower()
    cats: List[int] = []

    if any(w in t for w in ["dog", "gsp", "pointer", "puppy"]):
        cats.append(CATEGORY_IDS["dogs"])

    if "fish" in t or "fishing" in t:
        cats.append(CATEGORY_IDS["fishing"])

    if any(w in t for w in ["deer", "whitetail", "rut", "buck", "doe"]):
        cats.append(CATEGORY_IDS["deer_season"])

    if "hunt" in t or "hunting" in t or "turkey" in t or "duck" in t:
        cats.append(CATEGORY_IDS["hunting"])

    if any(w in t for w in ["camp", "tent", "campfire", "camping"]):
        cats.append(CATEGORY_IDS["camping"])

    if any(w in t for w in ["recipe", "cook", "kitchen", "meal", "dinner"]):
        cats.append(CATEGORY_IDS["recipes"])

    if not cats:
        cats.append(CATEGORY_IDS["uncategorized"])

    # de-duplicate while preserving order
    seen = set()
    out = []
    for c in cats:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


# ---------------- Affiliate helpers ----------------
def load_affiliate_products(path: str = AFFILIATE_FILE) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            print("🛒 Loaded affiliate product library.")
            return data
    except Exception as e:
        print(f"⚠️ Could not load affiliate_products.json: {e}")
    return {}


def choose_affiliate_buckets(topic: str, wp_categories: List[int]) -> List[str]:
    t = topic.lower()
    buckets: List[str] = []

    if CATEGORY_IDS["dogs"] in wp_categories:
        buckets.append("dogs_gsp")
    if CATEGORY_IDS["fishing"] in wp_categories:
        buckets.append("fishing")
    if CATEGORY_IDS["camping"] in wp_categories:
        buckets.append("camping")
    if CATEGORY_IDS["deer_season"] in wp_categories or CATEGORY_IDS["hunting"] in wp_categories:
        buckets.append("deer_hunting")
        buckets.append("hunting")
    if CATEGORY_IDS["recipes"] in wp_categories:
        buckets.append("kitchen_recipes")
    if CATEGORY_IDS["outdoor_gear"] in wp_categories:
        buckets.append("hunting")
        buckets.append("survival_bushcraft")

    if "gift" in t or "present" in t:
        buckets.append("gifts_country_men")
    if any(w in t for w in ["decor", "farmhouse", "home", "living room", "bedroom"]):
        buckets.append("farmhouse_decor")
    if any(w in t for w in ["bbq", "grill", "smoker", "pellet"]):
        buckets.append("outdoor_cooking")

    if not buckets:
        buckets = ["hunting", "camping", "gifts_country_men"]

    seen = set()
    out = []
    for b in buckets:
        if b not in seen:
            seen.add(b)
            out.append(b)
    return out


def pick_affiliate_products(
    topic: str,
    wp_categories: List[int],
    affiliate_data: Dict[str, Any],
    min_items: int = 5,
    max_items: int = 10,
) -> List[Dict[str, Any]]:
    if not affiliate_data:
        return []

    buckets = choose_affiliate_buckets(topic, wp_categories)
    pool: List[Dict[str, Any]] = []

    for key in buckets:
        items = affiliate_data.get(key) or []
        for item in items:
            if isinstance(item, dict) and item.get("url"):
                pool.append(item)

    if not pool:
        return []

    n = random.randint(min_items, max_items)
    if len(pool) <= n:
        random.shuffle(pool)
        return pool
    return random.sample(pool, n)


def build_affiliate_html(products: List[Dict[str, Any]]) -> str:
    if not products:
        return ""
    lines = ["<h2>Recommended Products</h2>", "<ul>"]
    for p in products:
        name = p.get("name", "View on Amazon")
        url = p.get("url", "#")
        desc = (p.get("description") or "").strip()
        if desc:
            lines.append(
                f'<li><a href="{url}" target="_blank" rel="nofollow noopener sponsored">{name}</a> – {desc}</li>'
            )
        else:
            lines.append(
                f'<li><a href="{url}" target="_blank" rel="nofollow noopener sponsored">{name}</a></li>'
            )
    lines.append("</ul>")
    return "\n".join(lines)


def inject_affiliate_html_into_body(body_html: str, affiliate_html: str) -> str:
    """Insert affiliate section after the 2nd </p> to keep it inside the article."""
    if not affiliate_html:
        return body_html

    matches = list(re.finditer(r"</p>", body_html, flags=re.IGNORECASE))
    if len(matches) >= 2:
        insert_pos = matches[1].end()
        return body_html[:insert_pos] + "\n\n" + affiliate_html + body_html[insert_pos:]
    else:
        return body_html + "\n\n" + affiliate_html


# ---------------- AI helpers ----------------
def generate_topic(client: OpenAI) -> str:
    recent = load_recent_topics()
    recent_str = "; ".join(recent[-10:]) if recent else "None yet."

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.9,
        max_tokens=64,
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate short, catchy blog post titles for an outdoors / "
                    "country / family lifestyle blog (hunting, fishing, camping, dogs, "
                    "recipes, farmhouse decor, outdoor cooking, gear). "
                    "Return ONLY the title text."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Give me ONE new blog title that is not too similar to any of these: "
                    f"{recent_str}"
                ),
            },
        ],
    )

    topic = (resp.choices[0].message.content or "").strip()
    topic = topic.replace("\n", " ").strip()
    print(f"🧠 Topic: {topic}")
    return topic


def generate_article_html(client: OpenAI, topic: str) -> str:
    prompt = (
        f"Write a friendly, helpful blog post about: {topic}. "
        "This is for a country/outdoors family lifestyle blog. "
        "Use HTML only (no Markdown): <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <em>. "
        "Keep paragraphs short and conversational. 600–900 words."
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = (resp.choices[0].message.content or "").strip()
    return normalize_html(raw)


# ---------------- MAIN ----------------
def main():
    print("🚀 Starting AI WordPress autoposter...\n")

    # Env
    openai_key = os.getenv("OPENAI_API_KEY")
    wp_url = os.getenv("WP_URL")
    wp_user = os.getenv("WP_USERNAME")
    wp_pass = os.getenv("WP_PASSWORD")
    wp_status = os.getenv("WP_STATUS", "publish")

    if not openai_key:
        print("❌ OPENAI_API_KEY is missing.")
        sys.exit(1)
    if not (wp_url and wp_user and wp_pass):
        print("❌ WP_URL / WP_USERNAME / WP_PASSWORD missing.")
        sys.exit(1)

    client = OpenAI(api_key=openai_key)

    # Topic
    topic = os.getenv("TOPIC", "").strip()
    if not topic:
        topic = generate_topic(client)

    # Body HTML
    print("✍️ Generating article body with OpenAI…")
    body_html = generate_article_html(client, topic)

    # Categories
    categories = choose_categories(topic)
    print(f"📚 Categories selected: {categories}")

    # Affiliate products
    affiliate_data = load_affiliate_products()
    affiliate_products = pick_affiliate_products(topic, categories, affiliate_data)
    affiliate_html = build_affiliate_html(affiliate_products)
    if affiliate_html:
        print(f"🛒 Adding {len(affiliate_products)} affiliate products into body.")
        final_html = inject_affiliate_html_into_body(body_html, affiliate_html)
    else:
        print("🛒 No affiliate products added.")
        final_html = body_html

    # WordPress client
    wp = WordPressClient(base_url=wp_url, username=wp_user, application_password=wp_pass)
    print(f"🔌 WordPress endpoint: {wp.posts_endpoint}")

    # Featured image via Pexels/Unsplash
    featured_media_id = None
    img_url, alt_text, mime_type = fetch_image_for_topic(topic)
    if img_url:
        try:
            print(f"📸 Downloading featured image: {img_url}")
            r = requests.get(img_url, timeout=20)
            r.raise_for_status()
            image_bytes = r.content
            filename = img_url.split("/")[-1].split("?")[0] or "featured.jpg"
            if "." not in filename:
                if (mime_type or "").lower() == "image/png":
                    filename += ".png"
                else:
                    filename += ".jpg"
            featured_media_id = wp.upload_image_from_bytes(
                image_bytes=image_bytes,
                filename=filename,
                mime_type=mime_type or "image/jpeg",
                alt_text=alt_text or topic,
            )
            print(f"✅ Uploaded image, media_id={featured_media_id}")
        except Exception as e:
            print(f"⚠️ Failed to upload featured image: {e}")
    else:
        print("⚠️ No image found; skipping featured image.")

    # Create post (no update logic to keep simple)
    post_id = wp.create_post(
        title=topic,
        html_content=final_html,
        excerpt="",
        status=wp_status,
        categories=categories,
        featured_media=featured_media_id,
    )

    save_topic(topic)
    print(f"✅ Done. Post ID: {post_id}")


if __name__ == "__main__":
    main()
