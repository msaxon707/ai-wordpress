# =========================
# ai_script.py
# =========================
import os
import sys
import argparse
from typing import Optional, List

import requests
from openai import OpenAI

from config import SETTINGS
from content_normalizer import normalize_post_html
from wordpress_client import WordPressClient
from image_handler import get_featured_image_url

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
            f"<h2>{topic}</h2>"
            f"<p>This is a sample article body about <strong>{topic}</strong>.</p>"
            f"<ul><li>Point one</li><li>Point two</li></ul>"
            f"<p>Visit https://example.com for more info.</p>{links}"
        )

    client = OpenAI(api_key=SETTINGS.OPENAI_API_KEY)

    system_prompt = (
        "You are a blogging assistant for an outdoors / country lifestyle blog. "
        "Output STRICT HTML only using: <h2>, <p>, <ul>, <ol>, <li>, <a>. "
        "No Markdown. No code fences. Keep paragraphs short, scannable, and SEO-friendly. "
        "Work in affiliate-style product mentions when natural."
    )

    user_prompt = f"Write a full blog article on: {topic}."
    if include_links:
        user_prompt += (
            "\nWeave these links naturally into the article as recommendations: "
            + ", ".join(include_links)
        )

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
        if not SETTINGS.OPENAI_API_KEY:
            sys.exit("No topic and no OPENAI_API_KEY; cannot auto-generate.")
        client = OpenAI(api_key=SETTINGS.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=SETTINGS.OPENAI_MODEL,
            max_tokens=48,
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Generate a single SEO-optimized blog topic for an outdoors / "
                        "country / family lifestyle blog. Respond with ONLY the title, "
                        "no quotes, no punctuation at the end."
                    ),
                },
                {
                    "role": "user",
                    "content": "Give me one good blogging topic for today.",
                },
            ],
        )
        topic = (resp.choices[0].message.content or "").strip()

    # Process include-links
    include_links = [
        u.strip()
        for u in (args.include_links or os.getenv("INCLUDE_LINKS", "")).split(",")
        if u.strip()
    ] or None

    # Always allow posting since we generate a real topic
    force = True or args.force

    return topic, force, include_links


# -------------------------
# FEATURED IMAGE
# -------------------------
def _maybe_upload_featured_image(wp: WordPressClient, topic: str) -> Optional[int]:
    """
    Try Pexels/Unsplash first via image_handler; if successful, upload to WP media and
    return the media ID. If anything fails, log and return None.
    """
    try:
        img_url, alt_text, mime_type = get_featured_image_url(topic)
        if not img_url:
            print("⚠️ No image URL returned for topic; skipping featured image.")
            return None

        print(f"📸 Downloading featured image from: {img_url}")
        resp = requests.get(img_url, timeout=20)
        resp.raise_for_status()
        image_bytes = resp.content

        # Derive filename
        filename = img_url.split("/")[-1].split("?")[0] or "featured.jpg"
        if "." not in filename:
            # Fallback extension based on mime_type
            if (mime_type or "").lower() == "image/png":
                filename += ".png"
            else:
                filename += ".jpg"

        media_id = wp.upload_image_from_bytes(
            image_bytes=image_bytes,
            filename=filename,
            mime_type=mime_type or "image/jpeg",
            alt_text=alt_text or f"{topic.title()} photo",
        )
        print(f"✅ Uploaded featured image, media_id={media_id}")
        return media_id

    except Exception as e:
        print(f"⚠️ Featured image upload failed: {e}")
        return None


# -------------------------
# MAIN
# -------------------------
def main():
    topic, force, include_links = _resolve_topic()
    print(f"🧠 Using topic: {topic!r}")

    # Prevent accidental junk posts
    if (topic.lower() in PLACEHOLDER_TOPICS) and not force:
        sys.exit(
            "Refusing to post without a real TOPIC. "
            "Use --topic 'Your Title' or env TOPIC=MyTitle. Add --force to override."
        )

    # Generate + normalize body
    print("✍️ Generating article body with OpenAI…")
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
    print(f"🔌 WordPress endpoint: {wp.posts_endpoint}")

    # Featured image (best effort)
    featured_media_id = _maybe_upload_featured_image(wp, topic)

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

    status = os.getenv("WP_STATUS", "publish")

    if match_id:
        print(f"♻️ Updating existing post id={match_id} title='{topic}'")
        post_id = wp.update_post(
            post_id=match_id,
            title=topic,
            html_content=normalized_html,
            excerpt=excerpt,
            status=status,
            featured_media=featured_media_id,
        )
    else:
        print(f"🆕 Creating new post title='{topic}'")
        if getattr(SETTINGS, "DRY_RUN", False):
            print("DRY_RUN=1 → not posting. Preview:\n", normalized_html[:800])
            return

        post_id = wp.create_post(
            title=topic,
            html_content=normalized_html,
            excerpt=excerpt,
            status=status,
            featured_media=featured_media_id,
        )

    print(f"✅ Done. Post ID: {post_id}")


if __name__ == "__main__":
    main()
