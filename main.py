"""
main.py — Main runner for AI autoposter (Coolify-friendly)
"""

import time
import argparse
from topic_generator import generate_topic
from ai_script import build_post
from config import POST_INTERVAL_HOURS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run a single test post.")
    args = parser.parse_args()

    print("=== AI AutoPublisher Started ===")

    if args.test:
        topic = generate_topic()
        build_post(topic)
        print("✅ Test post complete.")
        return

    while True:
        try:
            topic = generate_topic()
            build_post(topic)
            print("✅ Published new article successfully.")
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
        print(f"⏱️ Sleeping for {POST_INTERVAL_HOURS} hours before next post...")
        time.sleep(POST_INTERVAL_HOURS * 3600)


if __name__ == "__main__":
    main()
