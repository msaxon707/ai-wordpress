from __future__ import annotations
import os
from typing import Optional, List
from openai import OpenAI
from config import SETTINGS
from content_normalizer import normalize_post_html
from wordpress_client import WordPressClient

def _call_ai_to_generate_body(topic: str, include_links: Optional[List[str]]) -> str:
    # HTML-only to avoid '#' and Markdown leakage.
    if not SETTINGS.OPENAI_API_KEY:
        links = ""
        if include_links:
            bullets = "\n".join(f"- [{u}]({u})" for u in include_links)
            links = f"\n\n**References**\n\n{bullets}\n"
        return f"# {topic}\n\nThis is a sample article body about **{topic}**.\n\n- Point one\n- Point two\n\nVisit www.example.com for more info.{links}"
    client = OpenAI(api_key=SETTINGS.OPENAI_API_KEY)
    system = ("You are a blogging assistant. Output STRICT HTML only: <h2>, <p>, <ul>, <ol>, <li>, <a>. "
              "No Markdown. No code fences. Use short paragraphs and meaningful <h2> subheadings.")
    user = f"Topic: {topic}."
    if include_links: user += " Weave these links naturally: " + ", ".join(include_links)
    resp = client.chat.completions.create(
        model=SETTINGS.OPENAI_MODEL,
        temperature=SETTINGS.OPENAI_TEMPERATURE,
        max_tokens=SETTINGS.OPENAI_MAX_TOKENS,
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
    )
    return (resp.choices[0].message.content or "").strip()

def _make_excerpt_from_text(text: str, limit: int = 220) -> str:
    s = " ".join((text or "").split())
    return (s[:limit] + "…") if len(s) > limit else s

def generate_article(topic: str, include_links: Optional[List[str]] = None) -> dict:
    title = f"{topic}".strip() or "Untitled"
    raw_body = _call_ai_to_generate_body(topic=topic, include_links=include_links)
    excerpt = _make_excerpt_from_text(raw_body)
    return {"title": title, "content": raw_body, "excerpt": excerpt}

def main():
    topic = os.environ.get("TOPIC", "Sample Topic")
    include_links_env = os.environ.get("INCLUDE_LINKS", "")
    include_links = [u.strip() for u in include_links_env.split(",") if u.strip()] or None

    article = generate_article(topic, include_links=include_links)

    normalized_html = normalize_post_html(article["content"], affiliate_domains=SETTINGS.AFFILIATE_DOMAINS)

    wp = WordPressClient(base_url=SETTINGS.WP_BASE_URL, username=SETTINGS.WP_USERNAME, application_password=SETTINGS.WP_APP_PASSWORD)
    print(f"Publishing to: {wp.base_url}/wp-json/wp/v2/posts")

    if SETTINGS.DRY_RUN:
        print("DRY_RUN=1 → not posting. Preview:\n", normalized_html[:800])
        return

    post_id = wp.create_post(title=article["title"], html_content=normalized_html, excerpt=article.get("excerpt") or "", status=os.getenv("WP_STATUS", "publish"))
    print(f"Published post ID: {post_id}")

if __name__ == "__main__":
    main()
