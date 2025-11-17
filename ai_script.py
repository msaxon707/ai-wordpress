import os
import sys
from openai import OpenAI
from config import OPENAI_MODEL
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from affiliate_injector import inject_affiliate_links
from image_handler import get_featured_image_id
from wordpress_client import post_to_wordpress
from topic_generator import generate_topic
from category_detector import detect_category
from content_normalizer import normalize_content

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_article(prompt_topic):
    """Generate a blogger-style SEO article with contextual Amazon affiliate integration."""
    print(f"[ai_script] Generating article for topic: {prompt_topic}")

    prompt = f"""
    You are a friendly, knowledgeable outdoor and decor blogger.
    Write a detailed, conversational, SEO-optimized blog post about '{prompt_topic}'.
    Make it sound human, authentic, and helpful.
    Include practical advice, small stories, and a few product mentions naturally.
    Tone: relaxed, expert, country-style.
    Output should be clean HTML (no markdown symbols or hashtags).
    """

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=1.0,
        )
    except Exception as e:
        print(f"[ERROR] OpenAI request failed: {e}")
        sys.exit(1)

    article_html = response.choices[0].message.content.strip()
    return normalize_content(article_html)
    def generate_seo_metadata(article_text, topic):
    """Generate an SEO title and meta description using OpenAI."""
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""
    Analyze this blog article and craft:
    1. A catchy SEO title (≤60 characters) that includes the keyword "{topic}".
    2. A concise meta description (≤160 characters) that will improve Google CTR.

    Return output in JSON:
    {{
      "title": "SEO title here",
      "description": "meta description here"
    }}

    ARTICLE:
    {article_text[:2500]}
    """

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        import json
        raw = response.choices[0].message.content
        seo = json.loads(raw)
        return seo.get("title", topic), seo.get("description", "")
    except Exception as e:
        print(f"[WARN] SEO metadata generation failed: {e}")
        return topic, ""



def main():
    print("[ai_script] === AI WordPress Post Generation Started ===")

    # 1️⃣ Generate topic (balances decor/outdoors)
    topic = generate_topic()
    print(f"[ai_script] Selected topic: {topic}")

    # 2️⃣ Generate full article
    article = generate_article(topic)

    # 3️⃣ Get affiliate products
    product_names = generate_product_suggestions(article)
    amazon_links = create_amazon_links(product_names)
    print("[ai_recommender] Suggested products:")
    for p in product_names:
        print(f"   - {p}")

    # 4️⃣ Inject affiliate links
    article_with_links = inject_affiliate_links(article, amazon_links)

    # 5️⃣ Detect category
    category_id = detect_category(topic)
    print(f"[ai_script] Detected category ID: {category_id}")

    # 6️⃣ Get featured image
    featured_image_id = get_featured_image_id(topic)

    # 7️⃣ Post to WordPress
    post_id = post_to_wordpress(
        title=topic,
        content=article_with_links,
        categories=[category_id],
        image_bytes=None,
        image_filename=None
    )

    if post_id:
        print(f"[ai_script] ✅ Successfully posted to WordPress (ID: {post_id})")
    else:
        print("[ai_script] ❌ Failed to post to WordPress")

    print("[ai_script] === Run complete. Safe to exit for cron. ===")
    sys.exit(0)


if __name__ == "__main__":
    main()
