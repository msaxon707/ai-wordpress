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


def clean_topic(raw_topic):
    """Extract title and description cleanly from AI topic output."""
    title_match = re.search(r'Title[:：]?\s*["“]?([^"\n]+)', raw_topic)
    desc_match = re.search(r'Description[:：]?\s*(.+)', raw_topic, re.DOTALL)

    title = title_match.group(1).strip() if title_match else raw_topic.strip()
    description = desc_match.group(1).strip() if desc_match else ""

    # Clean up markdown and weird symbols
    title = re.sub(r'[*#`>_\-]+', '', title)
    description = re.sub(r'[*#`>_\-]+', '', description)
    title = title.replace("\n", " ").strip()
    description = description.replace("\n", " ").strip()

    logger.info(f"🧠 Cleaned title: {title}")
    logger.info(f"📝 Description extracted: {description[:100]}...")

    return title, description


def generate_article(topic):
    """Use OpenAI to create a full SEO-optimized blog post."""
    logger.info(f"[ai_script] Generating article for topic: {topic}")
    prompt = f"""
    Write a long, friendly, SEO-optimized blog post titled: '{topic}'.
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
    article = normalize_content(completion.choices[0].message.content)
    article = re.sub(r'[*#`>_\-]+', '', article).strip()
    return article


def generate_meta(topic, article, description_hint=""):
    """Generate SEO title and meta description."""
    prompt = (
        f"Generate an SEO title and meta description for '{topic}'. "
        f"Use this as context: {description_hint[:200]} "
        "Respond in JSON format: {'title': '', 'description': ''}"
    )
    try:
        r = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=150,
        )
        raw = r.choices[0].message.content
        meta = json.loads(raw)
        return meta.get("title", topic), meta.get("description", description_hint)
    except Exception as e:
        logger.warning(f"[Meta] Failed JSON parse: {e}")
        return topic, description_hint


def build_post():
    """Generate and post a complete article."""
    try:
        logger.info("=== AI AutoPublisher Started ===")

        raw_topic = generate_topic()
        title, desc_hint = clean_topic(raw_topic)

        article = generate_article(title)
        suggested = generate_product_suggestions(article)
        amazon_links = create_amazon_links(suggested)
        article_with_links = inject_affiliate_links(article, amazon_links)

        category_id = detect_category(title)
        image_id = get_featured_image_id(title)
        seo_title, seo_desc = generate_meta(title, article_with_links, desc_hint)

        post_id = post_to_wordpress(
            title=seo_title,
            content=article_with_links,
            category_id=category_id,
            featured_media_id=image_id,
            excerpt=seo_desc,
        )

        if post_id:
            refresh_aioseo(post_id)

        logger.info(f"[ai_script] ✅ Post completed: {seo_title}")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
