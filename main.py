# main.py
import time
from logger_setup import setup_logger
from setup_directories import setup_directories
from topic_generator import generate_topic
from ai_script import generate_article
from wordpress_client import post_to_wordpress
from image_handler import generate_featured_image
from category_detector import detect_category
from affiliate_injector import load_affiliate_products, inject_affiliate_links
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from content_normalizer import normalize_content
from config import Config

logger = setup_logger()

def main():
    setup_directories()
    logger.info("=== AI AutoPublisher Started ===")

    while True:
        try:
            # Generate a new unique topic
            topic = generate_topic()
            logger.info(f"🧠 Topic Selected: {topic}")

            # Generate the article HTML
            article_html = generate_article(topic)
            article_html = normalize_content(article_html)

            # Load affiliate products
            static_products = load_affiliate_products()
            suggested = generate_product_suggestions(article_html)
            dynamic_products = create_amazon_links(suggested)
            all_products = dynamic_products + static_products

            # Inject affiliate links into the article
            article_with_links = inject_affiliate_links(article_html, all_products)

            # Detect category for the post
            category_id = detect_category(topic)
            logger.info(f"📂 Category Detected: {category_id}")

            # Generate featured image
            from requests.auth import HTTPBasicAuth
            wp_credentials = HTTPBasicAuth(Config.WP_USERNAME, Config.WP_APP_PASSWORD)
            featured_image_id = generate_featured_image(topic, wp_credentials, Config.WP_BASE_URL)

            # Publish to WordPress
            post_id = post_to_wordpress(
                title=topic,
                content=article_with_links,
                category_id=category_id,
                featured_media_id=featured_image_id,
                excerpt=f"A blog post about {topic}"
            )

            if post_id:
                logger.info(f"✅ Successfully published post ID {post_id}")
            else:
                logger.warning("⚠️ Post failed to publish.")

        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")

        # Wait 1 hour before generating the next post
        logger.info("⏱️ Sleeping for 1 hour before next post...")
        time.sleep(3600)

if __name__ == "__main__":
    main()
