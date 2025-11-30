import os
import httpx
import json
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


def generate_topic():
    """Generate a unique, SEO-friendly blog topic via OpenAI HTTP API."""
    history = load_history()

    prompt = (
        "Generate one unique, SEO-friendly blog topic about home decor, "
        "outdoor lifestyle, or country living. Avoid repetition. "
        "Respond only with the topic title."
    )

    payload = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "max_tokens": 100,
    }

    try:
        response = httpx.post(API_URL, headers=HEADERS, json=payload, timeout=60)
        response.raise_for_status()
        topic = response.json()["choices"][0]["message"]["content"].strip()

        # Avoid duplicates
        if topic in history:
            logger.warning("⚠️ Duplicate topic detected. Generating another...")
            return generate_topic()

        history.append(topic)
        save_history(history)
        logger.info(f"✅ New topic: {topic}")
        return topic

    except Exception as e:
        logger.error(f"Error generating topic: {e}")
        return None


if __name__ == "__main__":
    print(generate_topic())
