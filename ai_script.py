import os
import time
import random
from datetime import datetime
import openai

from config import TOPIC_POOL
from image_handler import get_featured_image_url
from wordpress_client import create_wordpress_post

WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")
AFFILIATE_TAG = os.getenv("AFFILIATE_TAG")
MODEL = os.getenv("Model", "gpt-3.5-turbo")

openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_post_content(topic):
    print(f"{datetime.now()} 🧠 Generating content for: {topic}")
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are an expert outdoor lifestyle writer."},
            {"role": "user", "content": f"Write a detailed SEO blog post about {topic}. Include headings and useful tips."}
        ],
        max_tokens=950,
    )
    content = response.choices[0].message.content
    return content


def main():
    print(f"{datetime.now()} 🚀 Starting AI WordPress auto-poster...\n")

    entry = random.choice(TOPIC_POOL)
    topic = entry["topic"]
    manual_category = entry.get("category")

    print(f"{datetime.now()} 🧠 Topic Selected: {topic}")

    try:
        content = generate_post_content(topic)

        image_url, image_alt, mime_type = get_featured_image_url(topic)

        post_id = create_wordpress_post(
            WP_URL,
            WP_USERNAME,
            WP_PASSWORD,
            title=topic.title(),
            content=content,
            image_url=image_url,
            image_alt=image_alt,
            mime_type=mime_type,
            affiliate_tag=AFFILIATE_TAG,
            category=manual_category,
        )

        if post_id:
            print(f"{datetime.now()} 🎉 Post Published! ID: {post_id}")
        else:
            print(f"{datetime.now()} ⚠️ Post skipped or failed.")

    except Exception as e:
        print(f"{datetime.now()} ❌ ERROR: {e}")


if __name__ == "__main__":
    while True:
        main()
        print(f"{datetime.now()} ⏳ Sleeping 1 hour...\n")
        time.sleep(3600)