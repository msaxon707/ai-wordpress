import os
import json
import random
import requests
import openai
import markdown
from datetime import datetime
from config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    WP_BASE_URL,
    WP_USERNAME,
    WP_APP_PASSWORD,
    POST_CACHE_FILE,
    CATEGORY_IDS,
    CATEGORY_KEYWORDS,
    ENABLE_LOGGING,
)
from image_handler import get_featured_image_id
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from affiliate_injector import load_affiliate_products, inject_affiliate_links


# ========== Helper Functions ==========

def log(msg):
    if ENABLE_LOGGING:
        print(f"[ai_script] {msg}")

def load_post_cache():
    """Load cache of previously posted titles."""
    if os.path.exists(POST_CACHE_FILE):
        with open(POST_CACHE_FILE, "r") as f:
            return json.load(f)
    return []

def save_post_cache(cache):
    """Save cache to file."""
    with open(POST_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def detect_category(title, content):
    """Determine category based on title/content keywords."""
    text = f"{title.lower()} {content.lower()}"
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(word in text for word in keywords):
            return CATEGORY_IDS.get(category)
    return CATEGORY_IDS["uncategorized"]

# ========== AI Content Generation ==========

import random

def generate_topic():
    """Generate diverse SEO-driven outdoor topics."""
    base_topics = [
        "hunting gear",
        "country lifestyle",
        "camping",
        "fishing",
        "deer season",
        "outdoor cooking",
        "dog training for hunting",
        "backcountry survival",
        "off-grid living",
        "rural DIY projects",
        "wildlife photography",
        "homesteading gear",
        "bushcraft skills",
        "trail food and meal prep",
    ]

    # Randomly combine one base + one SEO keyword
    modifiers = [
        "tips",
        "essentials",
        "mistakes to avoid",
        "gear review",
        "guide for beginners",
        "on a budget",
        "for families",
        "like a pro",
        "every outdoorsman should know",
    ]

    return f"{random.choice(base_topics)} {random.choice(modifiers)}"


def generate_article(prompt_topic):
    """Generate SEO article using OpenAI GPT model and auto-inject affiliate links."""
    import openai
    from ai_product_recommender import generate_product_suggestions, create_amazon_links
    from affiliate_injector import load_affiliate_products, inject_affiliate_links

    openai.api_key = OPENAI_API_KEY
    prompt = f"""
    You are a seasoned outdoors writer who creates SEO-optimized, persuasive, story-driven articles.
    Focus on topics related to {prompt_topic}.
    Make the content authentic, rich, and encourage readers to check recommended gear naturally.
    Avoid sounding like a sales pitch. Include practical insights and real-sounding field advice.
    """

    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200,
        temperature=1.0,
    )

    article_text = response.choices[0].message["content"]

    # ====== AI Product Recommender Integration ======
    # 1️⃣ Generate AI-based product suggestions from the article text
    product_names = generate_product_suggestions(article_text)
    dynamic_products = create_amazon_links(product_names)

    # 2️⃣ Load your static affiliate backup list (hybrid mode)
    static_products = load_affiliate_products()

    # 3️⃣ Merge them for the injector
    all_products = dynamic_products + static_products

    # 4️⃣ Inject contextual affiliate links into the article
    article_with_links = inject_affiliate_links(article_text, all_products)

    return article_with_links

article_text = response.choices[0].message["content"]

# ====== AI Product Recommender Integration ======
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from affiliate_injector import load_affiliate_products, inject_affiliate_links

# 1️⃣  Generate AI-based product suggestions from the article text
product_names = generate_product_suggestions(article_text)
dynamic_products = create_amazon_links(product_names)

# 2️⃣  Load your static affiliate backup list (hybrid mode)
static_products = load_affiliate_products()

# 3️⃣  Merge them for the injector
all_products = dynamic_products + static_products

# 4️⃣  Inject contextual affiliate links into the article
article_with_links = inject_affiliate_links(article_text, all_products)

return article_with_links

# ========== WordPress Posting ==========

def post_to_wordpress(title, content, category_id, featured_media_id=None):
    """Create a post on WordPress."""
    url = f"{WP_BASE_URL}/wp-json/wp/v2/posts"
    headers = {"Content-Type": "application/json"}
    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [category_id],
    }

    if featured_media_id:
        post_data["featured_media"] = featured_media_id

    response = requests.post(
        url,
        headers=headers,
        json=post_data,
        auth=(WP_USERNAME, WP_APP_PASSWORD),
    )

    if response.status_code not in [200, 201]:
        log(f"WordPress post failed: {response.status_code} {response.text}")
        return None

    post_id = response.json().get("id")
    log(f"Successfully posted to WordPress: {title} (ID: {post_id})")
    return post_id

# ========== Main Runner ==========

def main():
    log("=== AI WordPress Post Generation Started ===")

    cache = load_post_cache()
    products = load_affiliate_products()

    # Step 1: Generate topic + article
    topic = generate_topic()
    article = generate_article(topic)

    # Step 2: Derive title
    title = article.split("\n")[0].strip().replace("#", "")
    if any(title in c for c in cache):
        log("Duplicate detected — skipping post.")
        return

    # Step 3: Inject affiliate links inline
    # Convert Markdown-style text to HTML
    article_html = markdown.markdown(article)

   # Then inject affiliate links into the HTML version
    article_with_links = inject_affiliate_links(article_html, products)


    # Step 4: Detect category
    category_id = detect_category(title, article_with_links)
    log(f"Detected category ID: {category_id}")

    # Step 5: Fetch and upload featured image
    featured_id = get_featured_image_id(title)

    # Step 6: Post to WordPress
    post_id = post_to_wordpress(title, article_with_links, category_id, featured_id)

    # Step 7: Update cache
    if post_id:
        cache.append(title)
        save_post_cache(cache)

    log("=== Run complete. Safe to exit for cron. ===")

if __name__ == "__main__":
    main()
