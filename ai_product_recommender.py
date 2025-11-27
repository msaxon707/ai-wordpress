# ai_product_recommender.py
import os
import openai
import json
from logger_setup import setup_logger

logger = setup_logger()
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_product_suggestions(article_text):
    """Generate affiliate product ideas from article content (safe JSON parsing)."""
    prompt = f"""
    Suggest 3 specific Amazon-style products related to this article:

    {article_text[:1500]}

    Respond in **valid JSON only**, like this:
    [
        {{"name": "Product Name", "description": "Short description"}}
    ]
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=400
        )
        raw_output = response["choices"][0]["message"]["content"].strip()

        try:
            products = json.loads(raw_output)
            logger.info(f"🛒 Generated {len(products)} product ideas.")
            return products
        except json.JSONDecodeError:
            logger.warning(f"⚠️ Malformed JSON in product suggestions. Raw output: {raw_output[:100]}...")
            return _fallback_products()

    except Exception as e:
        logger.error(f"❌ Error generating product suggestions: {e}")
        return _fallback_products()


def _fallback_products():
    """Provide safe default products if AI JSON fails."""
    logger.info("🧩 Using fallback product list.")
    return [
        {
            "name": "Rustic Home Lantern",
            "description": "A charming farmhouse lantern perfect for cozy evenings.",
            "url": "https://amzn.to/example1"
        },
        {
            "name": "Outdoor Survival Knife",
            "description": "Durable multi-purpose knife ideal for hunters and campers.",
            "url": "https://amzn.to/example2"
        },
        {
            "name": "Farmhouse Throw Blanket",
            "description": "Soft plaid blanket to complete your rustic living room look.",
            "url": "https://amzn.to/example3"
        },
    ]


def create_amazon_links(products):
    """Attach an Amazon affiliate link to each product."""
    linked = []
    for p in products:
        p["url"] = p.get("url") or f"https://www.amazon.com/s?k={p['name'].replace(' ', '+')}&tag=affiliatecode-20"
        linked.append(p)
    return linked
