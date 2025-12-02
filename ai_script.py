import random
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from affiliate_injector import inject_affiliate_links
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from image_handler import get_featured_image_id
from wordpress_client import post_to_wordpress
from topic_generator import generate_topic
from category_detector import detect_category
from content_normalizer import normalize_content
from logger_setup import setup_logger

logger = setup_logger()
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_article(topic):
    """Use OpenAI to create a full SEO blog post."""
    logger.info(f"[ai_script] Generating article for topic: {topic}")
    prompt = f"""
    Write a long, friendly, SEO-optimized blog post about: {topic}.
    Tone: Country/outdoors expert giving real advice.
    Include practical examples, affiliate mentions, and tips.
    Avoid hashtags, use HTML for headings and lists.
    """
    completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=1200,
    )
    return normalize_content(completion.choices[0].message.content)

def generate_meta(topic, article):
    """Generate SEO title and meta description."""
    prompt = f"Generate an SEO title and meta description for '{topic}'. Respond JSON: {{'title': '', 'description': ''}}"
    try:
        r = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=120,
        )
        import json
        meta = json.loads(r.choices[0].message.content)
        return meta.get("title", topic), meta.get("description", "")
    except Exception as e:
        logger.warning(f"[Meta] Failed JSON parse: {e}")
        return topic, ""

def build_post():
    """Generate and post a complete article."""
    topic = generate_topic()
    article = generate_article(topic)

    # product links
    suggested = generate_product_suggestions(article)
    amazon_links = create_amazon_links(suggested)
    article_with_links = inject_affiliate_links(article, amazon_links)

    # category + image + meta
    category_id = detect_category(topic)
    image_id = get_featured_image_id(topic)
    title, desc = generate_meta(topic, article_with_links)

    post_to_wordpress(
        title=title,
        content=article_with_links,
        category_id=category_id,
        featured_media_id=image_id,
        excerpt=desc,
    )
    logger.info(f"[ai_script] ✅ Post completed: {title}")
