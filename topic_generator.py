"""
topic_generator.py — Dynamically generates unique, niche-relevant blog post topics.
Fully compatible with OpenAI >= 1.13 and Coolify environments.
"""

import os
import json
import random
from openai import OpenAI
from config import OPENAI_MODEL, TOPIC_TEMPERATURE

DATA_DIR = "/app/data"
TOPIC_HISTORY_FILE = os.path.join(DATA_DIR, "topic_history.json")

# ✅ Modern initialization (no proxy error)
client = OpenAI()

CATEGORIES = [
    "Hunting Tips & Tactics",
    "Hunting Gear & Guns",
    "Hunting Dogs & Training",
    "Fishing & Lakes",
    "Camping & Outdoor Adventures",
    "Country Recipes & Cooking",
    "Country Home Decor & Lifestyle",
    "Clothing, Boots & Camo",
    "Tools & Outdoor Equipment",
    "Gifts & Holiday Ideas",
    "Scouting & Trailing Deer",
    "Nature & Country Living"
]


def load_topic_history():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(TOPIC_HISTORY_FILE):
        with open(TOPIC_HISTORY_FILE, "w") as f:
            json.dump([], f)
    with open(TOPIC_HISTORY_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_topic_history(history):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TOPIC_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def generate_topic():
    """Generate a unique, fresh blog post topic."""
    history = load_topic_history()

    prompt = f"""
You are a creative content generator for a country lifestyle and outdoors blog.
Create 5 *brand-new* blog topics (SEO optimized) related to:

hunting, fishing, camping, cooking, home decor, country living, outdoor tools, gifts, and dogs.

Avoid duplicates of these recent topics:
{history[-50:]}

Each topic should be catchy, conversational, and relevant.
Only output a simple numbered list of 5 topics.
"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=TOPIC_TEMPERATURE,
            max_tokens=500,
        )
        content = response.choices[0].message.content.strip()
        topics = [t.strip("1234567890. ") for t in content.split("\n") if t.strip()]
        topics = [t for t in topics if t and t not in history]

        if not topics:
            print("[topic_generator] ♻️ No new topics. Clearing history...")
            save_topic_history([])
            return generate_topic()

        topic = random.choice(topics)
        history.append(topic)
        save_topic_history(history)
        print(f"[topic_generator] ✅ New topic generated: {topic}")
        return topic

    except Exception as e:
        print(f"[topic_generator] ❌ Error generating topic: {e}")
        raise RuntimeError("Failed to generate topic from OpenAI.") from e
