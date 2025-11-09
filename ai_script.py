import os
import time
import random
import requests
import schedule
from datetime import datetime
from openai import OpenAI

# ========= ENVIRONMENT VARIABLES =========
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_URL = os.getenv("WP_URL")  # e.g. https://thesaxonblog.com/wp-json/wp/v2/posts
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")

# Default to cheaper model; you can override in Coolify with MODEL=gpt-4-turbo
MODEL = os.getenv("MODEL", "gpt-3.5-turbo")

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

AMAZON_TAG = "meganmcanespy-20"
SITE_BASE = os.getenv("SITE_BASE", "https://thesaxonblog.com")

client = OpenAI(api_key=OPENAI_API_KEY)

# ========= AMAZON & EXTERNAL LINKS =========
AMAZON_LINKS = {
    "hunting": [
        f"https://www.amazon.com/s?k=deer+hunting+gear&tag={AMAZON_TAG}",
        f"https://www.amazon.com/s?k=hunting+scope&tag={AMAZON_TAG}",
        f"https://www.amazon.com/s?k=hunting+boots&tag={AMAZON_TAG}",
    ],
    "fishing": [
        f"https://www.amazon.com/s?k=fishing+rod+combo&tag={AMAZON_TAG}",
        f"https://www.amazon.com/s?k=bass+fishing+lures&tag={AMAZON_TAG}",
    ],
    "dogs": [
        f"https://www.amazon.com/s?k=hunting+dog+training+collar&tag={AMAZON_TAG}",
        f"https://www.amazon.com/s?k=dog+crate+for+trucks&tag={AMAZON_TAG}",
    ],
    "recipes": [
        f"https://www.amazon.com/s?k=cast+iron+skillet&tag={AMAZON_TAG}",
        f"https://www.amazon.com/s?k=smoker+for+meat&tag={AMAZON_TAG}",
    ],
}

EXTERNAL_LINKS = {
    "hunting": [
        "https://www.outdoorlife.com/hunting/",
        "https://www.fieldandstream.com/hunting/",
    ],
    "fishing": [
        "https://www.outdoorlife.com/fishing/",
        "https://www.fieldandstream.com/fishing/",
    ],
    "dogs": [
        "https://www.akc.org/expert-advice/training/",
        "https://www.ukcdogs.com/hunting-dog-articles",
    ],
    "recipes": [
        "https://www.themeateater.com/cook",
        "https://www.allrecipes.com/",
    ],
}

# ========= TOPIC LISTS =========
topic_categories = {
    "hunting": [
        "Top deer hunting strategies for this season",
        "How to clean and store your hunting gear",
        "Best rifles and bows for new hunters",
    ],
    "fishing": [
        "Top bass fishing tips for beginners",
        "How to choose the perfect fishing spot",
        "Best bait and tackle for summer fishing",
    ],
    "dogs": [
        "Training your hunting dog to retrieve",
        "Best breeds for waterfowl hunting",
        "How to care for your hunting dog after a long day",
    ],
    "recipes": [
        "Easy venison chili recipe",
        "How to make smoked duck breast",
        "Simple campfire trout recipe for your next trip",
    ],
}

# ========= IMAGE HANDLER =========
def fetch_image(query: str) -> str | None:
    """Try Pexels first, then Unsplash as fallback."""
    # Pexels
    if PEXELS_API_KEY:
        try:
            r = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": PEXELS_API_KEY},
                params={"query": query, "per_page": 1},
                timeout=20,
            )
            if r.status_code == 200:
                photos = r.json().get("photos", [])
                if photos:
                    return photos[0]["src"]["large"]
        except Exception as e:
            print("⚠️ Pexels error:", e)

    # Unsplash fallback
    if UNSPLASH_ACCESS_KEY:
        try:
            r = requests.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": 1, "client_id": UNSPLASH_ACCESS_KEY},
                timeout=20,
            )
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    return results[0]["urls"]["regular"]
        except Exception as e:
            print("⚠️ Unsplash error:", e)

    return None

# ========= AI CONTENT CREATOR =========
def generate_content(topic: str, category: str) -> str | None:
    amazon_list = AMAZON_LINKS.get(category, [])
    external_list = EXTERNAL_LINKS.get(category, [])

    prompt = f"""
You are writing for The Saxon Blog, an outdoor lifestyle site about hunting, fishing, dogs, and wild game recipes.

Write a 700–900 word SEO-optimized article about:
"{topic}"

Category: {category}

Requirements:
- Use a clear H1-style title at the top.
- Use H2 and H3 subheadings.
- Keep paragraphs short (2–4 sentences).
- Naturally include at least ONE internal link to The Saxon Blog
  using a realistic URL like {SITE_BASE}/deer-hunting-tips/ or similar.
- Naturally include at least ONE authority external link from this list:
  {external_list}
- Naturally include at least ONE Amazon affiliate link from this list:
  {amazon_list}
  Use the full URL exactly as provided and work it into a helpful sentence.
- Tone: friendly, practical, helpful, and AdSense-safe.
- End with a short call-to-action inviting readers to explore more articles on The Saxon Blog.
Do NOT mention that you are an AI or that this is generated.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a professional SEO blog writer for an outdoor niche site."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1100,
        )
        return response.choices[0].message.content
    except Exception as e:
        print("⚠️ OpenAI error:", e)
        return None

# ========= WORDPRESS PUBLISHER =========
def post_to_wordpress(title: str, content: str, image_url: str | None, category: str) -> None:
    meta_description = content[:155].replace("\n", " ")
    slug = title.lower().replace(" ", "-")
    tags = ["hunting", "outdoors", "fishing", "dogs", "recipes", "adventure"]

    schema = f"""
<script type="application/ld+json">{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "datePublished": "{datetime.now().strftime('%Y-%m-%d')}",
  "author": {{
    "@type": "Person",
    "name": "The Saxon Blog"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "The Saxon Blog"
  }}
}}</script>
"""

    canonical = f'<link rel="canonical" href="{SITE_BASE}/{slug}/" />'

    full_content = f"{content}\n\n{schema}\n{canonical}"

    data = {
        "title": title,
        "slug": slug,
        "status": "publish",  # AUTO-PUBLISH
        "excerpt": meta_description,
        "content": full_content,
        "tags": tags,
    }

    # Note: featured_media_url may require a plugin or custom handling in WP.
    if image_url:
        data["featured_media_url"] = image_url

    try:
        r = requests.post(WP_URL, json=data, auth=(WP_USERNAME, WP_PASSWORD), timeout=30)
    except Exception as e:
        print("⚠️ Request to WordPress failed:", e)
        return

    if r.status_code == 201:
        body = r.json()
        link = body.get("link", "(no link)")
        print(f"✅ Published: {title} → {link}")
        log_published(title, link, category)
    else:
        print(f"❌ Error posting {title}: {r.status_code} - {r.text}")

# ========= LOGGING =========
def log_published(title: str, url: str, category: str) -> None:
    line = f"{datetime.now().isoformat()} | {category} | {title} | {url}\n"
    try:
        with open("published_log.txt", "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print("⚠️ Could not write to log file:", e)

# ========= TOPIC REFRESH (WEEKLY) =========
def refresh_topics() -> None:
    print("\n🔄 Refreshing topic list...")
    refresh_prompt = (
        "Generate 10 new SEO-friendly blog post titles for The Saxon Blog. "
        "Mix topics across hunting, fishing, hunting dogs, and wild game recipes. "
        "Each title under 10 words, catchy, and no numbering."
    )
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You create fresh SEO blog ideas for outdoor niches."},
                {"role": "user", "content": refresh_prompt},
            ],
            temperature=0.8,
            max_tokens=400,
        )
        raw = response.choices[0].message.content
        new_titles = [
            line.strip("-• ").strip()
            for line in raw.split("\n")
            if line.strip()
        ]
    except Exception as e:
        print("⚠️ Error refreshing topics:", e)
        return

    if not new_titles:
        print("⚠️ No new topics generated.\n")
        return

    chosen_category = random.choice(list(topic_categories.keys()))
    topic_categories[chosen_category].extend(new_titles)
    print(f"✨ Added {len(new_titles)} new topics to '{chosen_category}' category.\n")

# ========= TOPIC PICKER & BATCH RUN =========
def pick_random_topic() -> tuple[str, str]:
    category = random.choice(list(topic_categories.keys()))
    topic = random.choice(topic_categories[category])
    print(f"🎯 Selected category: {category} | Topic: {topic}")
    return topic, category

def run_batch() -> None:
    print(f"\n🕒 New post cycle: {datetime.now()}")
    topic, category = pick_random_topic()
    content = generate_content(topic, category)
    if not content:
        print("⚠️ Skipping post due to generation failure.")
        return

    image = fetch_image(topic)
    post_to_wordpress(topic, content, image, category)
    # Small delay for safety if you ever expand to multiple posts per run
    time.sleep(10)
    print("✅ Cycle complete.\n")

# ========= SCHEDULERS =========
# 1 post every hour → "fast" but still cheap with gpt-3.5-turbo
schedule.every().hour.do(run_batch)
# Refresh ideas once a week
schedule.every().sunday.at("08:00").do(refresh_topics)

print("🚀 Auto-publish system active for The Saxon Blog!")
print("🕓 Will publish 1 new post every hour and refresh topics weekly.\n")

# Run one immediately at startup
run_batch()

while True:
    schedule.run_pending()
    time.sleep(60)
