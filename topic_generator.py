from openai import OpenAI
import os
import json
import random
import time
from logger_setup import setup_logger

logger = setup_logger()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
HISTORY_FILE = "data/topic_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-100:], f, indent=2)

def generate_topic():
    """Generate new unique topic avoiding duplicates."""
    for _ in range(3):
        try:
            history = load_history()
            prompt = (
                "Generate 10 creative and unique blog post ideas about "
                "country living, rustic decor, or outdoors. "
                "Avoid these recent topics: " + ", ".join(history[-20:])
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=1.0,
                max_tokens=400
            )

            ideas = [
                idea.strip("- ").strip()
                for idea in response.choices[0].message.content.split("\n")
                if idea.strip()
            ]
            new_topic = random.choice(ideas)
            if new_topic not in history:
                history.append(new_topic)
                save_history(history)
                logger.info(f"✅ New topic: {new_topic}")
                return new_topic
        except Exception as e:
            logger.error(f"Error generating topic: {e}")
            time.sleep(5)
    raise RuntimeError("Failed to generate topic after retries.")
