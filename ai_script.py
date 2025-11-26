# ai_script.py
import os
import time
import json
import openai
from config import Config
from affiliate_injector import load_affiliate_products, inject_affiliate_links
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from image_handler import generate_featured_image
from wordpress_client import post_to_wordpress
from topic_generator import generate_topic
from category_detector import detect_category
from content_normalizer import normalize_content
from logger_setup import setup_logger
from requests.auth import HTTPBasicAuth

logger = setup_logger()
openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = Config.OPENAI_MODEL


def generate_article(topic):
    logger.info(f"Generating article for topic: {topic}")
    prompt = f"""
    Write a detailed, SEO-optimized blog post about "{topic}".
    Tone: friendly, helpful, and authentic — like a country lifestyle blogger.
    Include headings (<h2>, <h3>), structured paragraphs (<p>), and practical advice.
    Do NOT use markdown (#), placeholders, or code formatting. Return pure HTML only.
    """

    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
        max_tokens=1500
    )
    html_content = response["choices"][0]["message"]["content"]
    return normalize_content(html_content)


def generate_meta(topic, article_text):
    prompt = f"""
    Create a JSON SEO metadata package for a blog titled "{topic}".
    Use this article as context:
    {article_text[:1000]}
    Respond strictly in JSON format:
    {{
        "title": "SEO title",
        "description": "SEO meta description",
        "keywords": "comma,separated,keywords"
    }}
    """
    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=250
        )
        meta = json.loads(response["choices"][0]["message"]["content"])
        return meta.get("title", topic), meta.get("description", ""), meta.get("keywords", "")
    except Exception as e:
        logger.warning(f"⚠️ SEO Meta Generation Failed: {e}")
        return topic, "", ""


def add_affiliate_boxes(article_text, affiliate_products):
    """Insert affiliate product boxes throughout the article."""
    if not affiliate_products:
        return article_text

    box_template = """
    <div class="affiliate-box" style="border:1px solid #ccc;padding:10px;margin:20px 0;border-radius:8px;">
        <h3>Recommended Product: {name}</h3>
        <p>{description}</p>
        <a href="{url}" target="_blank" rel="nofollow sponsored">Check Price on Amazon</a>
    </div>
    """
    paragraphs = article_text.split("</p>")
    for i, product in enumerate(affiliate_products[:3]):
        if (i + 1) * 3 < len(paragraphs):
            paragraphs.insert((i + 1) * 3, box_template.format(**product))
    return "</p>".join(paragraphs)


def add_schema_markup(title, description, keywords):
    """Add JSON-LD structured data for SEO-rich Google snippets."""
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": description,
        "keywords": keywords,
        "author": {"@type": "Person", "name": "The Saxon Blog"},
        "publisher": {
            "@type": "Organization",
            "name": "The Saxon Blog",
            "logo": {
                "@type": "ImageObject",
                "url": "https://thesaxonblog.com/wp-content/uploads/logo.png"
            }
        },
    }
    return f'<script type="application/ld+json">{json.dumps(schema)}</script>'


def main():
    logger.info("=== 🚀 AI WordPress AutoPost Started ===")
    topic = generate_topic()
    logger.info(f"🧠 New Topic: {topic}")

    # Step 1: Generate Article
    article_html = generate_article(topic)

    # Step 2: Load and Generate Affiliate Products
    static_products = load_affiliate_products()
    suggested = generate_product_suggestions(article_html)
    dynamic_products = create_amazon_links(suggested)
    all_products = dynamic_products + static_products

    # Step 3: Add Affiliate Links + Boxes
    article_with_links = inject_affiliate_links(article_html, all_products)
    article_with_boxes = add_affiliate_boxes(article_with_links, all_products)

    # Step 4: Determine Category
    category_id = detect_category(topic)
    logger.info(f"📂 Assigned Category: {category_id}")

    # Step 5: Generate Featured Image
    wp_credentials = HTTPBasicAuth(Config.WP_USERNAME, Config.WP_APP_PASSWORD)
    featured_image_id = generate_featured_image(topic, wp_credentials, Config.WP_BASE_URL)

    # Step 6: SEO Meta + Schema
    seo_title, seo_description, seo_keywords = generate_meta(topic, article_with_boxes)
    schema_markup = add_schema_markup(seo_title, seo_description, seo_keywords)
    final_content = f"{schema_markup}\n{article_with_boxes}"

    # Step 7: Post to WordPress
    post_id = post_to_wordpress(
        title=seo_title,
        content=final_content,
        category_id=category_id,
        featured_media_id=featured_image_id,
        excerpt=seo_description
    )

    if post_id:
        logger.info(f"✅ Successfully published post (ID: {post_id})")
    else:
        logger.error("❌ Post failed to publish.")

    logger.info("🕒 Sleeping for 1 hour before next post...")
    time.sleep(3600)
    main()


if __name__ == "__main__":
    main()