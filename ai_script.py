# =========================
# path: ai_script.py  (DROP-IN REPLACEMENT)
# =========================
import os
import sys
import argparse
from typing import Optional, List
from openai import OpenAI
from config import SETTINGS
from content_normalizer import normalize_post_html
from wordpress_client import WordPressClient

PLACEHOLDER_TOPICS = {"sample topic", "topic", "test", "hello world", ""}

def _call_ai_to_generate_body(topic: str, include_links: Optional[List[str]]) -> str:
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

def _resolve_topic() -> tuple[str, bool]:
    parser = argparse.ArgumentParser(description="AI → WordPress publisher")
    parser.add_argument("--topic", help="Post title/topic")
    parser.add_argument("--force", action="store_true", help="Allow placeholder topics")
    parser.add_argument("--include-links", default="", help="Comma-separated URLs to weave in")
    args = parser.parse_args()

    topic = (args.topic or os.environ.get("TOPIC", "")).strip()
    include_links = [u.strip() for u in (args.include_links or os.getenv("INCLUDE_LINKS","")).split(",") if u.strip()] or None
    force = bool(args.force or os.getenv("FORCE_POST") in {"1","true","yes"})
    return topic, force, include_links

def main():
    topic, force, include_links = _resolve_topic()
    if (topic.lower() in PLACEHOLDER_TOPICS) and not force:
        sys.exit("Refusing to post without a real TOPIC. Use --topic 'Your Title' or set env TOPIC. Add --force to override.")

    raw_body = _call_ai_to_generate_body(topic=topic, include_links=include_links)
    normalized_html = normalize_post_html(raw_body, affiliate_domains=SETTINGS.AFFILIATE_DOMAINS)
    excerpt = _make_excerpt_from_text(raw_body)

    wp = WordPressClient(
        base_url=SETTINGS.WP_BASE_URL,
        username=SETTINGS.WP_USERNAME,
        application_password=SETTINGS.WP_APP_PASSWORD,
    )
    print(f"Endpoint: {wp.posts_endpoint}")

    # Upsert by exact title
    matches = wp.search_posts(title=topic, per_page=5)
    match_id = next((p["id"] for p in matches if (p.get("title", {}).get("rendered","").strip().lower() == topic.lower())), None)

    if match_id:
        print(f"Updating existing post id={match_id} title='{topic}'")
        post_id = wp.update_post(
