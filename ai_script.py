#!/usr/bin/env python3
import os
import sys
import re
import json
import random
from typing import Optional, List

from openai import OpenAI
from wordpress_client import WordpressClient
from content_normalizer import normalize_html
from image_handler import fetch_image_for_topic


# -------------------------------------------------------------------
#  CATEGORY IDS (YOUR WORDPRESS CATEGORY NUMBERS)
# -------------------------------------------------------------------
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


# -------------------------------------------------------------------
#  AFFILIATE PRODUCTS FILE
# -------------------------------------------------------------------
AFFILIATE_FILE = "affiliate_products.json"


# -------------------------------------------------------------------
#  LOAD AFFILIATE PRODUCT LIBRARY
# -------------------------------------------------------------------
def load_affiliate_products(path: str = AFFILIATE_FILE) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            print("🛒 Loaded affiliate product library.")
            return data
    except Exception as e:
        print(f"⚠️ Could not load affiliate_products.json: {e}")

    return {}


# -------------------------------------------------------------------
#  CHOOSE WHICH AFFILIATE BUCKET(S) TO USE
# -------------------------------------------------------------------
def choose_affiliate_buckets(topic: str, wp_categories: Optional[List[int]]) -> List[str]:
    t = topic.lower()
    buckets = []

    # WP Category → Affiliate bucket mapping
    if wp_categories:
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

    # Keyword backups
    if "gift" in t or "present" in t:
        buckets.append("gifts_country_men")

    if any(w in t for w in ["decor", "farmhouse", "home", "living room", "bedroom"]):
        buckets.append("farmhouse_decor")

    if any(w in t for w in ["bbq", "grill", "smoker", "pellet"]):
        buckets.append("outdoor_cooking")

    # Fallback default
    if not buckets:
        buckets = ["hunting", "camping", "gifts_country_men"]

    # Remove duplicates
    seen = set()
    uniq = []
    for b in buckets:
        if b not in seen:
            seen.add(b)
            uniq.append(b)

    return uniq


# -------------------------------------------------------------------
#  PICK 5–10 AFFILIATE PRODUCTS FOR THE POST
# -------------------------------------------------------------------
def pick_affiliate_products(
    topic: str,
    wp_categories: Optional[List[int]],
    affiliate_data: dict,
    min_items: int = 5,
    max_items: int = 10,
) -> List[dict]:

    if not affiliate_data:
        return []

    buckets = choose_affiliate_buckets(topic, wp_categories)
    pool = []

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


# -------------------------------------------------------------------
#  BUILD HTML SECTION FOR "RECOMMENDED PRODUCTS"
# -------------------------------------------------------------------
def build_affiliate_html(products: List[dict]) -> str:
    if not products:
        return ""

    lines = ["<h2>Recommended Products</h2>", "<ul>"]

    for p in products:
        name = p.get("name", "View on Amazon")
        url = p.get("url", "#")
        desc = p.get("description", "")

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


# -------------------------------------------------------------------
#  GENERATE UNIQUE TOPIC (GPT-4o-mini)
# -------------------------------------------------------------------
def generate_topic(client: OpenAI) -> str:
    prompt = (
        "Generate ONE unique blog post idea for an outdoors/country lifestyle website. "
        "Do NOT repeat ideas you've used before. Keep it short and clickable. No quotes."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    topic = resp.choices[0].message["content"].strip()
    topic = topic.replace('"', "").replace("'", "")
    print(f"🧠 Generated topic: {topic}")
    return topic


# -------------------------------------------------------------------
#  CHOOSE WORDPRESS CATEGORIES FROM TOPIC
# -------------------------------------------------------------------
def choose_categories(topic: str) -> Optional[List[int]]:
    t = topic.lower()
    selected = []

    if "dog" in t or "gsp" in t or "pointer" in t:
        selected.append(CATEGORY_IDS["dogs"])

    if "fish" in t:
        selected.append(CATEGORY_IDS["fishing"])

    if "camp" in t or "tent" in t or "outdoor" in t:
        selected.append(CATEGORY_IDS["camping"])

    if any(word in t for word in ["deer", "whitetail", "rut"]):
        selected.append(CATEGORY_IDS["deer_season"])

    if "hunt" in t:
        selected.append(CATEGORY_IDS["hunting"])

    if "recipe" in t or "cook" in t or "kitchen" in t:
        selected.append(CATEGORY_IDS["recipes"])

    if not selected:
        return [CATEGORY_IDS["uncategorized"]]

    return selected


# -------------------------------------------------------------------
#  MAIN SCRIPT
# -------------------------------------------------------------------
def main():
    print("🚀 Starting AI WordPress autoposter...\n")

    # Load environment variables
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    WP_URL = os.getenv("WP_URL")
    WP_USER = os.getenv("WP_USERNAME")
    WP_PASS = os.getenv("WP_PASSWORD")

    if not all([OPENAI_API_KEY, WP_URL, WP_USER, WP_PASS]):
        print("❌ Missing required environment variables.")
        sys.exit(1)

    client = OpenAI(api_key=OPENAI_API_KEY)

    # 1️⃣ GENERATE TOPIC
    topic = generate_topic(client)

    # 2️⃣ GENERATE ARTICLE BODY
    prompt = (
        f"Write a helpful, friendly outdoor-lifestyle blog post about: {topic}. "
        "Include tips or ideas. Around 500–800 words. Use simple language."
    )

    body_resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    html_body = body_resp.choices[0].message["content"].strip()
    normalized_html = normalize_html(html_body)

    # 3️⃣ CATEGORIES
    categories = choose_categories(topic)
    print(f"📚 Categories selected: {categories}")

    # 4️⃣ FEATURED IMAGE
    featured_image_url = fetch_image_for_topic(topic)

    # 5️⃣ AFFILIATE PRODUCTS
    affiliate_data = load_affiliate_products()
    picks = pick_affiliate_products(topic, categories, affiliate_data)
    affiliate_html = build_affiliate_html(picks)

    if affiliate_html:
        normalized_html += "\n\n" + affiliate_html
        print(f"🛒 Added {len(picks)} affiliate products.")

    # 6️⃣ PUBLISH TO WORDPRESS
    wp = WordpressClient(WP_URL, WP_USER, WP_PASS)

    post_id = wp.create_post(
        title=topic,
        html_content=normalized_html,
        excerpt="",
        status="publish",
        categories=categories,
        featured_image_url=featured_image_url,
    )

    print(f"✅ Post published successfully! ID: {post_id}")


# -------------------------------------------------------------------
#  RUN
# -------------------------------------------------------------------
if __name__ == "__main__":
    main()
