# ======================================================================
# File: ai_script.py  (ONLY the small top-level tweaks shown)
# If you used my previous ai_script, replace with this full file for clarity.
# ======================================================================
from __future__ import annotations

import os
from typing import Optional, List

from content_normalizer import normalize_post_html
from wordpress_client import WordPressClient

try:
    from config import (
        WP_USERNAME,
        WP_APP_PASSWORD,
        WP_BASE_URL,
        OPENAI_MODEL,
        AFFILIATE_DOMAINS,
    )
except Exception:
    WP_USERNAME = os.getenv("WP_USERNAME", "")
    WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")
    WP_BASE_URL = os.getenv("WP_BASE_URL", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    AFFILIATE_DOMAINS = None


def _call_ai_to_generate_body(topic: str, include_links: Optional[List[str]]) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            sys = (
                "Write a concise blog post in clean HTML (<p>, <h2>, <ul>, <a>). "
                "No Markdown. Keep headings as <h2> and paragraphs as <p>."
            )
            user = f"Topic: {topic}."
            if include_links:
                user += " Weave these links naturally: " + ", ".join(include_links)
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
                temperature=0.7,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception:
            pass

    links_section = ""
    if include_links:
        bullets = "\n".join(f"- [{u}]({u})" for u in include_links)
        links_section = f"\n\n**References**\n\n{bullets}\n"
    return f"# {topic}\n\nThis is a sample article body about **{topic}**.\n\n- Point one\n- Point two\n\nVisit www.example.com for more info.{links_section}"


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

    # Fail fast on missing base URL/user/pass
    if not WP_BASE_URL:
        raise SystemExit("Set WP_BASE_URL (e.g., https://your-site.com)")
    if not WP_USERNAME or not WP_APP_PASSWORD:
        raise SystemExit("Set WP_USERNAME and WP_APP_PASSWORD (WordPress application password).")

    # 1) Generate
    article = generate_article(topic, include_links=include_links)

    # 2) Normalize AI output → HTML
    normalized_html = normalize_post_html(article["content"], affiliate_domains=AFFILIATE_DOMAINS)

    # 3) Publish
    wp = WordPressClient(
        base_url=WP_BASE_URL,
        username=WP_USERNAME,
        application_password=WP_APP_PASSWORD,
    )
    print(f"Publishing to: {wp.base_url}/wp-json/wp/v2/posts")  # help debug config

    post_id = wp.create_post(
        title=article["title"],
        html_content=normalized_html,
        excerpt=article.get("excerpt") or "",
        status=os.getenv("WP_STATUS", "publish"),
    )
    print(f"Published post ID: {post_id}")


if __name__ == "__main__":
    main()
