import re
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from logger_setup import setup_logger
from content_normalizer import normalize_content
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from affiliate_injector import inject_affiliate_links
from wordpress_client import get_recent_posts, post_to_wordpress
from image_handler import get_featured_image_id
from category_detector import detect_category

logger = setup_logger()
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_article(topic: str) -> str:
    """Generate SEO-optimized article text."""
    logger.info(f"[ai_script] Generating article for topic: {topic}")

    prompt = f"""
    Write a detailed, SEO-optimized blog post about "{topic}".
    Tone: friendly, conversational, and written by a country/outdoors enthusiast.
    Include natural product mentions where relevant (no hashtags).
    Use proper HTML headings (<h2>, <h3>), lists, and strong tags.
    """

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=1500,
    )

    article = response.choices[0].message.content.strip()
    return normalize_content(article)

def generate_meta(topic: str, article_text: str):
    """Generate meta title and description for SEO."""
    prompt = f"""
    Write an SEO-friendly title and meta description for this article:
    Topic: {topic}
    Content: {article_text[:400]}
    Respond in JSON: {{ "title": "...", "description": "..." }}
    """

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150,
        )
        text = response.choices[0].message.content
        match = re.search(r'"title"\s*:\s*"([^"]+)"\s*,\s*"description"\s*:\s*"([^"]+)"', text)
        if match:
            return match.group(1), match.group(2)
    except Exception as e:
        logger.warning(f"[SEO META] Fallback used — {e}")
    return topic, f"Learn about {topic} and more country lifestyle insights."

def add_internal_links(content: str):
    """Fetch recent posts from WordPress and insert 2 internal links."""
    try:
        posts = get_recent_posts(limit=5)
        if not posts:
            return content
        import random
        picks = random.sample(posts, min(2, len(posts)))
        for post in picks:
            link_html = f'<a href="{post["link"]}" target="_blank">{post["title"]["rendered"]}</a>'
            content += f"<p>Read next: {link_html}</p>"
        return content
    except Exception as e:
        logger.warning(f"[Internal Linking] Skipped — {e}")
        return content

def build_post(topic: str):
    """Main build routine to generate and post full article."""
    article = generate_article(topic)
    products = generate_product_suggestions(article)
    links = create_amazon_links(products)
    article_with_links = inject_affiliate_links(article, links)
    article_final = add_internal_links(article_with_links)

    category = detect_category(topic)
    image_id = get_featured_image_id(topic)
    seo_title, seo_desc = generate_meta(topic, article_final)

    post_to_wordpress(
        title=seo_title,
        content=article_final,
        category_id=category,
        featured_media_id=image_id,
        excerpt=seo_desc,
    )

    logger.info(f"✅ Successfully published: {seo_title}")
