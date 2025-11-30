"""
ai_product_recommender.py — Generates Amazon product ideas and affiliate links
for each article using OpenAI and your Amazon Associate Tag.
"""

import json
import os
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, AMAZON_TAG

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_product_suggestions(article_text: str):
    """Ask OpenAI for 3 brand-specific product suggestions based on the article."""
    prompt = f"""
Based on this article:

{article_text[:2000]}

Suggest 3 Amazon products that would be highly relevant to readers.
- Include real brands if possible (YETI, Carhartt, Lodge, etc.).
- Each should be 3–8 words long.
- Return ONLY JSON in this format:
{{"products": ["product1", "product2", "product3"]}}
"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        products = json.loads(content).get("products", [])
        if not products:
            raise ValueError("Empty product list.")
        return products

    except Exception as e:
        print(f"[ai_product_recommender] ⚠️ Failed to parse product suggestions: {e}")
        # Fallback list
        return ["YETI Rambler Mug", "Carhartt Work Jacket", "Lodge Cast Iron Skillet"]


def create_amazon_links(products):
    """Turn product names into Amazon affiliate links."""
    links = []
    for p in products:
        query = p.replace(" ", "+")
        link = f"https://www.amazon.com/s?k={query}&tag={AMAZON_TAG}"
        links.append({"name": p, "url": link})
    print(f"[ai_product_recommender] 🔗 Created {len(links)} Amazon affiliate links.")
    return links
