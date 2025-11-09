import os
import time
import random
import requests
import schedule
from datetime import datetime
from openai import OpenAI

# ========= CONFIG / CONSTANTS =========

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_URL = os.getenv("WP_URL")              # e.g. https://thesaxonblog.com/wp-json/wp/v2/posts
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")

# Default to cheaper model; override in env with MODEL=gpt-4-turbo if you want later
MODEL = os.getenv("MODEL", "gpt-3.5-turbo")

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

AMAZON_TAG = "meganmcanespy-20"
SITE_BASE = os.getenv("SITE_BASE", "https://thesaxonblog.com")

# Google tracking info (you already set these via plugin; here we just track config)
GA_MEASUREMENT_ID = "G-5W817F8MV3"
GSC_META_TAG = '<meta name="google-site-verification" content="5cQeMbFTq8Uqoows5LH_mN2jeEyfZluanwC_g_CTHP4" />'

START_TIME = time.time()
MAX_UPTIME_SECONDS = 24 * 60 * 60  # 24 hours

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

# ========= LOGGING =========

def log_event(message: str) -> None:
    line = f"{datetime.now().isoformat()} | EVENT | {message}\n"
    try:
        with open("published_log.txt", "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print("⚠️ Could not write event log:", e)

def log_published(title: str, url: str, category: str) -> None:
    line = f"{datetime.now().isoformat()} | PUBLISHED | {category} | {title} | {url}\n"
    try:
        with open("published_log.txt", "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print("⚠️ Could not write to published log:", e)

# ========= HEALTH / TRACKING CONFIG CHECK =========

def check_tracking_config() -> None:
    if not GA_MEASUREMENT_ID:
        print("⚠️ GA_MEASUREMENT_ID missing. Add Analytics to your site.")
        log_event("GA_MEASUREMENT_ID missing.")
    else:
        print(f"ℹ️ Using Google Analytics ID: {GA_MEASUREMENT_ID}")

    if not GSC_META_TAG:
        print("⚠️ GSC meta tag missing. Make sure Search Console is verified.")
        log_event("GSC_META_TAG missing.")
    else:
        print("ℹ️ Google Search Console meta tag configured (ensure it's in your site header).")

# ========= IMAGE HANDLER =========

def fetch_image(query: str) -> str | None:
    """Try Pexels first, then Unsplash as fallback."""
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
            log_event(f"Pexels error: {e}")

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
            log_event(f"Unsplash error: {e}")

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
- Start with a strong H1-style title at the top.
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
        log_event(f"OpenAI error: {e}")
        return None

# ========= WORDPRESS PUBLISHER =========

def post_to_wordpress(title: str, content: str, image_url: str | None, category: str) -> None:
    meta_description = content[:155].replace("\n", " ")
    slug = title.lower().replace(" ", "-")

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
  }},
  "mainEntityOfPage": "{SITE_BASE}/{slug}/"
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
        # You can add categories/tags by ID later if you want.
    }

    if image_url:
        # This may require a plugin that understands featured_media_url.
        data["featured_media_url"] = image_url

    try:
        r = requests.post(WP_URL, json=data, auth=(WP_USERNAME, WP_PASSWORD), timeout=30)
    except Exception as e:
        print("⚠️ Request to WordPress failed:", e)
        log_event(f"WordPress request error: {e}")
        return

    if r.status_code == 201:
        body = r.json()
        link = body.get("link", "(no link)")
        print(f"✅ Published: {title} → {link}")
        log_published(title, link, category)
    else:
        print(f"❌ Error posting {title}: {r.status_code} - {r.text}")
        log_event(f"WordPress error {r.status_code}: {r.text}")

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
        log_event(f"Topic refresh error: {e}")
        return

    if not new_titles:
        print("⚠️ No new topics generated.\n")
        log_event("No new topics generated in refresh.")
        return

    chosen_category = random.choice(list(topic_categories.keys()))
    topic_categories[chosen_category].extend(new_titles)
    print(f"✨ Added {len(new_titles)} new topics to '{chosen_category}' category.\n")
    log_event(f"Added {len(new_titles)} new topics to {chosen_category}.")

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
        log_event("Skipped post: generation failure.")
        return

    image = fetch_image(topic)
    post_to_wordpress(topic, content, image, category)
    time.sleep(5)  # short delay safety
    print("✅ Cycle complete.\n")

# ========= MAIN LOOP / WATCHDOG =========

def main_loop() -> None:
    check_tracking_config()
    log_event("Auto-publish system started.")

    # 1 post every 2 hours (adjust here if you want faster/slower)
    schedule.every(2).hours.do(run_batch)
    # Refresh ideas once a week
    schedule.every().sunday.at("08:00").do(refresh_topics)

    # Run once at startup
    run_batch()

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print("⚠️ Error in scheduler loop:", e)
            log_event(f"Scheduler loop error: {e}")
            time.sleep(60)  # backoff

        # 24h watchdog restart
        uptime = time.time() - START_TIME
        if uptime > MAX_UPTIME_SECONDS:
            msg = "Restarting after 24 hours of uptime (watchdog)."
            print(msg)
            log_event(msg)
            break

        time.sleep(60)

if __name__ == "__main__":
    main_loop()
