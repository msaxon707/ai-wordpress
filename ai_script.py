import time, random
from config import TOPIC_POOL, INTERVAL_MINUTES
from content_generator import generate_title_and_focus, generate_html_body
from image_handler import fetch_image
from wordpress_client import post_to_wordpress

def main():
    print("🚀 Auto-poster running for The Saxon Blog...")
    while True:
        item = random.choice(TOPIC_POOL)
        topic = item["topic"]
        category = item["category"]
        print(f"📝 Creating new post: {topic}")

        title, focus = generate_title_and_focus(topic)
        html = generate_html_body(topic, category)
        img_url, _ = fetch_image(topic)

        post_to_wordpress(title, html, category, img_url, focus)

        print(f"Sleeping {INTERVAL_MINUTES} minutes...\n")
        time.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    main()
