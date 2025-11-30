from openai import OpenAI
import os
import json
from logger_setup import setup_logger

logger = setup_logger()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_product_suggestions(article_text):
    prompt = f"""
    Suggest 3 specific Amazon-style products related to this article:

    {article_text[:1500]}

    Respond in valid JSON only:
    [
        {{"name": "Product Name", "description": "Short description"}}
    ]
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=400
        )
        raw_output = response.choices[0].message.content.strip()
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            logger.warning(f"⚠️ Malformed JSON. Using fallback.")
            return _fallback_products()
    except Exception as e:
        logger.error(f"❌ Error generating product suggestions: {e}")
        return _fallback_products()

def _fallback_products():
    logger.info("🧩 Using fallback product list.")
    return [
        {"name": "Rustic Home Lantern", "description": "A charming farmhouse lantern perfect for cozy evenings.", "url": "https://amzn.to/example1"},
        {"name": "Outdoor Survival Knife", "description": "Durable multi-purpose knife ideal for hunters and campers.", "url": "https://amzn.to/example2"},
        {"name": "Farmhouse Throw Blanket", "description": "Soft plaid blanket to complete your rustic living room look.", "url": "https://amzn.to/example3"},
    ]

def create_amazon_links(products):
    linked = []
    for p in products:
        p["url"] = p.get("url") or f"https://www.amazon.com/s?k={p['name'].replace(' ', '+')}&tag=affiliatecode-20"
        linked.append(p)
    return linked
