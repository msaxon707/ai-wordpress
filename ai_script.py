import os
import time
from wordpress_client import create_wordpress_post
from content_generator import generate_blog_post
from image_handler import get_featured_image_url

# Environment variables from Coolify / .env
WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")
MODEL = os.getenv("Model", "gpt-3.5-turbo")
AFFILIATE_TAG = os.getenv("AFFILIATE_TAG", "")
SITE_BASE = os.getenv("SITE_BASE", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

def main():
    print("🚀 Starting AI WordPress auto-poster...")
    topics = [
        "duck hunting gear",
        "campfire breakfast ideas",
        "training german shorthaired pointers",
        "best outdoor family activities",
        "deer season prep guide"
    ]

    for topic in topics:
        print(f"\n🧠 Generating post for topic: {topic}")

        # Generate content (title, focus keyword, HTML body)
        title, focus, content_html = generate_blog_post(topic)

        # Get featured image from image_handler
        image_url = get_featured_image_url(topic)
        image_alt = topic


        # Create and post to WordPress
  post_id = create_wordpress_post(
    WP_URL,
    WP_USERNAME,
    WP_PASSWORD,
    title,
    content_html,
    image_url,
    image_alt,
    affiliate_tag=AFFILIATE_TAG,
    focus_keyword=focus_keyword
)

        if post_id:
            print(f"✅ Successfully posted: {title} (Post ID: {post_id})")
        else:
            print(f"⚠️ Failed to post: {title}")

        time.sleep(5)  # small pause between posts


if __name__ == "__main__":
    main()
