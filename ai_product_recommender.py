import re
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, AMAZON_TAG
from logger_setup import setup_logger

logger = setup_logger()
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_product_suggestions(article_text: str):
    """Ask OpenAI to generate relevant product ideas for affiliate linking."""
    logger.info("[ai_product_recommender] Generating AI-based product suggestions...")

    prompt = f"""
    Analyze the following article and list 3 products that could be promoted through Amazon affiliate links.
    Return them as a JSON list of product names.

    Article:
    {article_text[:1500]}
    """

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200,
        )
        text = response.choices[0].message.content
        products = re.findall(r'"(.*?)"', text)
        logger.info(f"🛒 Suggested products: {products}")
        return products
    except Exception as e:
        logger.warning(f"⚠️ Error generating product suggestions: {e}")
        return []

def create_amazon_links(products):
    """Turn product names into Amazon affiliate links."""
    links = []
    for product in products:
        clean = re.sub(r'[^a-zA-Z0-9 ]', '', product).replace(' ', '+')
        url = f"https://www.amazon.com/s?k={clean}&tag={AMAZON_TAG}"
        links.append({"name": product, "url": url})
    logger.info(f"🔗 Created {len(links)} Amazon-style product links.")
    return links
