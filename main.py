import time
import random
from ai_script import build_post
from logger_setup import setup_logger

logger = setup_logger()


def main():
    logger.info("=== 🌾 AI AutoPublisher Started ===")
    logger.info("This bot will automatically post articles every 45–75 minutes.")
    logger.info("You can stop it anytime with CTRL + C.\n")

    while True:
        try:
            logger.info("🧠 Starting new content generation cycle...")
            build_post()
            logger.info("✅ Post published successfully. Preparing for next cycle.")
        except Exception as e:
            logger.error(f"❌ Unexpected error in main loop: {e}")

        # Random delay between 45 and 75 minutes
        delay_minutes = random.randint(45, 75)
        delay_seconds = delay_minutes * 60
        logger.info(f"⏳ Sleeping for {delay_minutes} minutes before next post...")
        time.sleep(delay_seconds)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 AI AutoPublisher stopped manually by user.")
