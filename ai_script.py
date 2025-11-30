"""
ai_script.py — Generates a full blog post with OpenAI, SEO meta, and affiliate links.
"""

import json
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from affiliate_injector import inject_affiliate_links
from category_detector import detect_category
from image_handler import get_featured_image_id
from wordpress_client import post_to_wordpress

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_article(topic):
    prompt = f"""
Write a friendly, engaging, SEO-optimized blog post about: "{topic}".

- Style: friendly country blogger
- Include storytelling, practical tips, and personal tone.
- Encourage readers to check out useful Amazon products (without sounding salesy).
- Structure: intro, helpful subheadings (h2/h3), conclusion.
- Avoid hashtags and filler.
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
        max_tokens=1300
    )

    return response.choices[0].message.content


def generate_meta(topic, article):
    prompt = f"""
Create a short SEO title and meta description for a blog post about "{topic}".
Return JSON in this format:
{{"title": "string", "description": "string"}}
"""

    try:
        r = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        data = json.loads(r.choices[0].message.content)
        return data["title"], data["description"]
    except Exception:
        return topic, f"Learn helpful country living and hunting tips about {topic}."


def build_post(topic):
    article = generate_article(topic)
    products = generate_product_suggestions(article)
    affiliate_links = create_amazon_links(products)
    linked_article = inject_affiliate_links(article, affiliate_links)
    category = detect_category(article)
    featured_image_id = get_featured_image_id(topic)
    title, excerpt = generate_meta(topic, linked_article)
    post_to_wordpress(title, linked_article, category, featured_media_id=featured_image_id, excerpt=excerpt)
