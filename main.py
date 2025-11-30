import os
import time
from ai_script import generate_article, generate_meta
from topic_generator import generate_topic
from affiliate_injector import load_affiliate_products, inject_affiliate_links
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from image_handler import get_featured_image_id
from wordpress_client import post_to_wordpress
from category_detector import detect_category
from logger_setup import setup_logger

logger = setup_logger()


def publish_post_cycle():
    """Runs one full AI autopublishing cycle."""
    logger.info("=== AI AutoPublisher Started ===")

    # 1️⃣ Generate topic
    topic = generate_topic()
    if not topic:
        logger.error("❌ Failed to generate topic.")
        return

    logger.info(f"🧠 Topic Selected: {topic}")

    # 2️⃣ Generate article
    article_text = generate_article(topic)
    if not article_text:
        logger.error("❌ Failed to generate article.")
        return

    # 3️⃣ Affiliate integration
    static_products = load_affiliate_products()
    suggested_products = generate_product_suggestions(article_text)
    dynamic_products = create_amazon_links(suggested_products)
    all_products = dynamic_products + static_products

    article_with_links = inject_affiliate_links(article_text, all_products)
    logger.info(f"🔗 Inserted {len(all_products)} affiliate links.")

    # 4️⃣ Detect category
    category_id = detect_category(topic)
    logger.info(f"📂 Category Detected: {category_id}")

    # 5️⃣ Generate featured image
    featured_image_id = get_featured_image_id(topic)

    # 6️⃣ SEO metadata
    seo_title, seo_description = generate_meta(topic, article_with_links)
    logger.info(f"🧾 SEO Meta Generated: {seo_title}")

    # 7️⃣ Publish to WordPress
    try:
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
            logger.error("❌ WordPress post failed.")
    except Exception as e:
        logger.error(f"❌ Unexpected error while publishing: {e}")

    logger.info("=== Cycle Complete ===")


def main():
    """Runs autopublishing loop every 1 hour."""
    while True:
        try:
            publish_post_cycle()
        except Exception as e:
            logger.error(f"⚠️ Unexpected error in main loop: {e}")
        logger.info("⏱️ Sleeping for 1 hour before next post...")
        time.sleep(3600)


if __name__ == "__main__":
    main()
