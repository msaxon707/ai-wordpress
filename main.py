import time
import argparse
from topic_generator import generate_topic
from ai_script import build_post
from config import POST_INTERVAL_HOURS
from logger_setup import setup_logger

logger = setup_logger()

def main(test_mode=False):
    logger.info("=== AI AutoPublisher Started ===")

    try:
        topic = generate_topic()
        logger.info(f"🧠 Topic Selected: {topic}")
        build_post(topic)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        if not test_mode:
            logger.info(f"⏱️ Sleeping for {POST_INTERVAL_HOURS} hour(s) before next post...")
            time.sleep(POST_INTERVAL_HOURS * 3600)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run one post and exit.")
    args = parser.parse_args()
    main(test_mode=args.test)
