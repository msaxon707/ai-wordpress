# ai_product_recommender.py
import os
import openai
from logger_setup import setup_logger

logger = setup_logger()
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_product_suggestions(article_text):
    """Generate affiliate product ideas based on the article content."""
    prompt = f"""
    Suggest 3 specific Amazon-style products related to this article:

    {article_text[:1500]}

    Respond in JSON format:
    [
        {{"name": "Product Name", "description": "Short appealing description"}}
    ]
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=350
        )
        import json
        products = json.loads(response["choices"][0]["message"]["content"])
        logger.info(f"🛒 Generated {len(products)} product ideas.")
        return products
    except Exception as e:
        logger.error(f"Error generating product suggestions: {e}")
        return []


def create_amazon_links(products):
    """Attach an Amazon affiliate link to each product."""
    linked = []
    for p in products:
        p["url"] = f"https://www.amazon.com/s?k={p['name'].replace(' ', '+')}&tag=affiliatecode-20"
        linked.append(p)
    return linked