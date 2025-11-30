"""
topic_generator.py — Generates unique blog topics using OpenAI
for the Saxon Blog niche: hunting, outdoors, decor, recipes, gifts, etc.
"""

import json
import os
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, MAX_TOPIC_HISTORY

client = OpenAI(api_key=OPENAI_API_KEY)
HISTORY_FILE = "data/topic_history.json"

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
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_topic_history(history):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-MAX_TOPIC_HISTORY:], f, indent=2)


def generate_topic():
    """Generate a unique topic from OpenAI for the Saxon Blog."""
    history = load_topic_history()

    prompt = f"""
You are an expert content strategist for a blog about hunting, outdoors, decor, and country living.
Generate 5 fresh, unique blog post ideas that fit one or more of these main categories:

{', '.join(CATEGORIES)}

Each topic should:
- Be under 120 characters.
- Be engaging and specific.
- Avoid repeating recent themes.
- Sound natural, friendly, and human (not clickbait).

Return ONLY a JSON list of strings, no extra commentary.
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=400,
        response_format={"type": "json_object"}
    )

    try:
        result = json.loads(response.choices[0].message.content)
        topics = result.get("topics", [])
    except Exception:
        # fallback if OpenAI returns text instead of JSON
        text = response.choices[0].message.content.strip()
        topics = [line.strip("•- ") for line in text.split("\n") if line.strip()]

    # Filter out duplicates
    topics = [t for t in topics if t not in history]

    if not topics:
        raise RuntimeError("No new unique topics could be generated. Try increasing temperature or clearing history.")

    new_topic = topics[0]
    history.append(new_topic)
    save_topic_history(history)
    print(f"[topic_generator] ✅ New topic generated: {new_topic}")
    return new_topic
