import os
import time
import random
import requests
from datetime import datetime
from openai import OpenAI
import schedule

# ========= ENV / CONSTANTS =========

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_URL = os.getenv("WP_URL")          # e.g. https://thesaxonblog.com/wp-json/wp/v2/posts
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")

# Default model: GPT-3.5-Turbo (cheaper)
MODEL = os.getenv("MODEL", "gpt-3.5-turbo")

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

SITE_BASE = os.getenv("SITE_BASE", "https://thesaxonblog.com")
AFFILIATE_TAG = "meganmcanespy-20"

# Your Google IDs (for info/logging only)
GA_MEASUREMENT_ID = "G-5W817F8MV3"
GSC_META_TAG = '<meta name="google-site-verification" content="5cQeMbFTq8Uqoows5LH_mN2jeEyfZluanwC_g_CTHP4" />'

START_TIME = time.time()
MAX_UPTIME_SECONDS = 24 * 60 * 60  # 24h watchdog

client = OpenAI(api_key=OPENAI_API_KEY)

# ========= WORDPRESS CATEGORY IDS =========

CATEGORY_IDS = {
    "dogs": 11,
    "deer season": 36,
    "hunting": 38,
    "recipes": 54,
    "fishing": 91,
    "outdoor living": 90,
    "survival-bushcraft": 92,
}

# ========= TOPIC LISTS (SEED) =========

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
        "How to care for your hunting dog after a long day outdoors",
    ],
    "recipes": [
        "Easy venison chili recipe",
        "How to make smoked duck breast at home",
        "Simple campfire trout recipe for your next trip",
    ],
    "outdoor living": [
        "Must-have camping gear for weekend trips",
        "How to set up a comfortable base camp",
        "Beginner guide to outdoor gear on a budget",
    ],
    "survival-bushcraft": [
        "Essential bushcraft skills for beginners",
        "How to build a shelter in the woods",
        "Fire starting techniques every hunter should know",
    ],
    "deer season": [
        "How to prep for deer season months in advance",
        "Scouting tips to find deer hotspots",
        "How to pattern deer movement before the opener",
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
        print("⚠️ Could not write published log:", e)

# ========= TRACKING CONFIG (INFO) =========

def check_tracking_config() -> None:
    if GA_MEASUREMENT_ID:
        print(f"ℹ️ Google Analytics ID: {GA_MEASUREMENT_ID}")
    else:
        print("⚠️ GA_MEASUREMENT_ID not set.")
        log_event("GA_MEASUREMENT_ID missing.")

    if GSC_META_TAG:
        print("ℹ️ GSC meta tag configured (must be in site header via plugin).")
    else:
        print("⚠️ GSC meta tag missing.")
        log_event("GSC_META_TAG missing.")

# ========= CATEGORY DETECTION =========

def detect_category(topic: str) -> str:
    t = topic.lower()
    if "recipe" in t or "chili" in t or "jerky" in t or "cook" in t:
        return "recipes"
    if "dog" in t or "pet" in t:
        return "dogs"
    if "fish" in t or "bass" in t or "trout" in t:
        return "fishing"
    if "survival" in t or "bushcraft" in t or "shelter" in t:
        return "survival-bushcraft"
    if "gear" in t or "camp" in t or "outdoor" in t:
        return "outdoor living"
    if "deer" in t or "season" in t or "rut" in t:
        return "deer season"
    if "hunt" in t:
        return "hunting"
    # fallback random
    return random.choice(list(topic_categories.keys()))

# ========= IMAGE HANDLER =========

def fetch_image(topic: str) -> str | None:
    """Try Pexels first, then Unsplash fallback."""
    if PEXELS_API_KEY:
        try:
            r = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": PEXELS_API_KEY},
                params={"query": topic, "per_page": 1},
                timeout=20,
            )
            if r.status_code == 200:
                photos = r.json().get("photos", [])
                if photos:
                    return photos[0]["src"]["large"]
        except Exception as e:
            print("⚠️ Pexels error:", e)
            log_event(f"Pexels error: {e}")

    # Unsplash simple fallback
    try:
        r = requests.get(f"https://source.unsplash.com/featured/?{topic}", timeout=20)
        if r.status_code == 200:
            return r.url
    except Exception as e:
        print("⚠️ Unsplash error:", e)
        log_event(f"Unsplash error: {e}")

    return None

# ========= AFFILIATE CTA =========

def build_affiliate_cta(category: str) -> str:
    if category == "hunting" or category == "deer season":
        query = "deer+hunting+gear"
    elif category == "dogs":
        query = "hunting+dog+training+gear"
    elif category == "recipes":
        query = "camping+cookware"
    elif category == "fishing":
        query = "fishing+gear"
    else:
        query = "outdoor+gear"

    link = f"https://www.amazon.com/s?k={query}&tag={AFFILIATE_TAG}"
    return f"\n\n🛒 **Gear Tip:** Want to upgrade your setup? Check out recommended {category} products on [Amazon]({link})."

# ========= AI CONTENT CREATOR =========

def generate_content(topic: str, category: str) -> str | None:
    external_hunting = [
        "https://www.outdoorlife.com/hunting/",
        "https://www.fieldandstream.com/hunting/",
    ]
    external_fishing = [
        "https://www.outdoorlife.com/fishing/",
        "https://www.fieldandstream.com/fishing/",
    ]
    external_dogs = [
        "https://www.akc.org/expert-advice/training/",
        "https://www.ukcdogs.com/hunting-dog-articles",
    ]
    external_recipes = [
        "https://www.themeateater.com/cook",
        "https://www.allrecipes.com/",
    ]
    external_survival = [
        "https://www.rei.com/learn/c/survival",
        "https://bushcraftusa.com/",
    ]
    external_outdoor = [
        "https://www.outsideonline.com/",
        "https://www.backpacker.com/",
    ]

    if category in ("hunting", "deer season"):
        external = external_hunting
    elif category == "fishing":
        external = external_fishing
    elif category == "dogs":
        external = external_dogs
    elif category == "recipes":
        external = external_recipes
    elif category == "survival-bushcraft":
        external = external_survival
    else:
        external = external_outdoor

    prompt = f"""
You are writing a blog post for The Saxon Blog, an outdoor lifestyle site about hunting, fishing, dogs, survival, and wild game recipes.

Topic: "{topic}"
Category: {category}

Write a **700–900 word**, SEO-optimized article that:
- Starts with a strong H1-style title on the first line.
- Uses H2 and H3 subheadings.
- Uses short paragraphs (2–4 sentences).
- Feels human, friendly, and practical.
- Is **AdSense-safe** (no graphic content, no hate, etc.).
- Naturally includes at least ONE internal link to The Saxon Blog using a URL like:
  {SITE_BASE}/deer-hunting-tips/  or a similar realistic slug.
- Naturally includes at least ONE external link to a credible site chosen from:
  {external}
- Is helpful for beginners and intermediate readers.

Do **not** mention that you are an AI or that this is generated. End with a short call-to-action inviting readers to explore more posts on The Saxon Blog.
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a professional SEO blog writer for an outdoor niche site."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1100,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print("⚠️ OpenAI error:", e)
        log_event(f"OpenAI error: {e}")
        return None

# ========= WORDPRESS POSTING =========

def post_to_wordpress(title: str, content: str, category: str, image_url: str | None) -> None:
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

    full_content = f"{content}{build_affiliate_cta(category)}\n\n{schema}\n{canonical}"

    data = {
        "title": title,
        "slug": slug,
        "status": "publish",  # auto-publish
        "excerpt": meta_description,
        "content": full_content,
        "categories": [CATEGORY_IDS.get(category, 1)],
    }

    # FIFU plugin: featured_media_url is understood as remote featured image
    if image_url:
        data["featured_media_url"] = image_url

    try:
        r = requests.post(WP_URL, json=data, auth=(WP_USERNAME, WP_PASSWORD), timeout=30)
    except Exception as e:
        print("⚠️ WordPress request failed:", e)
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
    prompt = (
        "Generate 10 new SEO-friendly blog post titles for The Saxon Blog. "
        "Mix topics across hunting, fishing, hunting dogs, survival/bushcraft, outdoor living, and wild game recipes. "
        "Each title under 10 words, catchy, and no numbering."
    )
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You create fresh SEO blog ideas for outdoor niches."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=400,
        )
        raw = resp.choices[0].message.content
        new_titles = [
            line.strip("-• ").strip()
            for line in raw.split("\n")
            if line.strip()
        ]
    except Exception as e:
        print("⚠️ Topic refresh error:", e)
        log_event(f"Topic refresh error: {e}")
        return

    if not new_titles:
        print("⚠️ No new topics generated.")
        log_event("No new topics generated in refresh.")
        return

    chosen_category = random.choice(list(topic_categories.keys()))
    topic_categories[chosen_category].extend(new_titles)
    print(f"✨ Added {len(new_titles)} new topics to '{chosen_category}'.")
    log_event(f"Added {len(new_titles)} new topics to {chosen_category}.")

# ========= PICK TOPIC & RUN BATCH =========

def pick_random_topic() -> tuple[str, str]:
    cat = random.choice(list(topic_categories.keys()))
    topic = random.choice(topic_categories[cat])
    # Let detection override if needed
    detected = detect_category(topic)
    return topic, detected

def run_batch() -> None:
    print(f"\n🕒 New post cycle: {datetime.now()}")
    topic, category = pick_random_topic()
    print(f"🎯 Topic: {topic} | Category: {category}")

    content = generate_content(topic, category)
    if not content:
        print("⚠️ Skipping post due to generation failure.")
        log_event("Skipped post: generation failure.")
        return

    image_url = fetch_image(topic)
    post_to_wordpress(topic, content, category, image_url)
    print("✅ Cycle complete.\n")

# ========= MAIN LOOP (SCHEDULER + WATCHDOG) =========

def main_loop() -> None:
    check_tracking_config()
    log_event("Auto-publish system started for The Saxon Blog.")

    # Post 1 article every 2 hours
    schedule.every(2).hours.do(run_batch)

    # Weekly topic refresh (Sunday 08:00)
    schedule.every().sunday.at("08:00").do(refresh_topics)

    # Run one immediately
    run_batch()

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print("⚠️ Error in scheduler loop:", e)
            log_event(f"Scheduler loop error: {e}")
            time.sleep(60)

        uptime = time.time() - START_TIME
        if uptime > MAX_UPTIME_SECONDS:
            msg = "Watchdog: exiting after 24h uptime to allow restart."
            print(msg)
            log_event(msg)
            break

        time.sleep(60)

if __name__ == "__main__":
    main_loop()
