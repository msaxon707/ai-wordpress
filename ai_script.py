"""
ai_script.py — Generates SEO-optimized, affiliate-rich blog content using OpenAI.
"""

import os
from openai import OpenAI
from config import OPENAI_MODEL
from content_normalizer import normalize_content
from affiliate_injector import inject_affiliate_links, load_affiliate_products
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from wordpress_client import post_to_wordpress
from image_handler import get_featured_image_id
from category_detector import detect_category

# ✅ Modern client (auto-loads API key)
client = OpenAI()


def generate_article(topic):
    print(f"[ai_script] Generating article for: {topic}")
    prompt = f"""
Write a friendly, SEO-optimized blog article about "{topic}".
The style should feel like a down-to-earth country blogger sharing real advice.
Include 2–3 affiliate product mentions naturally (e.g. “I recommend…” or “One great option is…”).
Make sure it’s well-structured with <h2>, <ul>, and <p> tags.
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1200,
    )

    article = response.choices[0].message.content
    return normalize_content(article)


def generate_meta(topic, article):
    """Generate SEO meta title and description."""
    prompt = f"""
Create an SEO title and meta description for a blog post about "{topic}".
Respond ONLY in JSON format like:
{{"title": "...", "description": "..."}}
"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200,
        )
        import json
        meta = json.loads(response.choices[0].message.content)
        return meta.get("title", topic), meta.get("description", "")
    except Exception:
        return topic, f"Learn about {topic} and more country living ideas."


def main_generate(topic):
    """Generate and publish a complete post for the given topic."""
    article = generate_article(topic)

    products = load_affiliate_products()
    suggested = generate_product_suggestions(article)
    links = create_amazon_links(suggested)
    combined = links + products

    article_with_links = inject_affiliate_links(article, combined)
    category = detect_category(topic)
    featured_image = get_featured_image_id(topic)
    seo_title, seo_desc = generate_meta(topic, article_with_links)

    post_to_wordpress(
        title=seo_title,
        content=article_with_links,
        category_id=category,
        featured_media_id=featured_image,
        excerpt=seo_desc,
    )

    print(f"[ai_script] ✅ Posted successfully: {seo_title}")
