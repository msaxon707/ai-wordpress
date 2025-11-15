# =========================
# path: ai_script.py  (REPLACE FILE)
# =========================
import os
from typing import Optional, List
from openai import OpenAI
from config import SETTINGS
from content_normalizer import normalize_post_html
from wordpress_client import WordPressClient

PLACEHOLDER_TOPICS = {"sample topic", "topic", "test", "hello world"}

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

def main():
    topic = os.environ.get("TOPIC", "").strip()
    if not topic or topic.lower() in PLACEHOLDER_TOPICS:
        raise SystemExit("Refusing to post without a real TOPIC. Set TOPIC to a meaningful title.")

    include_links_env = os.environ.get("INCLUDE_LINKS", "")
    include_links = [u.strip() for u in include_links_env.split(",") if u.strip()] or None

    # Generate + normalize
    raw_body = _call_ai_to_generate_body(topic=topic, include_links=include_links)
    normalized_html = normalize_post_html(raw_body, affiliate_domains=SETTINGS.AFFILIATE_DOMAINS)
    excerpt = _make_excerpt_from_text(raw_body)

    # WP client
    wp = WordPressClient(
        base_url=SETTINGS.WP_BASE_URL,
        username=SETTINGS.WP_USERNAME,
        application_password=SETTINGS.WP_APP_PASSWORD,
    )
    print(f"Endpoint: {wp.posts_endpoint}")

    # --- UPSERT LOGIC ---
    # 1) See if a post with the same title already exists.
    matches = wp.search_posts(title=topic, per_page=5)
    match_id = next((p["id"] for p in matches if (p.get("title", {}).get("rendered","").strip().lower() == topic.lower())), None)

    if match_id:
        # Update in place
        print(f"Updating existing post id={match_id} title='{topic}'")
        post_id = wp.update_post(
            post_id=match_id,
            title=topic,
            html_content=normalized_html,
            excerpt=excerpt,
            status=os.getenv("WP_STATUS", "publish"),
        )
    else:
        # Create new
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
