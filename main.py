# main.py
import time
from config import Config
from topic_generator import generate_unique_topic
from ai_script import generate_article
from image_handler import generate_featured_image
from wordpress_client import create_post
from setup_directories import setup_directories
from requests.auth import HTTPBasicAuth
from logger_setup import setup_logger

logger = setup_logger()

def main_loop():
    setup_directories()
    wp_credentials = HTTPBasicAuth(Config.WP_USERNAME, Config.WP_APP_PASSWORD)

    while True:
        try:
            topic = generate_unique_topic()
            logger.info(f"🧠 Starting new post cycle for: {topic}")

            internal_links = [
                "https://thesaxonblog.com/farmhouse-decor-guide",
                "https://thesaxonblog.com/hunting-gear-tips"
            ]
            content, category, seo_meta = generate_article(topic, internal_links)

            featured_image_id = generate_featured_image(topic, wp_credentials, Config.WP_BASE_URL)

            create_post(
                seo_meta["title"],
                content,
                category,
                featured_image_id,
                seo_meta,
                Config.WP_BASE_URL,
                Config.WP_USERNAME,
                Config.WP_APP_PASSWORD,
            )

            logger.info("⏱️ Sleeping for 1 hour before next post...")
            time.sleep(3600)

        except Exception as e:
            logger.error(f"Critical error in main loop: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main_loop()
