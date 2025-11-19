import os
from openai import OpenAI
from config import OPENAI_MODEL
from affiliate_injector import load_affiliate_products, inject_affiliate_links
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from image_handler import get_featured_image_id
from wordpress_client import post_to_wordpress
from topic_generator import generate_topic
from category_detector import detect_category
from content_normalizer import normalize_content


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


def generate_article(topic):
    """Generate SEO-optimized article text using OpenAI."""
    print(f"[ai_script] Generating article for topic: {topic}")

    prompt = f"""
    Write a detailed, SEO-optimized blog post about "{topic}".
    You are an expert lifestyle and outdoors blogger who writes with personality and warmth.
    Include natural affiliate product mentions (e.g., “I recommend checking out …”).
    Focus on storytelling, practical advice, and conversational tone.
    Avoid using placeholders like [HEAD], [META], or [BODY].
    Output the full article ready for a WordPress post.
    """

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=1200,
    )

    article_text = response.choices[0].message.content
    return normalize_content(article_text)


def generate_meta(topic, article_text):
    """Generate SEO meta title and description."""
    prompt = f"""
    Create an SEO title and meta description for a blog post about "{topic}".
    Respond in JSON like this:
    {{
        "title": "string",
        "description": "string"
    }}
    """

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150,
        )
        import json
        meta = json.loads(response.choices[0].message.content)
        return meta.get("title", topic), meta.get("description", "")
    except Exception as e:
        print(f"[WARN] Failed to generate meta: {e}")
        return topic, ""


def main():
    print("[ai_script] === AI WordPress Post Generation Started ===")

    topic = generate_topic()
    print(f"[ai_script] Selected topic: {topic}")

    article_text = generate_article(topic)

    # Load products
    static_products = load_affiliate_products()
    suggested = generate_product_suggestions(article_text)
    dynamic_products = create_amazon_links(suggested)
    all_products = dynamic_products + static_products

    # Inject links naturally
    article_with_links = inject_affiliate_links(article_text, all_products)

    # Detect category
    category_id = detect_category(topic)
    print(f"[ai_script] Detected category ID: {category_id}")

    # Featured image
    featured_image_id = get_featured_image_id(topic)

    # Generate SEO meta
    seo_title, seo_description = generate_meta(topic, article_with_links)

    # Post to WordPress
    post_id = post_to_wordpress(
    title=seo_title,
    content=article_with_links,
    category_id=category_id,
    featured_media_id=featured_image_id,
    excerpt=seo_description,
)

    print(f"[ai_script] ✅ Successfully posted to WordPress (ID: {post_id})")
    print("[ai_script] === Run complete. Safe to exit for cron. ===")


if __name__ == "__main__":
    main()
