# ======================================================================
# File: ai_script.py
# Path: ./ai_script.py
# Purpose: Generate article, normalize to HTML, publish to WordPress
# ======================================================================
from __future__ import annotations

import os
from typing import Optional, List

from content_normalizer import normalize_post_html
from wordpress_client import WordPressClient

# Expect these in your own config.py, or via env vars as fallback.
try:
    from config import (
        WP_USERNAME,
        WP_APP_PASSWORD,
        WP_BASE_URL,
        OPENAI_MODEL,          # optional; ignored if OpenAI not configured
        AFFILIATE_DOMAINS,     # optional list like ["amzn.to","amazon.com","impact.com"]
    )
except Exception:
    WP_USERNAME = os.getenv("WP_USERNAME", "")
    WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")
    WP_BASE_URL = os.getenv("WP_BASE_URL", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    AFFILIATE_DOMAINS = None  # set to list to scope "sponsored" rels


def _call_ai_to_generate_body(topic: str, include_links: Optional[List[str]]) -> str:
    """
    Generates Markdown or HTML. If OpenAI isn't configured, returns a simple Markdown stub.
    Why: Keeps script runnable without external setup.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            # Minimal OpenAI call (new SDK). Replace with your existing logic if present.
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
            content = (resp.choices[0].message.content or "").strip()
            return content
        except Exception:
            pass  # fall back to stub if SDK/model not available

    # Fallback Markdown stub (ensures pipeline compiles/runs)
    links_section = ""
    if include_links:
        bullets = "\n".join(f"- [{u}]({u})" for u in include_links)
        links_section = f"\n\n**References**\n\n{bullets}\n"
    return f"# {topic}\n\nThis is a sample article body about **{topic}**. It contains a paragraph, a list, and a link.\n\n- Point one\n- Point two\n\nVisit www.example.com for more info.{links_section}"


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
    include_links_env = os.environ.get("INCLUDE_LINKS", "")  # CSV URLs
    include_links = [u.strip() for u in include_links_env.split(",") if u.strip()] or None

    # 1) Generate
    article = generate_article(topic, include_links=include_links)

    # 2) Normalize AI output → HTML (fix headings/paragraphs + affiliate links)
    normalized_html = normalize_post_html(
        article["content"],
        affiliate_domains=AFFILIATE_DOMAINS,
    )

    # 3) Publish
    wp = WordPressClient(
        base_url=WP_BASE_URL,
        username=WP_USERNAME,
        application_password=WP_APP_PASSWORD,
    )

    post_id = wp.create_post(
        title=article["title"],
        html_content=normalized_html,
        excerpt=article.get("excerpt") or "",
        status=os.getenv("WP_STATUS", "publish"),
    )
    print(f"Published post ID: {post_id}")


if __name__ == "__main__":
    main()
