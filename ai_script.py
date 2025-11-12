import os
import time
import random
from datetime import datetime
import openai
from image_handler import get_featured_image_url
from wordpress_client import create_wordpress_post

# ✅ Load environment variables
WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
AFFILIATE_TAG = os.getenv("AFFILIATE_TAG")
MODEL = os.getenv("Model", "gpt-3.5-turbo")

openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Topics for AI blog generation
topics = [
    "duck hunting gear",
    "deer hunting tips",
    "training German shorthaired pointers",
    "homemade venison recipes",
    "family camping essentials",
    "outdoor photography for beginners",
    "best duck decoys 2025",
    "how to train a hunting dog"
]

# ✅ Generate SEO content using GPT
def generate_post_content(topic):
    print(f"{datetime.now()} 🧠 Generating content for: {topic}")
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a skilled outdoor lifestyle content writer."},
            {"role": "user", "content": f"Write a detailed SEO blog post about {topic}. Include helpful info, affiliate-friendly tone, and engaging introduction."}
        ],
        max_tokens=1000,
    )
    content = response.choices[0].message.content
    focus_keyword = topic.lower()
    return content, focus_keyword

# ✅ Main loop
def main():
    print(f"{datetime.now()} 🚀 Starting AI WordPress auto-poster...\n")

    topic = random.choice(topics)
    print(f"{datetime.now()} 🧠 Generating post for topic: {topic}")

    try:
        # Generate content
        content_html, focus_keyword = generate_post_content(topic)

        # Get featured image
        image_url, image_alt = get_featured_image_url(topic)

        # ✅ Post to WordPress with all arguments
        post_id = create_wordpress_post(
            WP_URL,
            WP_USERNAME,
            WP_PASSWORD,
            title=topic.title(),
            content=content_html,
            image_url=image_url,
            image_alt=image_alt,
            affiliate_tag=AFFILIATE_TAG,
            focus_keyword=focus_keyword
        )

        if post_id:
            print(f"{datetime.now()} 🎉 Post published successfully! ID: {post_id}")
        else:
            print(f"{datetime.now()} ❌ Failed to publish post for topic: {topic}")

    except Exception as e:
        print(f"{datetime.now()} ❌ Error during posting: {e}")

# ✅ Run once per loop (you can modify the sleep time)
if __name__ == "__main__":
    while True:
        main()
        time.sleep(3600)  # Wait 1 hour between posts