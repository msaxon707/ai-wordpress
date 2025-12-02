"""
topic_generator.py — Dynamically generates unique, niche-relevant blog post topics.
Compatible with OpenAI >= 1.0 and Coolify environment setup.
"""

import os
import json
import random
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, TOPIC_TEMPERATURE

DATA_DIR = "/app/data"
TOPIC_HISTORY_FILE = os.path.join(DATA_DIR, "topic_history.json")

client = OpenAI(api_key=OPENAI_API_KEY)

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
    """Load or create topic history file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(TOPIC_HISTORY_FILE):
        with open(TOPIC_HISTORY_FILE, "w") as f:
            json.dump([], f)
        return []
    try:
        with open(TOPIC_HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_topic_history(history):
    """Save list of used topics."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TOPIC_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def generate_topic():
    """Generate a brand-new unique topic."""
    history = load_topic_history()

    prompt = f"""
You are a creative blog topic generator for a country living, hunting, fishing, and outdoor lifestyle blog.

Create 5 new and original blog topics that would appeal to readers interested in:
- hunting, fishing, camping, cooking, country home decor, gifts, dogs, and outdoor life.
- Each topic should be unique, SEO-optimized, and engaging.
- Avoid repeating any of these topics:
{history[-100:]}  # last 100 topics for context
- Return ONLY a numbered list of 5 new topics, no explanations or extra text.
"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=TOPIC_TEMPERATURE,
            max_tokens=500
        )

        content = response.choices[0].message.content.strip()
        topics = [line.strip("1234567890. ").strip() for line in content.split("\n") if line.strip()]
        topics = [t for t in topics if t and t not in history]

        if not topics:
            print("[topic_generator] ♻️ All topics used. Resetting history...")
            save_topic_history([])  # Clear old history
            return generate_topic()

        new_topic = random.choice(topics)
        history.append(new_topic)
        save_topic_history(history)
        print(f"[topic_generator] ✅ New topic generated: {new_topic}")
        return new_topic

    except Exception as e:
        print(f"[topic_generator] ❌ Error generating topic: {e}")
        raise RuntimeError("Failed to generate new topics from OpenAI.") from e
