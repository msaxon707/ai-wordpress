# ai_script.py

import os
import openai
from config import OPENAI_MODEL
from affiliate_injector import load_affiliate_products, inject_affiliate_links
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from image_handler import get_featured_image_id
from wordpress_client import post_to_wordpress
from topic_generator import generate_topic
from category_detector import detect_category

# Load environment keys from Coolify
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def generate_article(prompt_topic):
    """Generate SEO article using OpenAI GPT model and auto-inject affiliate links."""
    openai.api_key = OPENAI_API_KEY

    prompt = f"""
    You are a seasoned outdoors writer who creates SEO-optimized, persuasive, story-driven articles.
    Focus on topics related to {prompt_topic}.
    Make the content authentic, rich, and encourage readers to check recommended gear naturally.
    Avoid sounding like a sales pitch. Include practical insights and real-sounding field advice.
    """

    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200,
        temperature=1.0,
    )

    article_text = response.choices[0].message["content"]

    # === AI Product Recommender Integration ===
    product_names = generate_product_suggestions(article_text)
    dynamic_products = create_amazon_links(product_names)

    # Load static affiliate backup list (hybrid mode)
    static_products = load_affiliate_products()

    # Merge dynamic + static lists
    all_products = dynamic_products + static_products

    # Inject affiliate links
    article_with_links = inject_affiliate_links(article_text, all_products)

    return article_with_links


def main():
    print("[ai_script] === AI WordPress Post Generation Started ===")
    topic = generate_topic()
    print(f"[ai_script] Generating article for topic: {topic}")

    article = generate_article(topic)
    c
