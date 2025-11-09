import os
import time
import random
import requests
from datetime import datetime, timedelta, timezone
from openai import OpenAI
import schedule

# ========= ENV / CONSTANTS =========

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_URL = os.getenv("WP_URL")          # e.g. https://thesaxonbelong.com/wp-json/wp/v2/posts
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")

MODEL = os.getenv("MODEL", "gpt-3.5-turbo")  # default: gpt-3.5-turbo

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

SITE_BASE = os.getenv("SITE_BASE", "https://thesaxonbelong.com")
AFFILIATE_TAG = "meganmcanespy-20"

GA_MEASUREMENT_ID = "G-5W817F8MV3"
GSC_META_TAG = '<meta name="google-site-verification" content="5cQeMbFTq8Uqoows5LH_mN2jeEyfZluanwC_g_CTHP4" />'

START_TIME = time.time()
MAX_UPTIME_SECONDS = 24 * 60 * 60  # 24 hours

client = OpenAI(api_key=OPENAI_API_KEY)

# ========= CATEGORY IDS =========

CATEGORY_IDS = {
    "dogs": 11,
    "deer season": 36,
    "hunting": 38,
    "recipes": 54,
    "fishing": 91,
    "outdoor living": 90,
    "survival-bushcraft": 92,
}

# ========= AMAZON LINKS =========
# Later you can paste real product URLs here.
# For now it falls back to Amazon search pages with your tag.

AMAZON_PRODUCT_LINKS = {
    "hunting": [],
    "fishing": [],
    "dogs": [],
    "recipes": [],
    "outdoor living": [],
    "survival-bushcraft": [],
    "deer season": [],
}

AMAZON_SEARCH_QUERIES = {
    "hunting": "deer+hunting+gear",
    "deer season": "hunting+equipment",
    "dogs": "hunting+dog+supplies",
    "recipes": "cast+iron+cookware",
    "fishing": "fishing+gear",
    "outdoor living": "camping+gear",
    "survival-bushcraft": "survival+tools",
}


def choose_amazon_link(category: str) -> str:
    products = AMAZON_PRODUCT_LINKS.get(category, [])
    if products:
        return random.choice(products)
    query = AMAZON_SEARCH_QUERIES.get(category, "outdoor+gear")
    return f"https://www.amazon.com/s?k={query}&tag={AFFILIATE_TAG}"


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
        print("Could not write event log:", e)


def log_published(title: str, url: str, category: str) -> None:
    line = f"{datetime.now().isoformat()} | PUBLISHED | {category} | {title} | {url}\n"
    try:
        with open("published_log.txt", "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print("Could not write published log:", e)

# ========= INFO / CHECKS =========

def check_tracking_config() -> None:
    if GA_MEASUREMENT_ID:
        print(f"GA ID: {GA_MEASUREMENT_ID}")
    else:
        log_event("GA_MEASUREMENT_ID missing.")
    if GSC_META_TAG:
        print("GSC tag configured.")
    else:
        log_event("GSC_META_TAG missing.")

# ========= CATEGORY DETECTION =========

def detect_category(text: str) -> str:
    t = text.lower()
    if any(x in t for x in ["recipe", "chili", "jerky", "cook"]):
        return "recipes"
    if "dog" in t or "pet" in t:
        return "dogs"
    if "fish" in t or "bass" in t or "trout" in t:
        return "fishing"
    if "survival" in t or "bushcraft" in t or "shelter" in t:
        return "survival-bushcraft"
    if "gear" in t or "camp" in t or "outdoor" in t:
        return "outdoor living"
    if "rut" in t or "season" in t or "deer season" in t:
        return "deer season"
    if "deer" in t or "hunt" in t:
        return "hunting"
    return random.choice(list(topic_categories.keys()))

# ========= IMAGE HANDLING =========

def fetch_image(topic: str) -> str | None:
    # Try Pexels first
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
            print("Pexels error:", e)
            log_event(f"Pexels error: {e}")

    # Fallback: Unsplash
    try:
        r = requests.get(f"https://source.unsplash.com/featured/?{topic}", timeout=20)
        if r.status_code == 200:
            return r.url
    except Exception as e:
        print("Unsplash error:", e)
        log_event(f"Unsplash error: {e}")
    return None

# ========= AFFILIATE CTA =========

def build_affiliate_cta(category: str) -> str:
    url = choose_amazon_link(category)
    return f"""
<div class="affiliate-cta">
  <p><strong>Recommended Gear:</strong> Want to upgrade your setup? Check out our favorite
  <a href="{url}" target="_blank" rel="nofollow">Amazon {category} picks</a> before your next trip.</p>
</div>
"""

# ========= AI CONTENT: NEW POSTS (INCOME-FOCUSED) =========

def generate_content(topic: str, category: str) -> str | None:
    external_sources = {
        "hunting": ["https://www.outdoorlife.com/hunting/", "https://www.fieldandstream.com/hunting/"],
        "deer season": ["https://www.outdoorlife.com/deer-hunting/", "https://www.nrahlf.org/articles/deer-hunting/"],
        "fishing": ["https://www.outdoorlife.com/fishing/", "https://www.fieldandstream.com/fishing/"],
        "dogs": ["https://www.akc.org/expert-advice/training/", "https://www.ukcdogs.com/hunting-dog-articles"],
        "recipes": ["https://www.themeateater.com/cook", "https://www.allrecipes.com/"],
        "survival-bushcraft": ["https://bushcraftusa.com/", "https://www.rei.com/learn/c/survival"],
        "outdoor living": ["https://www.outsideonline.com/", "https://www.backpacker.com/"],
    }
    externals = external_sources.get(category, external_sources["hunting"])

    prompt = f"""
You are a professional content creator for a monetized outdoor blog called The Saxon Blog.

Your goals:
- Attract search traffic (SEO).
- Keep readers on the page longer (short paragraphs, strong structure).
- Encourage ad impressions and affiliate clicks in a natural, non-spammy way.

Write a 700–900 word blog post in HTML about:
"{topic}" (category: {category})

Requirements:
- Use <h1> for the main title at the top, then <h2> and <h3> for sections.
- Use <p> for all paragraphs (2–4 sentences each).
- Include at least ONE internal link to The Saxon Blog, e.g.
  <a href="{SITE_BASE}/deer-hunting-tips/">The Saxon Blog</a>
- Include at least ONE external link to one of these: {externals}
- Naturally mention 2–3 pieces of gear with strong buying intent language
  (e.g. "best budget", "top-rated", "worth the upgrade")
  but do NOT fabricate prices.
- Include a short comparison-style section (e.g. "Top 3 gear picks for beginners").
- Use ONLY HTML <a href="..."> links (no Markdown).
- Be AdSense-safe and family friendly.
- End with a call to action to explore more articles on The Saxon Blog.

Return only the HTML for the body of the article.
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a skilled SEO and affiliate content writer for a hunting/outdoors blog. "
                        "You always write clean, monetization-aware HTML."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1100,
        )
        content = resp.choices[0].message.content

        # Just in case it sneaks in Markdown links
        content = content.replace("](", "\">").replace("[", "<a href=\"").replace(")", "</a>")

        # Fallback: ensure at least one link
        if "href=" not in content:
            fallback = random.choice(externals)
            content += f'<p>For more info, check out <a href="{fallback}" target="_blank" rel="nofollow">this resource</a>.</p>'

        return content
    except Exception as e:
        print("OpenAI error (new content):", e)
        log_event(f"OpenAI error (new content): {e}")
        return None

# ========= POST TO WORDPRESS (NEW) – WITH FIFU IMAGE =========

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

    # We let FIFU handle showing the featured image; no <img> HTML needed in content
    full_content = f"{content}\n{build_affiliate_cta(category)}\n\n{schema}\n{canonical}"

    data = {
        "title": title,
        "slug": slug,
        "status": "publish",
        "excerpt": meta_description,
        "content": full_content,
        "categories": [CATEGORY_IDS.get(category, 1)],
    }

    # Tell FIFU which image URL to use as the featured image
    if image_url:
        data.setdefault("meta", {})["fifu_image_url"] = image_url

    try:
        r = requests.post(WP_URL, json=data, auth=(WP_USERNAME, WP_PASSWORD), timeout=30)
    except Exception as e:
        print("WordPress request failed (new):", e)
        log_event(f"WordPress request error (new): {e}")
        return

    if r.status_code == 201:
        body = r.json()
        link = body.get("link", "(no link)")
        print(f"✅ Published: {title} -> {link}")
        log_published(title, link, category)
    else:
        print(f"❌ Error posting {title}: {r.status_code} - {r.text}")
        log_event(f"WordPress error (new) {r.status_code}: {r.text}")

# ========= EXISTING POSTS: FETCH & REWRITE (INCOME-FOCUSED) =========

def fetch_existing_posts() -> list:
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
            log_event(f"Fetch posts failed: {r.status_code} {r.text}")
            return []
    except Exception as e:
        print("⚠️ Error fetching posts:", e)
        log_event(f"Error fetching posts: {e}")
        return []


def rewrite_post_content(post: dict):
    original_html = post.get("content", {}).get("rendered", "")
    title = post.get("title", {}).get("rendered", "(Untitled)")
    combined_text = f"{title}\n{original_html}"
    category = detect_category(combined_text)

    external_sources = {
        "hunting": ["https://www.outdoorlife.com/hunting/", "https://www.fieldandstream.com/hunting/"],
        "deer season": ["https://www.outdoorlife.com/deer-hunting/", "https://www.nrahlf.org/articles/deer-hunting/"],
        "fishing": ["https://www.outdoorlife.com/fishing/", "https://www.fieldandstream.com/fishing/"],
        "dogs": ["https://www.akc.org/expert-advice/training/", "https://www.ukcdogs.com/hunting-dog-articles"],
        "recipes": ["https://www.themeateater.com/cook", "https://www.allrecipes.com/"],
        "survival-bushcraft": ["https://bushcraftusa.com/", "https://www.rei.com/learn/c/survival"],
        "outdoor living": ["https://www.outsideonline.com/", "https://www.backpacker.com/"],
    }
    externals = external_sources.get(category, external_sources["hunting"])

    prompt = f"""
You are rewriting an existing monetized blog post for The Saxon Blog.

Title: "{title}"
Category: {category}

Goals:
- Keep the same main topic and overall message.
- Improve SEO (clear headings, keywords, internal links).
- Improve monetization: naturally encourage readers to consider outdoor gear or tools, without sounding spammy.
- Increase readability and time-on-page.

Rewrite the post in HTML that:
- Uses <h2> and <h3> for sections (assume the theme handles <h1>).
- Uses <p> for paragraphs (2–4 sentences each).
- Includes at least ONE internal link to The Saxon Blog, e.g.
  <a href="{SITE_BASE}/deer-hunting-tips/">The Saxon Blog</a>
- Includes at least ONE external link to one of: {externals}
- Mentions 2–3 types of gear that could reasonably be recommended (no prices).
- Has a small comparison-style section (e.g. comparing gear types).
- Uses ONLY <a href="..."> links (no Markdown).
- Ends with a short call to action for readers to explore more posts on The Saxon Blog.

Return only the updated HTML body.

Original HTML:
{original_html}
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert SEO + affiliate editor for an outdoor blog. "
                        "You rewrite posts to boost search traffic and revenue while staying helpful and natural."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=1100,
        )
        new_html = resp.choices[0].message.content

        new_html = new_html.replace("](", "\">").replace("[", "<a href=\"").replace(")", "</a>")

        if "href=" not in new_html:
            fallback = random.choice(externals)
            new_html += f'<p>Learn more from <a href="{fallback}" target="_blank" rel="nofollow">this trusted resource</a>.</p>'

        return new_html, category
    except Exception as e:
        print("⚠️ OpenAI error (rewrite):", e)
        log_event(f"OpenAI error (rewrite): {e}")
        return None, None


def update_existing_post(post: dict, new_body_html: str, category: str, image_url: str | None) -> None:
    post_id = post.get("id")
    slug = post.get("slug", "")
    title = post.get("title", {}).get("rendered", "(Untitled)")

    schema = f"""
<script type="application/ld+json">{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "dateModified": "{datetime.now().strftime('%Y-%m-%d')}",
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

    full_content = f"{new_body_html}\n{build_affiliate_cta(category)}\n\n{schema}\n{canonical}"

    post_url = WP_URL.rstrip("/") + f"/{post_id}"
    data = {"content": full_content}

    if image_url:
        data.setdefault("meta", {})["fifu_image_url"] = image_url

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
    print("\n🔎 Checking existing posts for SEO/monetization rewrite...")
    posts = fetch_existing_posts()
    if not posts:
        print("No posts fetched; skipping optimization.")
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    optimized = 0

    for post in posts:
        if optimized >= max_to_optimize:
            break

        modified_str = post.get("modified_gmt") or post.get("modified")
        if not modified_str:
            continue
        try:
            modified_dt = datetime.fromisoformat(modified_str.replace("Z", "")).replace(tzinfo=timezone.utc)
        except Exception:
            continue

        if modified_dt >= cutoff:
            continue  # skip posts updated in last 7 days

        post_id = post.get("id")
        title = post.get("title", {}).get("rendered", "(Untitled)")
        print(f"♻️ Rewriting old post ID {post_id}: {title}")

        new_html, category = rewrite_post_content(post)
        if not new_html or not category:
            print("⚠️ Skipping post due to rewrite failure.")
            continue

        image_url = None
        if post.get("featured_media", 0) == 0:
            image_url = fetch_image(title)

        update_existing_post(post, new_html, category, image_url)
        optimized += 1
        time.sleep(5)

    if optimized == 0:
        print("✅ No older posts needed optimization.")
        log_event("Optimize existing posts: none updated.")
    else:
        print(f"✅ Optimized {optimized} older posts this run.")
        log_event(f"Optimized {optimized} older posts this run.")

# ========= TOPIC REFRESH =========

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
        log_event("No new topics generated.")
        return

    chosen_category = random.choice(list(topic_categories.keys()))
    topic_categories[chosen_category].extend(new_titles)
    print(f"✨ Added {len(new_titles)} new topics to '{chosen_category}'.")
    log_event(f"Added {len(new_titles)} new topics to {chosen_category}.")

# ========= NEW POST SCHEDULER =========

def pick_random_topic():
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
        print("⚠️ Skipping post: generation failure.")
        log_event("Skipped post: generation failure.")
        return

    image_url = fetch_image(topic)
    post_to_wordpress(topic, content, category, image_url)
    print("✅ New post cycle complete.\n")

# ========= MAIN LOOP =========

def main_loop() -> None:
    check_tracking_config()
    log_event("Auto-publish system started for The Saxon Blog.")

    # At startup: tidy up to 5 old posts
    optimize_existing_posts(max_to_optimize=5)

    # New post every 2 hours
    schedule.every(2).hours.do(run_batch)

    # Weekly new topics
    schedule.every().sunday.at("08:00").do(refresh_topics)

    # Daily small SEO/monetization touch-up
    schedule.every().day.at("03:30").do(optimize_existing_posts)

    # Run one new post immediately
    run_batch()

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print("⚠️ Scheduler error:", e)
            log_event(f"Scheduler error: {e}")
            time.sleep(60)

        uptime = time.time() - START_TIME
        if uptime > MAX_UPTIME_SECONDS:
            msg = "Watchdog: exiting after 24h uptime."
            print(msg)
            log_event(msg)
            break

        time.sleep(60)


if __name__ == "__main__":
    main_loop()