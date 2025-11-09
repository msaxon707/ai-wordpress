import os
import requests
import random
import time
from datetime import datetime
from openai import OpenAI

# === CONFIGURATION ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_URL = os.getenv("WP_URL")  # e.g. https://thesaxonbelong.com/wp-json/wp/v2/posts
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4-turbo")

# === CATEGORY IDS ===
CATEGORY_IDS = {
    "dogs": 11,
    "deer season": 36,
    "hunting": 38,
    "recipes": 54,
    "fishing": 91,
    "outdoor living": 90,
    "survival-bushcraft": 92
}

# === TAGS BY CATEGORY ===
TAGS = {
    "hunting": ["deer hunting", "whitetail deer", "hunting tips", "gear", "outdoors", "The Saxon Blog"],
    "dogs": ["dog training", "hunting dogs", "canine health", "outdoors", "The Saxon Blog"],
    "recipes": ["wild game recipes", "outdoor cooking", "campfire meals", "The Saxon Blog"],
    "fishing": ["fishing gear", "bass fishing", "outdoors", "The Saxon Blog"],
    "outdoor living": ["gear reviews", "camping", "nature", "The Saxon Blog"],
    "survival-bushcraft": ["bushcraft", "survival skills", "wilderness", "The Saxon Blog"],
}

AFFILIATE_TAG = "meganmcanespy-20"

# === OPENAI CLIENT ===
client = OpenAI(api_key=OPENAI_API_KEY)


def detect_category(topic):
    topic_lower = topic.lower()
    if "recipe" in topic_lower:
        return "recipes"
    elif "dog" in topic_lower or "pet" in topic_lower:
        return "dogs"
    elif "fish" in topic_lower:
        return "fishing"
    elif "survival" in topic_lower or "bushcraft" in topic_lower:
        return "survival-bushcraft"
    elif "gear" in topic_lower or "camp" in topic_lower or "outdoor" in topic_lower:
        return "outdoor living"
    elif "deer" in topic_lower or "hunt" in topic_lower:
        return "hunting"
    else:
        return random.choice(list(CATEGORY_IDS.keys()))


def get_stock_image(topic):
    """Try Pexels first, then fallback to Unsplash."""
    headers = {"Authorization": PEXELS_API_KEY}
    r = requests.get(f"https://api.pexels.com/v1/search?query={topic}&per_page=1", headers=headers)
    if r.status_code == 200 and r.json()["photos"]:
        return r.json()["photos"][0]["src"]["medium"]
    else:
        unsplash = requests.get(f"https://source.unsplash.com/featured/?{topic}")
        return unsplash.url


def generate_content(topic):
    """Generate SEO-optimized article content."""
    prompt = (
        f"Write a detailed, SEO-optimized blog post about '{topic}' for The Saxon Blog. "
        "Make it between 700 and 900 words. Use engaging headings, bullet points, and short paragraphs. "
        "Include SEO keywords, external links to authoritative sources, and at least one internal link to thesaxonbelong.com. "
        "End with a call to action or reflection. Write in a friendly, knowledgeable tone."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a professional outdoor blog writer focused on SEO and affiliate content."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content


def insert_affiliate_links(content, category):
    """Insert Amazon affiliate links contextually."""
    if category == "hunting":
        link = f"https://www.amazon.com/s?k=hunting+gear&tag={AFFILIATE_TAG}"
    elif category == "dogs":
        link = f"https://www.amazon.com/s?k=dog+training+gear&tag={AFFILIATE_TAG}"
    elif category == "recipes":
        link = f"https://www.amazon.com/s?k=camping+cookware&tag={AFFILIATE_TAG}"
    elif category == "fishing":
        link = f"https://www.amazon.com/s?k=fishing+gear&tag={AFFILIATE_TAG}"
    else:
        link = f"https://www.amazon.com/s?k=outdoor+gear&tag={AFFILIATE_TAG}"

    return f"{content}\n\n🛒 Check out the latest {category} products on [Amazon]({link})."


def post_to_wordpress(title, content, category, image_url):
    """Publish a post to WordPress."""
    tags = TAGS.get(category, ["outdoors", "The Saxon Blog"])
    data = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [CATEGORY_IDS.get(category, 1)],
        "tags": tags,
        "featured_media_url": image_url  # Works with FIFU plugin
    }

    response = requests.post(WP_URL, json=data, auth=(WP_USERNAME, WP_PASSWORD))
    if response.status_code == 201:
        print(f"✅ Published: {title}")
    else:
        print(f"❌ Error posting {title}: {response.text}")


def main():
    topics = [
        "Deer hunting tips for beginners",
        "Best fishing lures for spring bass",
        "Homemade venison jerky recipe",
        "How to train your hunting dog for retrieves",
        "Top outdoor camping gear in 2025",
        "Wilderness survival skills everyone should know",
    ]

    random.shuffle(topics)

    for topic in topics:
        print(f"🦌 Generating post: {topic}")
        category = detect_category(topic)
        content = generate_content(topic)
        content = insert_affiliate_links(content, category)
        image_url = get_stock_image(topic)
        post_to_wordpress(topic, content, category, image_url)

        # Wait 3 hours between posts
        print("⏳ Waiting 3 hours before next post...")
        time.sleep(3 * 60 * 60)


if __name__ == "__main__":
    main()
