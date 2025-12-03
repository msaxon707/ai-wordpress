import random
import re
import json
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from affiliate_injector import inject_affiliate_links
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from image_handler import get_featured_image_id
from wordpress_client import post_to_wordpress, refresh_aioseo
from topic_generator import generate_topic
from category_detector import detect_category
from content_normalizer import normalize_content
from logger_setup import setup_logger

logger = setup_logger()
client = OpenAI(api_key=OPENAI_API_KEY)


def generate_article(topic):
    """Use OpenAI to create a full SEO-optimized blog post."""
    logger.info(f"[ai_script] Generating article for topic: {topic}")

    prompt = f"""
    Write a long, friendly, SEO-optimized blog post about: {topic}.
    Tone: Country/outdoors expert giving real advice.
    Include practical examples, affiliate mentions, and tips.
    Avoid hashtags. Use valid HTML for headings, lists, and links.
    """

    completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=1200,
    )

    article = completion.choices[0].message.content
    article = normalize_content(article)

    # 🧹 Clean any leftover markdown or weird symbols
    article = re.sub(r'[*#`_>]+', '', article)
    article = article.replace("\n\n", "\n").strip()

    return article


def generate_meta(topic, article):
    """Generate SEO title and meta description."""
    prompt = (
        f"Generate a concise SEO title and meta description for '{topic}'. "
        f"Respond in JSON only, format: {{'title': '...', 'description': '...'}}"
    )
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=150,
        )

        raw = response.choices[0].message.content
        meta = json.loads(raw)

        title = meta.get("title", topic)
        desc = meta.get("description", "")

        return title, desc
    except Exception as e:
        logger.warning(f"[Meta] Failed JSON parse: {e}")
        return topic, ""


def build_post():
    """Generate and post a complete article."""
    try:
        logger.info("=== AI AutoPublisher Started ===")

        # 🧠 Step 1: Generate topic
        topic = generate_topic()

        # 🧹 Clean markdown / symbols from topic
        clean_topic = re.sub(r'[*#`>_\n]+', ' ', topic).strip()
        clean_topic = re.sub(r'\s+', ' ', clean_topic)
        logger.info(f"🧠 Clean topic selected: {clean_topic}")

        # 📝 Step 2: Generate article content
        article = generate_article(clean_topic)

        # 🛒 Step 3: Add affiliate links
        suggested = generate_product_suggestions(article)
        amazon_links = create_amazon_links(suggested)
        article_with_links = inject_affiliate_links(article, amazon_links)

        # 🏷️ Step 4: Determine category
        category_id = detect_category(clean_topic)

        # 🖼️ Step 5: Get or generate featured image
        image_id = get_featured_image_id(clean_topic)
        if not image_id:
            logger.warning("⚠️ No image was uploaded; continuing without featured image.")

        # 🧾 Step 6: Create SEO metadata
        title, desc = generate_meta(clean_topic, article_with_links)

        # 📰 Step 7: Publish to WordPress
        post_id = post_to_wordpress(
            title=title,
            content=article_with_links,
            category_id=category_id,
            featured_media_id=image_id,
            excerpt=desc,
        )

        # 🔁 Step 8: Refresh SEO (All in One SEO)
        if post_id:
            refresh_aioseo(post_id)

        logger.info(f"[ai_script] ✅ Post completed: {title}")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
