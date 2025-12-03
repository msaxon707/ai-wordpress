import re
from topic_generator import generate_topic
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from affiliate_injector import inject_affiliate_links
from wordpress_client import post_to_wordpress, get_featured_image_id, refresh_aioseo
from seo_meta import generate_meta
from category_detector import detect_category
from article_generator import generate_article
from logger_setup import setup_logger

logger = setup_logger()

def build_post():
    """Full pipeline: generate topic, article, products, image, SEO, and post to WordPress."""
    try:
        logger.info("=== AI AutoPublisher Started ===")

        # 🧠 Generate topic
        topic = generate_topic()

        # 🧹 Clean Markdown symbols and junk
        clean_topic = re.sub(r'[*#`>_\n]+', ' ', topic).strip()
        clean_topic = re.sub(r'\s+', ' ', clean_topic)

        logger.info(f"🧠 Clean topic selected: {clean_topic}")

        # ✍️ Generate article
        article = generate_article(clean_topic)

        # 🛒 Generate products and links
        suggested_products = generate_product_suggestions(article)
        links = create_amazon_links(suggested_products)

        # 💬 Inject affiliate links
        article_with_links = inject_affiliate_links(article, links)

        # 🏷️ Detect category
        category_id = detect_category(clean_topic)

        # 🖼️ Generate featured image
        featured_image_id = get_featured_image_id(clean_topic)

        # 🧾 Generate SEO title + description
        seo_title, seo_desc = generate_meta(clean_topic, article_with_links)

        # 📰 Publish post
        post_id = post_to_wordpress(
            title=seo_title,
            content=article_with_links,
            category_id=category_id,
            featured_media_id=featured_image_id,
            excerpt=seo_desc,
        )

        # 🔁 Refresh AIOSEO
        refresh_aioseo(post_id)

        logger.info(f"[ai_script] ✅ Post completed: {seo_title}")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
