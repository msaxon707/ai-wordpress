
import time
_last_call_time = 0
_min_interval = 5  # seconds between OpenAI calls
_retry_limit = 3   # maximum retries before giving up

import random
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


def clean_topic_text(topic: str):
    """Extract a clean title and description from AI's verbose topic text."""
    title = topic
    description = ""
    if "Title:" in topic or "Blog Topic:" in topic:
        try:
            # Extract title between quotes if available
            if '"' in topic:
                title = topic.split('"')[1]
            else:
                title = topic.split(":")[-1].strip()

            # Try to extract description part
            if "Description" in topic:
                description = topic.split("Description")[-1].replace(":", "").strip()
        except Exception:
            pass

    return title.strip(), description.strip()


def generate_article(topic):
    """Use OpenAI to create a full SEO blog post."""
    logger.info(f"[ai_script] Generating article for topic: {topic}")
    prompt = f"""
    Write a detailed, SEO-optimized blog post about: {topic}.
    Tone: friendly, country lifestyle expert.
    Include headings, lists, and real examples.
    Use HTML for structure (<h2>, <ul>, <li>).
    Naturally mention related gear, cooking tips, and outdoor themes.
    """
    completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=1200,
    )
    return normalize_content(completion.choices[0].message.content)


def generate_meta(topic, article):
    """Generate a concise SEO title and meta description."""
    prompt = f"""
    Based on the following topic and article, generate a short SEO-optimized title and meta description.
    Topic: {topic}
    Article excerpt: {article[:500]}
    Respond in JSON like this:
    {{
      "title": "SEO-friendly title",
      "description": "Compelling short meta description under 150 characters"
    }}
    """
    try:
        r = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=150,
        )
        meta = json.loads(r.choices[0].message.content)
        return meta.get("title", topic), meta.get("description", "")
    except Exception as e:
        logger.warning(f"[Meta] Failed JSON parse: {e}")
        return topic, ""


def build_post():
    """Generate and post a complete article."""
    topic = generate_topic()
    title, desc = clean_topic_text(topic)

    article = generate_article(title)
    suggested = generate_product_suggestions(article)
    amazon_links = create_amazon_links(suggested)
    article_with_links = inject_affiliate_links(article, amazon_links)

    category_id = detect_category(title)
    image_id = get_featured_image_id(title)
    seo_title, seo_desc = generate_meta(title, article_with_links)

    post_id = post_to_wordpress(
        title=seo_title,
        content=article_with_links,
        category_id=category_id,
        featured_media_id=image_id,
        excerpt=seo_desc or desc,
    )

    if post_id:
        refresh_aioseo(post_id)
        logger.info(f"[ai_script] ✅ Post completed successfully: {seo_title}")
    else:
        logger.error("[ai_script] ❌ Post failed to publish.")
