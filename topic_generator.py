import os
import httpx
import json
import time
from logger_setup import setup_logger

# === CONFIG ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

API_URL = "https://api.openai.com/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

logger = setup_logger()
HISTORY_FILE = "data/topic_history.json"


# === Helper Functions ===
def load_history():
    """Load previously used topics to avoid duplicates."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []


def save_history(topics):
    """Save generated topics for deduplication."""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(topics, f, indent=2)


def generate_topic(max_retries=3, retry_delay=10):
    """
    Generate a unique SEO-friendly topic related to country living, home decor,
    and outdoor lifestyle. Retries automatically if API fails.
    """
    history = load_history()
    attempt = 0

    prompt = (
        "Generate one unique, SEO-friendly blog post topic related to "
        "home decor, outdoor living, or rustic country lifestyle. "
        "Make it engaging, descriptive, and never duplicate a topic "
        "you’ve used before. Respond with only the topic title."
    )

    payload = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 100
    }

    while attempt < max_retries:
        try:
            response = httpx.post(API_URL, headers=HEADERS, json=payload, timeout=60)
            response.raise_for_status()

            data = response.json()
            topic = data["choices"][0]["message"]["content"].strip()

            # Avoid duplicates
            if topic in history:
                logger.warning("⚠️ Duplicate topic detected. Retrying...")
                time.sleep(2)
                attempt += 1
                continue

            history.append(topic)
            save_history(history)
            logger.info(f"✅ New topic generated: {topic}")
            return topic

        except Exception as e:
            attempt += 1
            logger.error(f"Error generating topic (Attempt {attempt}/{max_retries}): {e}")
            time.sleep(retry_delay)

    logger.error("❌ Failed to generate topic after multiple retries.")
    return None


if __name__ == "__main__":
    print(generate_topic())
