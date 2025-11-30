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


def openai_chat(prompt, max_tokens=600, temperature=0.7, retries=3, delay=8):
    """Send chat prompt to OpenAI with retry logic."""
    payload = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    for attempt in range(1, retries + 1):
        try:
            response = httpx.post(API_URL, headers=HEADERS, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

        except Exception as e:
            logger.warning(f"⚠️ OpenAI product suggestion attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                logger.error("❌ OpenAI product suggestion failed after multiple retries.")
                return None


# === PRODUCT RECOMMENDER ===
def generate_product_suggestions(article_text):
    """
    Generate contextual product ideas based on the article text.
    The AI analyzes the content and recommends affiliate-suitable items.
    """
    logger.info("[ai_product_recommender] Generating AI-based product suggestions...")
    
    prompt = f"""
    Analyze the following blog article and suggest 3-5 affiliate product ideas
    that would naturally fit within it. Choose items that readers would likely
    be interested in buying based on the topic context.

    Article:
    {article_text[:2500]}

    Return your response in JSON as a list of objects:
    [
      {{"name": "Rustic Wall Shelf", "category": "Home Decor"}},
      {{"name": "Mason Jar Chandelier", "category": "Lighting"}}
    ]
    """

    suggestions_raw = openai_chat(prompt)
    if not suggestions_raw:
        return []

    try:
        suggestions = json.loads(suggestions_raw)
        logger.info(f"✅ AI suggested {len(suggestions)} relevant products.")
        return suggestions
    except Exception as e:
        logger.warning(f"⚠️ Failed to parse product suggestions JSON: {e}")
        return []


# === AMAZON LINK BUILDER ===
def create_amazon_links(products):
    """
    Converts AI product suggestions into simple Amazon affiliate-style links.
    Replace 'YOURTAG-20' with your actual Amazon Associates tag if desired.
    """
    logger.info("[ai_product_recommender] Creating Amazon-style links...")
    amazon_affiliate_tag = os.getenv("AMAZON_TAG", "YOURTAG-20")
    base_url = "https://www.amazon.com/s?k="

    links = []
    for product in products:
        if isinstance(product, dict) and "name" in product:
            query = product["name"].replace(" ", "+")
            link = f"{base_url}{query}&tag={amazon_affiliate_tag}"
            links.append({"name": product["name"], "link": link})

    logger.info(f"🔗 Created {len(links)} Amazon-style product links.")
    return links


if __name__ == "__main__":
    test_text = "This article discusses how to decorate a rustic farmhouse kitchen using reclaimed wood and cozy lighting."
    suggestions = generate_product_suggestions(test_text)
    print(create_amazon_links(suggestions))
