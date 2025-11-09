import os
import time
import random
import requests
from datetime import datetime, timedelta, timezone
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

# Tracking IDs (for info/logging – you already added these via plugins)
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

def detect_category(text: str) -> str:
    t = text.lower()
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
    if category in ("hunting", "deer season"):
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

# ========= AI CONTENT CREATOR (NEW POSTS) =========

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
You are writing a blog post for The Saxon Blog, an outdoor lifestyle site.

Topic: "{topic}"
Category: {category}

Write an **SEO-optimized article** (700–900 words) that:
- Uses proper HTML headings (<h1>, <h2>, <h3>)
- Includes short paragraphs and bullet points
- Contains at least ONE internal HTML link to The Saxon Blog (use a slug like <a href="{SITE_BASE}/deer-hunting-tips/">The Saxon Blog</a>)
- Contains at least ONE external HTML link from: {external}
- Never use Markdown links — only <a href="...">text</a> format
- Include a strong conclusion and stay AdSense-safe.
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a skilled SEO content writer who always uses HTML format."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1100,
        )
        content = resp.choices[0].message.content

        # Convert Markdown to HTML (backup)
        content = content.replace("[", "<a href=\"").replace("](", "\">").replace(")", "</a>")

        # Ensure at least one external link exists
        if "href=" not in content:
            fallback_link = random.choice(external)
            content += f'\n<p>For more info, visit <a href="{fallback_link}" target="_blank">this source</a>.</p>'

        return content
    except Exception as e:
        print("⚠️ OpenAI error:", e)
        log_event(f"OpenAI error (new post): {e}")
        return None

# ========= WORDPRESS POST (NEW POSTS) =========

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
        "status": "publish",
        "excerpt": meta_description,
        "content": full_content,
        "categories": [CATEGORY_IDS.get(category, 1)],
    }

    # FIFU plugin expects this to set featured image from remote URL
    if image_url:
        data["featured_media_url"] = image_url

    try:
        r = requests.post(WP_URL, json=data, auth=(WP_USERNAME, WP_PASSWORD), timeout=30)
    except Exception as e:
        print("⚠️ WordPress request failed:", e)
        log_event(f"WordPress request error (new post): {e}")
        return

    if r.status_code == 201:
        body = r.json()
        link = body.get("link", "(no link)")
        print(f"✅ Published: {title} → {link}")
        log_published(title, link, category)
    else:
        print(f"❌ Error posting {title}: {r.status_code} - {r.text}")
        log_event(f"WordPress error (new post) {r.status_code}: {r.text}")

# ========= EXISTING POSTS: FETCH & REWRITE =========

def fetch_existing_posts() -> list:
    """Fetch published posts from WordPress (first page, enough for ~15 posts)."""
    try:
        r = requests.get(
            WP_URL,
            params={"per_page": 20, "status": "publish"},
            auth=(WP_USERNAME, WP_PASSWORD),
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()
        else:
            print(f"⚠️ Failed to fetch posts: {r.status_code} {r.text}")
            log_event(f"Fetch existing posts failed: {r.status_code} {r.text}")
            return []
    except Exception as e:
        print("⚠️ Error fetching existing posts:", e)
        log_event(f"Error fetching existing posts: {e}")
        return []

def rewrite_post_content(post: dict) -> str | None:
    original_html = post.get("content", {}).get("rendered", "")
    title = post.get("title", {}).get("rendered", "(Untitled)")
    combined_text = f"{title}\n{original_html}"
    category = detect_category(combined_text)

    prompt = f"""
You are rewriting an existing WordPress blog post for The Saxon Blog.

Goals:
- Keep the same main topic and intent as the original.
- Improve readability, heading structure (H2/H3), and SEO.
- Keep it AdSense-safe.
- Include at least one internal link to The Saxon Blog (e.g. {SITE_BASE}/deer-hunting-tips/ or similar).
- Include at least one external link to a credible outdoor/recipe/training source relevant to the topic.
- Add a short concluding call-to-action inviting readers to explore more on The Saxon Blog.

Return ONLY the full HTML content to be stored directly in WordPress (no explanations outside the HTML).

Original HTML content:
{original_html}
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert SEO editor for outdoor blogs."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=1100,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print("⚠️ OpenAI error (rewrite):", e)
        log_event(f"OpenAI error (rewrite): {e}")
        return None

def update_existing_post(post_id: int, new_html: str) -> None:
    post_url = WP_URL.rstrip("/") + f"/{post_id}"
    data = {"content": new_html}

    try:
        r = requests.post(post_url, json=data, auth=(WP_USERNAME, WP_PASSWORD), timeout=30)
    except Exception as e:
        print(f"⚠️ Error updating post {post_id}:", e)
        log_event(f"Error updating post {post_id}: {e}")
        return

    if r.status_code in (200, 201):
        print(f"♻️ Updated existing post ID {post_id}")
        log_event(f"Updated existing post ID {post_id}")
    else:
        print(f"⚠️ Failed to update post {post_id}: {r.status_code} {r.text}")
        log_event(f"Failed to update post {post_id}: {r.status_code} {r.text}")

def optimize_existing_posts(max_to_optimize: int = 5) -> None:
    print("\n🔎 Checking existing posts for SEO rewrite...")
    posts = fetch_existing_posts()
    if not posts:
        print("No posts fetched; skipping optimization.")
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    optimized_count = 0

    for post in posts:
        if optimized_count >= max_to_optimize:
            break

        modified_str = post.get("modified_gmt") or post.get("modified")
        if not modified_str:
            continue

        try:
            # WordPress format: "YYYY-MM-DDTHH:MM:SS"
            modified_dt = datetime.fromisoformat(modified_str.replace("Z", "")).replace(tzinfo=timezone.utc)
        except Exception:
            continue

        if modified_dt >= cutoff:
            # Skip posts updated within last 7 days
            continue

        post_id = post.get("id")
        title = post.get("title", {}).get("rendered", "(Untitled)")
        print(f"♻️ Rewriting old post ID {post_id}: {title}")

        new_html = rewrite_post_content(post)
        if not new_html:
            print("⚠️ Skipping this post due to rewrite failure.")
            continue

        update_existing_post(post_id, new_html)
        optimized_count += 1
        time.sleep(5)  # small delay between rewrites

    if optimized_count == 0:
        print("✅ No older posts needed optimization (or all were updated recently).")
        log_event("Optimize existing posts: none updated.")
    else:
        print(f"✅ Optimized {optimized_count} older posts this run.")
        log_event(f"Optimized {optimized_count} older posts this run.")

# ========= TOPIC REFRESH (WEEKLY) =========

def refresh_topics() -> None:
    print("\n🔄 Refreshing topic list...")
    prompt = (
        "Generate 10 new SEO-friendly blog post titles for The Saxon Blog. "
        "Mix topics across hunting, fishing, hunting dogs, survival/bushcraft, outdoor living, deer season, and wild game recipes. "
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

# ========= PICK TOPIC & RUN BATCH (NEW POSTS) =========

def pick_random_topic() -> tuple[str, str]:
    cat = random.choice(list(topic_categories.keys()))
    topic = random.choice(topic_categories[cat])
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

    # 1) At startup, clean up / improve up to 5 older posts (skip last 7 days)
    optimize_existing_posts(max_to_optimize=5)

    # 2) Post 1 new article every 2 hours
    schedule.every(2).hours.do(run_batch)

    # 3) Weekly topic refresh (Sunday 08:00)
    schedule.every().sunday.at("08:00").do(refresh_topics)

    # 4) Daily SEO touch-up for older posts at 03:30 (optional, small batch)
    schedule.every().day.at("03:30").do(optimize_existing_posts)

    # Run one new post immediately
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

