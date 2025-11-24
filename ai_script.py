import os
import time
import json
from openai import OpenAI
from config import OPENAI_MODEL
from affiliate_injector import load_affiliate_products, inject_affiliate_links
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from image_handler import get_featured_image_id
from wordpress_client import post_to_wordpress
from topic_generator import generate_topic
from category_detector import detect_category
from content_normalizer import normalize_content
from logger_setup import logger

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_article(topic):
    logger.info(f"Generating article for topic: {topic}")
    prompt = f'''
    Write a long-form, SEO-optimized blog article on "{topic}".
    The tone should be friendly and authoritative, similar to a lifestyle blog.
    Use structured headers (H2, H3) and conversational flow.
    Do NOT use hashtags or markdown symbols (#). Output in pure HTML.
    Include clear sections and a natural narrative.
    '''

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
        max_tokens=1500,
    )
    html_content = response.choices[0].message.content
    return normalize_content(html_content)


def generate_meta(topic, article_text):
    prompt = f'''
    Create a JSON SEO package for a blog titled "{topic}" based on the following article content:
    {article_text[:1000]}
    Respond in JSON with: title, description, keywords (comma-separated).
    '''
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=250,
        )
        meta = json.loads(response.choices[0].message.content)
        return meta.get("title", topic), meta.get("description", ""), meta.get("keywords", "")
    except Exception as e:
        logger.warning(f"Failed to generate meta data: {e}")
        return topic, "", ""


def add_affiliate_boxes(article_text, affiliate_products):
    if not affiliate_products:
        return article_text

    box_template = '''
    <div class="affiliate-box">
        <h3>Recommended Product: {name}</h3>
        <p>{description}</p>
        <a href="{url}" target="_blank" rel="nofollow sponsored">Check Price on Amazon</a>
    </div>
    '''
    insert_points = article_text.split("</p>")
    for i, product in enumerate(affiliate_products[:3]):
        if i * 3 < len(insert_points):
            insert_points.insert((i + 1) * 3, box_template.format(**product))
    return "</p>".join(insert_points)


def add_schema_markup(title, description, keywords):
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
            "logo": {"@type": "ImageObject", "url": "https://thesaxonblog.com/wp-content/uploads/logo.png"}
        },
    }
    return f'<script type="application/ld+json">{json.dumps(schema)}</script>'


def main():
    logger.info("=== AI WordPress Autopost Started ===")
    topic = generate_topic()
    logger.info(f"Topic: {topic}")

    article_html = generate_article(topic)
    static_products = load_affiliate_products()
    suggested = generate_product_suggestions(article_html)
    dynamic_products = create_amazon_links(suggested)
    all_products = dynamic_products + static_products

    article_with_links = inject_affiliate_links(article_html, all_products)
    article_with_boxes = add_affiliate_boxes(article_with_links, all_products)

    category_id = detect_category(topic)
    logger.info(f"Detected Category ID: {category_id}")

    featured_image_id = get_featured_image_id(topic)

    seo_title, seo_description, seo_keywords = generate_meta(topic, article_with_boxes)
    schema_markup = add_schema_markup(seo_title, seo_description, seo_keywords)

    final_content = f"{schema_markup}\n{article_with_boxes}"

    post_id = post_to_wordpress(
        title=seo_title,
        content=final_content,
        category_id=category_id,
        featured_media_id=featured_image_id,
        excerpt=seo_description,
    )

    logger.info(f"✅ Successfully posted to WordPress (ID: {post_id})")
    logger.info("Sleeping for 1 hour before next post...")
    time.sleep(3600)
    main()


if __name__ == "__main__":
    main()

