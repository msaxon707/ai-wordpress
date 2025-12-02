import random
import re
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from logger_setup import setup_logger

logger = setup_logger()
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_product_suggestions(article_text: str):
    """Generate product suggestions relevant to the article."""
    logger.info("[ai_product_recommender] Generating AI-based product suggestions...")

    prompt = f"""
    Based on the following blog post, list 4-6 Amazon-style product ideas that directly relate.
    The products should be realistic, useful, and fit naturally with the content.
    Example output (no numbering):
    - YETI Rambler 20 oz Tumbler
    - Cast Iron Skillet
    - Outdoor Grill Table
    - Rustic Lantern Lights

    Blog content:
    {article_text[:3000]}
    """

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert in affiliate content optimization."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        suggestions = response.choices[0].message.content.strip().split("\n")
        clean_suggestions = [re.sub(r"^[\-\d\.\s]+", "", s).strip() for s in suggestions if s.strip()]
        logger.info(f"🛒 Suggested products: {clean_suggestions}")
        return clean_suggestions

    except Exception as e:
        logger.warning(f"⚠️ Failed to parse product suggestions: {e}")
        return []

def create_amazon_links(product_names):
    """Create Amazon affiliate links for given product names."""
    if not product_names:
        return []
    tag = "thesaxonblog01-20"
    links = [
        {
            "name": name,
            "url": f"https://www.amazon.com/s?k={'+'.join(name.split())}&tag={tag}"
        }
        for name in product_names
    ]
    logger.info(f"🔗 Created {len(links)} Amazon-style product links.")
    return links
