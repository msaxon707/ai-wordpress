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


def generate_article(title, description_hint=""):
    """Use OpenAI to create a long, SEO-optimized blog post from the title."""
    logger.info(f"[ai_script] Generating article for topic: {title}")
    prompt = f"""
    Write a detailed, SEO-optimized blog article titled "{title}".
    Tone: friendly and practical, like an outdoors or country living expert.
    Incorporate advice, examples, and affiliate mentions naturally.
    Use proper HTML for headings (<h2>, <h3>), lists (<ul>, <li>), and links.
    Avoid hashtags or markdown formatting.
    Expand on this description if useful: {description_hint[:250]}.
    """
    completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
        max_tokens=1500,
    )
    article = normalize_content(completion.choices[0].message.content)
    return article.strip()


def generate_meta(title, article, description_hint=""):
    """Generate SEO title and meta description."""
    prompt = (
        f"Generate an SEO title and meta description for '{title}'. "
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
        return meta.get("title", title), meta.get("description", description_hint)
    except Exception as e:
        logger.warning(f"[Meta] Failed JSON parse: {e}")
        return title, description_hint


def build_post():
    """Generate and publish a complete article."""
    try:
        logger.info("=== AI AutoPublisher Started ===")

        # Step 1: Generate and clean topic
        raw_topic = generate_topic()
        title, desc_hint = clean_topic(raw_topic)

        # Step 2: Write a full article based on the title
        article = generate_article(title, desc_hint)

        # Step 3: Generate affiliate suggestions and links
        suggested = generate_product_suggestions(article)
        amazon_links = create_amazon_links(suggested)
        article_with_links = inject_affiliate_links(article, amazon_links)

        # Step 4: Detect category, generate image, and SEO metadata
        category_id = detect_category(title)
        image_id = get_featured_image_id(title)
        seo_title, seo_desc = generate_meta(title, article_with_links, desc_hint)

        # Step 5: Publish to WordPress
        post_id = post_to_wordpress(
            title=seo_title,
            content=article_with_links,
            category_id=category_id,
            featured_media_id=image_id,
            excerpt=seo_desc,
        )

        # Step 6: Refresh AIOSEO if possible
        if post_id:
            refresh_aioseo(post_id)

        logger.info(f"[ai_script] ✅ Post completed successfully: {seo_title}")

    except Exception as e:
        logger.error(f"Unexpected error during post build: {e}")
