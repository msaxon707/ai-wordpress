import os
import requests
import time
from openai import OpenAI

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")

# Use cheaper, faster model by default
MODEL = os.getenv("MODEL", "gpt-3.5-turbo")

client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------------  FUNCTIONS  ----------------------

def generate_content(topic):
    """Generate a ~400–600 word post (≈25¢ with GPT-4, ≈2¢ with GPT-3.5)."""
    prompt = (
        f"Write a concise, SEO-friendly blog post (400–600 words) about '{topic}'. "
        "Include an engaging intro, 2-3 short subheadings, and a closing paragraph."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a professional outdoor blog writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=700,          # cost guardrail
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print("⚠️  OpenAI error:", e)
        return None


def post_to_wordpress(title, content):
    """Create a draft post in WordPress."""
    data = {"title": title, "content": content, "status": "draft"}
    try:
        r = requests.post(WP_URL, json=data, auth=(WP_USERNAME, WP_PASSWORD), timeout=20)
        if r.status_code == 201:
            print(f"✅ Draft created: {title}")
        else:
            print(f"❌ WordPress error ({r.status_code}):", r.text)
    except Exception as e:
        print("⚠️  Request failed:", e)


# ----------------------  MAIN LOOP  ----------------------

if __name__ == "__main__":
    topics = [
        "Deer hunting tips for beginners",
        "Best deer hunting gear in 2025",
        "How to track deer effectively",
        "Essential clothing for cold weather hunts",
        "Safety basics for new hunters"
    ]

    # Limit to 3 posts per run
    for topic in topics[:3]:
        print(f"\n🦌 Generating: {topic}")
        content = generate_content(topic)
        if content:
            post_to_wordpress(topic, content)
        time.sleep(10)  # pause between requests to prevent API spikes

