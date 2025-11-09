import os
import time
import random
import logging
import json
import urllib.parse
from datetime import datetime
import requests
from openai import OpenAI

# === Environment variables ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_URL = os.getenv("WP_URL")  # e.g. https://thesaxonblog.com/wp-json/wp/v2/posts
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")
MODEL = os.getenv("MODEL", "gpt-3.5-turbo")
INTERVAL_MINUTES = int(os.getenv("INTERVAL_MINUTES", "180"))
AMAZON_TAG = os.getenv("AMAZON_TAG", "meganmcanespy-20")
SITE_NAME = os.getenv("SITE_NAME", "The Saxon Blog")
WP_BASE_URL = os.getenv("WP_BASE_URL", "https://thesaxonblog.com")

if not all([OPENAI_API_KEY, WP_URL, WP_USERNAME, WP_PASSWORD]):
    raise RuntimeError("Missing required environment variables.")

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# === Category setup ===
CATEGORY_IDS = {
    "dogs": 11,
    "deer season": 36,
    "hunting": 38,
    "recipes": 54,
    "fishing": 91,
    "outdoor living": 90,
    "survival-bushcraft": 92,
}

CATEGORY_TOPICS = {
    "dogs": ["Best hunting dog breeds for family life", "How to train your bird dog to retrieve"],
    "deer season": ["Morning vs evening deer hunts: what really works", "How to pattern whitetails"],
    "hunting": ["Budget-friendly hunting gear that actually lasts", "Public land hunting tips"],
    "recipes": ["Easy campfire trout recipe", "One-pan venison skillet dinner"],
    "fishing": ["Bank fishing tips when you don’t own a boat", "Best baits and lures for small ponds"],
    "outdoor living": ["Beginner camping checklist for families", "Making your backyard wildlife-friendly"],
    "survival-bushcraft": ["Basic bushcraft skills every hunter should know", "Fire starting basics"],
}

IMAGE_URLS = {
    "dogs": ["https://thesaxonblog.com/wp-content/uploads/2025/11/german-shorthaired-pointer-attentively-watching-a-red.jpeg"],
    "deer season": ["https://thesaxonblog.com/wp-content/uploads/2025/11/pexels-photo-4467687.jpeg"],
    "hunting": ["https://thesaxonblog.com/wp-content/uploads/2025/11/pexels-photo-4047881.jpeg"],
    "recipes": ["https://thesaxonblog.com/wp-content/uploads/2025/11/pexels-photo-5081913.jpeg"],
    "fishing": ["https://thesaxonblog.com/wp-content/uploads/2025/11/pexels-photo-3153203.jpeg"],
    "outdoor living": ["https://thesaxonblog.com/wp-content/uploads/2025/11/pexels-photo-3321799.jpeg"],
    "survival-bushcraft": ["https://thesaxonblog.com/wp-content/uploads/2025/11/pexels-photo-3958883.jpeg"],
}

CATEGORY_ORDER = list(CATEGORY_IDS.keys())
_category_index = 0


def choose_category_and_topic():
    global _category_index
    name = CATEGORY_ORDER[_category_index % len(CATEGORY_ORDER)]
    _category_index += 1
    topic = random.choice(CATEGORY_TOPICS[name])
    return name, CATEGORY_IDS[name], topic


def pick_image_url(category_name):
    urls = IMAGE_URLS.get(category_name) or []
    return random.choice(urls) if urls else None


def build_affiliate_cta(keyword):
    q = urllib.parse.quote_plus(keyword or "outdoor gear")
    url = f"https://www.amazon.com/s?k={q}&tag={AMAZON_TAG}"
    return f'<div class="affiliate-cta"><p><strong>Recommended Gear:</strong> Want to upgrade your setup? <a href="{url}" target="_blank" rel="nofollow sponsored noopener">Check Amazon</a>.</p></div>'


def call_openai(topic, category):
    prompt = f"""
Write an expert yet natural outdoor blog post for "{SITE_NAME}" about "{topic}" in the {category} category.
Tone: conversational, confident, and AdSense-safe. 
Length: 900–1100 words.
Include subheadings and short, clear paragraphs.
Return valid JSON with:
"title", "excerpt", "content_html", "focus_keyword", and "amazon_keyword".
    """.strip()

    r = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You write like an experienced hunter, outdoorsman, and parent blogger."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1100,
    )
    try:
        return json.loads(r.choices[0].message.content)
    except:
        return {"title": topic, "excerpt": "", "content_html": r.choices[0].message.content, "focus_keyword": topic, "amazon_keyword": topic}


def create_wp_post(data, cat_id, cat_name):
    title = data["title"]
    body = data["content_html"]
    focus_keyword = data["focus_keyword"]
    amazon_keyword = data["amazon_keyword"]
    image_url = pick_image_url(cat_name)

    if image_url:
        body = f'<figure><img src="{image_url}" alt="{title}" loading="lazy" /></figure>\n' + body
    body += "\n\n" + build_affiliate_cta(amazon_keyword)

    meta = {
        "fifu_image_url": image_url or "",
        "_aioseo_focus_keyword": focus_keyword,
    }

    payload = {
        "title": title,
        "content": body,
        "excerpt": data["excerpt"],
        "status": "publish",
        "categories": [cat_id],
        "meta": meta,
    }

    r = requests.post(WP_URL, json=payload, auth=(WP_USERNAME, WP_PASSWORD))
    if r.status_code not in (200, 201):
        logger.error(f"WP error {r.status_code}: {r.text}")
        return
    pid = r.json().get("id")
    logger.info(f"✅ Published post {pid}: {title}")
    with open("published_log.txt", "a") as f:
        f.write(f"{datetime.utcnow().isoformat()}Z\t{pid}\t{title}\n")


def main():
    logger.info(f"Starting autopublisher for {SITE_NAME}")
    while True:
        try:
            cat, cat_id, topic = choose_category_and_topic()
            logger.info(f"🦌 Generating {cat}: {topic}")
            post = call_openai(topic, cat)
            create_wp_post(post, cat_id, cat)
        except Exception as e:
            logger.exception(e)
        time.sleep(INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()

