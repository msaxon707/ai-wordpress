# ai_script.py
import os
import time
import random
import json
from datetime import datetime, date

import openai

from config import TOPIC_POOL
from image_handler import get_featured_image_url
from wordpress_client import create_wordpress_post

# --- Environment ---
WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")
AFFILIATE_TAG = os.getenv("AFFILIATE_TAG")

MODEL = os.getenv("Model", "gpt-3.5-turbo")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Safety: max posts per day (extra protection on top of 1/hour)
MAX_DAILY_POSTS = int(os.getenv("MAX_DAILY_POSTS", "12"))
USAGE_STATE_FILE = "usage_state.json"


def _load_usage_state():
    try:
        with open(USAGE_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"date": str(date.today()), "count": 0}


def _save_usage_state(state):
    try:
        with open(USAGE_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"⚠️ Could not save usage state: {e}")


def _can_post_today():
    """Return True if we are under the daily post limit."""
    state = _load_usage_state()
    today_str = str(date.today())

    if state.get("date") != today_str:
        state = {"date": today_str, "count": 0}

    if state["count"] >= MAX_DAILY_POSTS:
        print(
            f"{datetime.now()} ⛔ Daily post limit reached "
            f"({state['count']}/{MAX_DAILY_POSTS}). Skipping."
        )
        _save_usage_state(state)
        return False

    state["count"] += 1
    _save_usage_state(state)
    return True


def generate_post_content(topic: str):
    """Call OpenAI once to generate the blog body + focus keyword."""
    if not openai.api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in environment.")

    print(f"{datetime.now()} 🧠 Generating content for: {topic}")

    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a skilled outdoor lifestyle content writer. "
                    "Write friendly, practical, SEO-aware posts for hunting, "
                    "camping, dogs, and country living."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Write a detailed SEO blog post about '{topic}'. "
                    "Include an engaging intro, helpful tips, subheadings, "
                    "and a short conclusion. Keep it family-friendly. "
                    "Do NOT mention that you are an AI."
                ),
            },
        ],
        max_tokens=1000,
    )

    content = response.choices[0].message.content
    focus_keyword = topic.lower()
    return content, focus_keyword


def main():
    print(f"{datetime.now()} 🚀 Starting AI WordPress auto-poster...\n")

    if not (WP_URL and WP_USERNAME and WP_PASSWORD):
        print(
            f"{datetime.now()} ❌ Missing WordPress configuration "
            "(WP_URL / WP_USERNAME / WP_PASSWORD)."
        )
        return

    if not _can_post_today():
        return

    topic_entry = random.choice(TOPIC_POOL)
    topic = topic_entry["topic"]
    category = topic_entry.get("category")
    tags = topic_entry.get("tags", [])

    print(f"{datetime.now()} 🧠 Generating post for topic: {topic}")

    try:
        # Generate content
        content_html, focus_keyword = generate_post_content(topic)

        # Get featured image
        image_url, image_alt = get_featured_image_url(topic)
        if image_url:
            # Add tiny credit line for safety/attribution
            content_html += (
                '<p style="font-size:0.85em; color:#777;">'
                "Photo via Pexels/Unsplash</p>"
            )

        # Publish to WordPress
        post_id = create_wordpress_post(
            WP_URL,
            WP_USERNAME,
            WP_PASSWORD,
            title=topic.title(),
            content=content_html,
            image_url=image_url,
            image_alt=image_alt,
            affiliate_tag=AFFILIATE_TAG,
            focus_keyword=focus_keyword,
            category=category,
            tags=tags,
        )

        if post_id:
            print(f"{datetime.now()} 🎉 Post published successfully! ID: {post_id}")
        else:
            print(f"{datetime.now()} ❌ Failed to publish post for topic: {topic}")

    except Exception as e:
        print(f"{datetime.now()} ❌ Error during posting: {e}")


if __name__ == "__main__":
    # One post per hour for safety
    while True:
        main()
        print(f"{datetime.now()} ⏲ Sleeping for 1 hour...\n")
        time.sleep(3600)
