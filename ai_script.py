# =========================
# path: ai_script.py  (FIXED & CLEANED)
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


# -------------------------
# AI BODY GENERATION
# -------------------------
def _call_ai_to_generate_body(topic: str, include_links: Optional[List[str]]) -> str:
    """Generate HTML-only body via OpenAI, or fallback sample if no API key."""
    if not SETTINGS.OPENAI_API_KEY:
        # Fallback mode for testing
        links = ""
        if include_links:
            bullets = "\n".join(f"- [{u}]({u})" for u in include_links)
            links = f"\n\n**References**\n\n{bullets}\n"

        return (
            f"<h1>{topic}</h1>"
            f"<p>This is a sample article body about <strong>{topic}</strong>.</p>"
            f"<ul><li>Point one</li><li>Point two</li></ul>"
            f"<p>Visit https://example.com for more info.</p>{links}"
        )

    client = OpenAI(api_key=SETTINGS.OPENAI_API_KEY)

    system_prompt = (
        "You are a blogging assistant. "
        "Output STRICT HTML only using: <h2>, <p>, <ul>, <ol>, <li>, <a>. "
        "No Markdown. No code fences. Keep paragraphs short and structured."
    )

    user_prompt = f"Write a full article on: {topic}."
    if include_links:
        user_prompt += " Weave these links naturally: " + ", ".join(include_links)

    resp = client.chat.completions.create(
        model=SETTINGS.OPENAI_MODEL,
        temperature=SETTINGS.OPENAI_TEMPERATURE,
        max_tokens=SETTINGS.OPENAI_MAX_TOKENS,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return (resp.choices[0].message.content or "").strip()


# -------------------------
# EXCERPT BUILDER
# -------------------------
def _make_excerpt_from_text(text: str, limit: int = 220) -> str:
    s = " ".join((text or "").split())
    return (s[:limit] + "…") if len(s) > limit else s


def _resolve_topic() -> tuple[str, bool, list[str] | None]:
    parser = argparse.ArgumentParser(description="AI → WordPress publisher")
    parser.add_argument("--topic", help="Post title/topic")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--include-links", default="")
    args = parser.parse_args()

    # pick up provided or env-based topic
    topic = (args.topic or os.environ.get("TOPIC", "")).strip()

    # If no topic → auto-generate one with OpenAI
    if not topic:
        client = OpenAI(api_key=SETTINGS.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=SETTINGS.OPENAI_MODEL,
            max_tokens=50,
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": "Generate a single SEO-optimized blog topic. No quotes."
                },
                {
                    "role": "user",
                    "content": "Give me a good blogging topic for today."
                }
            ]
        )
        topic = resp.choices[0].message.content.strip()

    # Process include-links
    include_links = [
        u.strip() for u in
        (args.include_links or os.getenv("INCLUDE_LINKS", "")).split(",")
        if u.strip()
    ] or None

    # Always allow posting since we generate a real topic
    force = True

    return topic, force, include_links



# -------------------------
# MAIN
# -------------------------
def main():
    topic, force, include_links = _resolve_topic()

    # Prevent accidental junk posts
    if (topic.lower() in PLACEHOLDER_TOPICS) and not force:
        sys.exit(
            "Refusing to post without a real TOPIC. "
            "Use --topic 'Your Title' or env TOPIC=MyTitle. Add --force to override."
        )

    # Generate + normalize body
    raw_body = _call_ai_to_generate_body(topic, include_links)
    normalized_html = normalize_post_html(
        raw_body, affiliate_domains=SETTINGS.AFFILIATE_DOMAINS
    )
    excerpt = _make_excerpt_from_text(raw_body)

    # Initialize WP client
    wp = WordPressClient(
        base_url=SETTINGS.WP_BASE_URL,
        username=SETTINGS.WP_USERNAME,
        application_password=SETTINGS.WP_APP_PASSWORD,
    )
    print(f"Endpoint: {wp.posts_endpoint}")

    # Upsert by exact title
    matches = wp.search_posts(title=topic, per_page=5)
    match_id = next(
        (
            p["id"]
            for p in matches
            if p.get("title", {}).get("rendered", "").strip().lower()
            == topic.lower()
        ),
        None,
    )

    if match_id:
        print(f"Updating existing post id={match_id} title='{topic}'")
        post_id = wp.update_post(
            post_id=match_id,
            title=topic,
            html_content=normalized_html,
            excerpt=excerpt,
            status=os.getenv("WP_STATUS", "publish"),
        )
    else:
        print(f"Creating new post title='{topic}'")
        if getattr(SETTINGS, "DRY_RUN", False):
            print("DRY_RUN=1 → not posting. Preview:\n", normalized_html[:800])
            return

        post_id = wp.create_post(
            title=topic,
            html_content=normalized_html,
            excerpt=excerpt,
            status=os.getenv("WP_STATUS", "publish"),
        )

    print(f"Post ID: {post_id}")


if __name__ == "__main__":
    main()
