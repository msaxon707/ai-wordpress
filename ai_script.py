import os
import time
import random
import logging
import requests
import re
from datetime import datetime
from urllib.parse import quote_plus

from openai import OpenAI

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ---------- Environment ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_URL = os.getenv("WP_URL")  # e.g. https://thesaxonblog.com/wp-json/wp/v2/posts
WP_USERNAME = os.getenv("WP_USERNAME") or os.getenv("WORDPRESS_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD") or os.getenv("WORDPRESS_APP_PASSWORD")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
SITE_BASE = os.getenv("SITE_BASE", "https://thesaxonblog.com")
AFFILIATE_TAG = os.getenv("AFFILIATE_TAG", "meganmcanespy-20")

# Fixed model as requested
MODEL = "gpt-3.5-turbo"

# How often to post (minutes)
INTERVAL_MINUTES = int(os.getenv("INTERVAL_MINUTES", "180"))

if not OPENAI_API_KEY:
    logging.error("Missing OPENAI_API_KEY")
    raise SystemExit(1)

if not (WP_URL and WP_USERNAME and WP_PASSWORD):
    logging.error("Missing WP_URL or WP_USERNAME or WP_PASSWORD")
    raise SystemExit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- Categories / Topics ----------
CATEGORIES = {
    "dogs": 11,
    "deer-season": 36,
    "hunting": 38,
    "recipes": 54,
    "fishing": 91,
    "outdoor-living": 90,
    "survival-bushcraft": 92,
}

TOPIC_POOL = [
    # deer season / hunting
    {"category": "deer-season", "topic": "Morning vs evening deer hunts: what really works"},
    {"category": "hunting", "topic": "Best budget-friendly deer hunting gear that still performs"},
    {"category": "hunting", "topic": "How to pattern deer on pressured public land"},
    # dogs
    {"category": "dogs", "topic": "How to train your bird dog to retrieve reliably"},
    {"category": "dogs", "topic": "Off-season conditioning tips for hunting dogs"},
    # recipes
    {"category": "recipes", "topic": "Simple campfire trout recipe for your next trip"},
    {"category": "recipes", "topic": "Smoked duck breast at home: step-by-step guide"},
    # fishing
    {"category": "fishing", "topic": "Bank fishing tips for beginners"},
    {"category": "fishing", "topic": "Simple river fishing rigs that just work"},
    # outdoor living / gear
    {"category": "outdoor-living", "topic": "Essential gear for a comfortable hunting camp"},
    {"category": "outdoor-living", "topic": "Outdoor cooking setups for deer camp"},
    # survival / bushcraft
    {"category": "survival-bushcraft", "topic": "Basic bushcraft skills every hunter should know"},
    {"category": "survival-bushcraft", "topic": "Starting a fire in wet conditions: practical tips"},
]

AFFILIATE_KEYWORDS = {
    "deer-season": "deer hunting gear",
    "hunting": "hunting gear",
    "dogs": "hunting dog supplies",
    "recipes": "campfire cooking gear",
    "fishing": "fishing tackle",
    "outdoor-living": "camp gear",
    "survival-bushcraft": "survival gear",
}

PEXELS_QUERIES = {
    "deer-season": "whitetail deer hunting woods",
    "hunting": "hunter in camouflage forest",
    "dogs": "hunting dog in field",
    "recipes": "campfire cooking outdoors",
    "fishing": "fishing at lake",
    "outdoor-living": "camping tent forest",
    "survival-bushcraft": "bushcraft camp firewoods",
}

# ---------- Helpers ----------


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-") or "post"


def derive_focus_keyword(topic: str) -> str:
    # Simple heuristic: use a cleaned version of the topic
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", topic)
    return cleaned.lower().strip()


def extract_excerpt_from_html(html: str, max_words: int = 40) -> str:
    text = re.sub(r"<[^>]+>", " ", html)  # strip tags
    words = text.split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]) + "..."


def build_affiliate_cta(category_key: str) -> str:
    search_term = AFFILIATE_KEYWORDS.get(category_key, "outdoor gear")
    url = f"https://www.amazon.com/s?k={quote_plus(search_term)}&tag={AFFILIATE_TAG}"
    return f"""
<div class="affiliate-cta">
  <p><strong>Recommended gear:</strong> Want to upgrade your setup? Check out our favorite
    <a href="{url}" target="_blank" rel="nofollow sponsored noopener">Amazon picks</a> before your next trip.
  </p>
</div>
""".strip()


def fetch_pexels_image(category_key: str):
    """Return (image_url, alt_text) or (None, None)."""
    if not PEXELS_API_KEY:
        logging.warning("No PEXELS_API_KEY set; skipping image.")
        return None, None

    query = PEXELS_QUERIES.get(category_key, "outdoor hunting camp")
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": 1, "orientation": "landscape"},
            headers={"Authorization": PEXELS_API_KEY},
            timeout=15,
        )
        if resp.status_code != 200:
            logging.warning("Pexels error %s: %s", resp.status_code, resp.text[:200])
            return None, None
        data = resp.json()
        photos = data.get("photos") or []
        if not photos:
            logging.warning("Pexels returned no photos for query '%s'", query)
            return None, None
        photo = photos[0]
        src = photo.get("src") or {}
        image_url = src.get("large") or src.get("medium") or src.get("original")
        alt_text = photo.get("alt") or query
        return image_url, alt_text
    except Exception as e:
        logging.warning("Error talking to Pexels: %s", e)
        return None, None


def clean_html_body(html: str) -> str:
    # strip code fences and <html>/<body> wrappers if model adds them
    html = re.sub(r"`{3,}.*?\n", "", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"</?html[^>]*>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"</?body[^>]*>", "", html, flags=re.IGNORECASE)
    return html.strip()


# ---------- OpenAI Calls ----------


def generate_title_and_focus(topic: str):
    system_msg = (
        "You are an expert outdoor and hunting blogger writing for The Saxon Blog. "
        "Respond in JSON."
    )
    user_msg = f"""
Create a catchy SEO blog post title and a focus keyword for this topic:

"{topic}"

Return JSON ONLY in this exact format:
{{
  "title": "Your Title Here",
  "focus_keyword": "your main keyword phrase"
}}
"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.7,
    )
    content = resp.choices[0].message.content.strip()

    # Very simple JSON parsing without importing json (to keep script compact)
    title_match = re.search(r'"title"\s*:\s*"([^"]+)"', content)
    focus_match = re.search(r'"focus_keyword"\s*:\s*"([^"]+)"', content)

    if not title_match:
        # fallback: use topic
        title = topic.strip().capitalize()
    else:
        title = title_match.group(1).strip()

    if not focus_match:
        focus_keyword = derive_focus_keyword(topic)
    else:
        focus_keyword = focus_match.group(1).strip()

    return title, focus_keyword


def generate_body_html(topic: str, category_key: str) -> str:
    internal_links = f"""
- {SITE_BASE}/
- {SITE_BASE}/category/hunting/
- {SITE_BASE}/category/dogs/
- {SITE_BASE}/category/recipes/
- {SITE_BASE}/category/fishing/
- {SITE_BASE}/category/outdoor-living/
- {SITE_BASE}/category/survival-bushcraft/
""".strip()

    system_msg = (
        "You are a professional outdoor, hunting, fishing, dog training, and camp cooking writer. "
        "You write naturally, like a human, but still clear and structured for SEO."
    )

    user_msg = f"""
Write a 900–1100 word blog post for **The Saxon Blog** about:

"{topic}"

Requirements:
- Tone: expert, friendly, and conversational. Write like a real hunter or outdoor mom/dad talking to a friend.
- Audience: everyday hunters, anglers, dog owners, and camp cooks.
- Formatting:
  * Use HTML: <p>, <h2>, <h3>, <ul>, <li>, <strong>.
  * Do NOT include <html>, <head>, or <body> tags.
  * Do NOT include any code fences like ``` or ```html.
  * Do NOT say "here is your post."
  * Start with a short engaging <p> as an intro, then use <h2> and <h3> subheadings.
- SEO:
  * Naturally weave in long-tail keywords related to: {category_key} and "{topic}".
  * Include 1–2 internal links using these exact URLs where relevant:
{internal_links}
  * Include 1–2 external links to TRUSTED, non-competing sites (e.g. outdoor magazines, conservation orgs).
- Monetization:
  * Naturally mention that readers can check recommended gear on Amazon, but DO NOT include any Amazon URL.
  * Mention gear in a helpful, non-spammy way.
- Readability:
  * Use short paragraphs and scannable subheadings.
  * Avoid overly robotic or repetitive phrasing.

Return ONLY the HTML body content.
"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.8,
    )
    html = resp.choices[0].message.content
    return clean_html_body(html)


# ---------- WordPress ----------


def create_wordpress_post(
    title: str,
    slug: str,
    excerpt: str,
    body_html: str,
    category_key: str,
    image_url: str | None,
    image_alt: str | None,
    focus_keyword: str,
):
    category_id = CATEGORIES.get(category_key)
    if not category_id:
        logging.warning("Unknown category key %s, defaulting to hunting", category_key)
        category_id = CATEGORIES["hunting"]

    # Build CTA + simple Article schema
    cta_html = build_affiliate_cta(category_key)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    schema_html = f"""
<script type="application/ld+json">{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "datePublished": "{today}",
  "author": {{
    "@type": "Person",
    "name": "The Saxon Blog"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "The Saxon Blog"
  }},
  "mainEntityOfPage": "{SITE_BASE}/{slug}/"
}}</script>
""".strip()

    full_content = f"<h1>{title}</h1>\n{body_html}\n\n{cta_html}\n\n{schema_html}"

    meta = {}
    if image_url:
        meta["fifu_image_url"] = image_url
    if image_alt:
        meta["fifu_image_alt"] = image_alt
    if focus_keyword:
        # AIOSEO focus keyword (best effort)
        meta["_aioseo_focus_keyphrase"] = focus_keyword

    payload = {
        "title": title,
        "slug": slug,
        "excerpt": excerpt,
        "content": full_content,
        "status": "publish",
        "categories": [category_id],
    }
    if meta:
        payload["meta"] = meta

    logging.info("Publishing to WordPress: %s", title)
    resp = requests.post(
        WP_URL,
        json=payload,
        auth=(WP_USERNAME, WP_PASSWORD),
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        logging.error("Error publishing post: %s", resp.text[:500])
        return None

    data = resp.json()
    post_id = data.get("id")
    logging.info("✅ Published post %s: %s", post_id, title)
    return post_id


# ---------- Main Loop ----------


def main_loop():
    logging.info("Starting The Saxon Blog auto-publisher.")
    logging.info("Model: %s | Interval: %d minutes", MODEL, INTERVAL_MINUTES)

    while True:
        try:
            choice = random.choice(TOPIC_POOL)
            category_key = choice["category"]
            topic = choice["topic"]

            logging.info("🦌 Generating post in '%s' on topic: %s", category_key, topic)

            title, focus_keyword = generate_title_and_focus(topic)
            slug = slugify(title)
            body_html = generate_body_html(topic, category_key)
            excerpt = extract_excerpt_from_html(body_html)

            img_url, img_alt = fetch_pexels_image(category_key)

            create_wordpress_post(
                title=title,
                slug=slug,
                excerpt=excerpt,
                body_html=body_html,
                category_key=category_key,
                image_url=img_url,
                image_alt=img_alt,
                focus_keyword=focus_keyword,
            )
        except Exception as e:
            logging.exception("Error while generating post: %s", e)

        logging.info("Sleeping for %d minutes...", INTERVAL_MINUTES)
        time.sleep(INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main_loop()
