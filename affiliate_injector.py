"""
affiliate_injector.py — Inserts affiliate links and internal WordPress links
into generated article text for natural engagement and SEO benefit.
"""

import random
import requests
from config import WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD


def get_recent_posts(limit=10):
    """Pull recent posts to use for internal linking."""
    try:
        r = requests.get(f"{WP_BASE_URL}/wp-json/wp/v2/posts?per_page={limit}",
                         auth=(WP_USERNAME, WP_APP_PASSWORD))
        if r.status_code == 200:
            return [{"title": p["title"]["rendered"], "url": p["link"]} for p in r.json()]
    except Exception as e:
        print(f"[affiliate_injector] ⚠️ Failed to fetch recent posts: {e}")
    return []


def inject_affiliate_links(article_text, affiliate_products):
    """Injects 2–3 affiliate links and 2 internal links in the article."""
    paragraphs = article_text.split("\n")
    if len(paragraphs) < 3:
        return article_text

    # Choose random paragraphs to insert links
    positions = random.sample(range(len(paragraphs)), min(3, len(paragraphs)))

    for i, product in enumerate(affiliate_products[:3]):
        link_html = f'<a href="{product["url"]}" target="_blank" rel="nofollow noopener">{product["name"]}</a>'
        paragraphs[positions[i % len(positions)]] += f" Check out {link_html} for a great option."

    # Internal links
    posts = get_recent_posts()
    if posts:
        internal_links = random.sample(posts, min(2, len(posts)))
        for post in internal_links:
            link_html = f'<a href="{post["url"]}">{post["title"]}</a>'
            insert_index = random.choice(range(len(paragraphs)))
            paragraphs[insert_index] += f" You might also like my post on {link_html}."

    return "\n".join(paragraphs)
