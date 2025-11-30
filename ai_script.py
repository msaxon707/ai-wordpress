import os
import httpx
import json
import time
from affiliate_injector import load_affiliate_products, inject_affiliate_links
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from image_handler import get_featured_image_id
from wordpress_client import post_to_wordpress
from topic_generator import generate_topic
from category_detector import detect_category
from content_normalizer import normalize_content
from logger_setup import setup_logger

# === CONFIG ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

API_URL = "https://api.openai.com/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

logger = setup_logger()


# === AI Helper ===
def openai_chat(prompt, max_tokens=1500, temperature=0.7, retries=3, delay=10):
    """Send prompt to OpenAI with retries and return the text output."""
    payload = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    for attempt in range(1, retries + 1):
        try:
            response = httpx.post(API_URL, headers=HEADERS, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

        except Exception as e:
            logger.warning(f"⚠️ OpenAI request failed (Attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                logger.error("❌ OpenAI API failed after multiple attempts.")
                return None


# === Main AI Functions ===
def generate_article(topic):
    """Generate SEO-optimized article text that sells affiliate links naturally."""
    logger.info(f"[ai_script] Generating article for topic: {topic}")

    prompt = f"""
    Write a detailed, SEO-optimized blog post about "{topic}" for The Saxon Blog.
    The tone should be warm, helpful, and authentic — like a seasoned home decor
    and country lifestyle blogger who subtly includes affiliate links.

    STRUCTURE:
    - Intro paragraph: relatable story or observation.
    - 3–5 subheadings with practical advice or inspiration.
    - Include at least 2 internal links to relevant blog categories.
    - Include at least 2 external authoritative links (like Better Homes & Gardens, HGTV, etc.).
    - Naturally mention affiliate product ideas — e.g. “I love this rustic planter I found here...”
    - End with a short conclusion and friendly CTA (e.g. “Happy decorating!”).

    SEO GOALS:
    - Use relevant keywords naturally.
    - Include 1 primary keyword in the title and subheadings.
    - Keep sentences clear and easy to read.
    """

    article_text = openai_chat(prompt)
    if not article_text:
        logger.error("Failed to generate article text.")
        return None

    return normalize_content(article_text)


def generate_meta(topic, article_text):
    """Generate an SEO title and meta description for the article."""
    prompt = f"""
    Create an SEO-friendly title and meta description for this blog post:

    Topic: {topic}
    Article: {article_text[:800]}

    Return your response in JSON:
    {{
        "title": "string",
        "description": "string"
    }}
    """

    meta_raw = openai_chat(prompt, max_tokens=150)
    if not meta_raw:
        return topic, ""

    try:
        meta = json.loads(meta_raw)
        return meta.get("title", topic), meta.get("description", "")
    except Exception:
        logger.warning("⚠️ Failed to parse meta JSON. Using fallback title/desc.")
        return topic, ""


# === MAIN PUBLISHER ===
def main():
    logger.info("[ai_script] === AI WordPress AutoPublisher Started ===")

    # 1. Generate topic
    topic = generate_topic()
    if not topic:
        logger.error("❌ Could not generate topic. Exiting.")
        return

    # 2. Generate article text
    article_text = generate_article(topic)
    if not article_text:
        return

    # 3. Affiliate product integration
    static_products = load_affiliate_products()
    suggested = generate_product_suggestions(article_text)
    dynamic_products = create_amazon_links(suggested)
    all_products = dynamic_products + static_products

    article_with_links = inject_affiliate_links(article_text, all_products)

    # 4. Detect category
    category_id = detect_category(topic)
    logger.info(f"[ai_script] Detected category ID: {category_id}")

    # 5. Featured image
    featured_image_id = get_featured_image_id(topic)

    # 6. Generate SEO metadata
    seo_title, seo_description = generate_meta(topic, article_with_links)

    # 7. Publish to WordPress
    post_id = post_to_wordpress(
        title=seo_title,
        content=article_with_links,
        category_id=category_id,
        featured_media_id=featured_image_id,
        excerpt=seo_description,
    )

    if post_id:
        logger.info(f"✅ Successfully published post ID: {post_id}")
    else:
        logger.error("❌ Post failed to publish.")

    logger.info("[ai_script] === Cycle Complete — Sleeping until next cron ===")


if __name__ == "__main__":
    main()
