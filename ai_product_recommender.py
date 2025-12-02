"""
ai_product_recommender.py — Suggests and builds affiliate product links.
"""

import os
import json
from openai import OpenAI
from config import OPENAI_MODEL, AMAZON_ASSOCIATE_TAG

client = OpenAI()


def generate_product_suggestions(article_text):
    prompt = f"""
Based on the following article, suggest 3 relevant Amazon product ideas.
Each should match the tone and subject (e.g., hunting gear, decor, cooking tools, etc.).
Output in plain JSON format:
["product name 1", "product name 2", "product name 3"]
Article:
{article_text[:1000]}
"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=250,
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        print("[ai_product_recommender] ⚠️ Using fallback products.")
        return ["hunting backpack", "rustic lantern", "cast iron skillet"]


def create_amazon_links(products):
    links = []
    for p in products:
        search_term = p.replace(" ", "+")
        url = f"https://www.amazon.com/s?k={search_term}&tag={AMAZON_ASSOCIATE_TAG}"
        links.append({"name": p, "url": url})
    print(f"[ai_product_recommender] 🔗 Created {len(links)} Amazon links.")
    return links
