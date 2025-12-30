
import time
_last_call_time = 0
_min_interval = 5  # seconds between OpenAI calls
_retry_limit = 3   # maximum retries before giving up

import os
import json
import random
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, TOPIC_TEMPERATURE, DATA_DIR
from logger_setup import setup_logger

logger = setup_logger()
client = OpenAI(api_key=OPENAI_API_KEY)

HISTORY_FILE = os.path.join(DATA_DIR, "topic_history.json")

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-50:], f)  # keep last 50 for memory control

def generate_topic():
    """Generate a new, niche-relevant topic avoiding duplicates."""
    history = load_history()
    logger.info("🧠 Generating fresh topic with OpenAI...")

    prompt = """
    You are a creative content generator for a country lifestyle and outdoors blog.
    The blog covers hunting, country home decor, fishing, camping, cooking, and gift ideas.
    Generate one unique, engaging blog topic that fits these themes.
    Avoid repeating past ideas. Keep it SEO-friendly and natural.
    """

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=TOPIC_TEMPERATURE,
        max_tokens=120,
    )

    topic = response.choices[0].message.content.strip().strip('"')
    if topic in history:
        raise RuntimeError("Duplicate topic detected — retry later.")

    history.append(topic)
    save_history(history)
    logger.info(f"✅ New topic generated: {topic}")
    return topic
