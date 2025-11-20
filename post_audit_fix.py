"""
post_audit_fix_resumable.py
One-time WordPress post fixer with retry + delay.
Resumes after connection errors and logs every change.
"""

import os, json, time, requests, openai
from datetime import datetime
from affiliate_injector import inject_affiliate_links, load_affiliate_products
from ai_product_recommender import generate_product_suggestions, create_amazon_links
from image_handler import get_featured_image_id
from wordpress_client import WordPressClient

# === ENVIRONMENT ===
BASE = os.getenv("WP_BASE_URL").rstrip("/")
USERNAME = os.getenv("WP_USERNAME")
APP_PASS = os.getenv("WP_APP_PASSWORD")
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# === LOGGING ===
LOG_FILE = "/app/audit_log.txt"
def log(msg):
    msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

# === HELPERS ===
def generate_excerpt(content, title):
    prompt = f"Write a concise, SEO-friendly 2-sentence excerpt for a blog post titled '{title}'."
    try:
        resp = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        log(f"[WARN] Excerpt generation failed: {e}")
        return content[:200] + "..."

def generate_meta(title):
    prompt = f"Generate SEO title and meta description for a post titled '{title}'. Return JSON with keys 'title' and 'description'."
    try:
        resp = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )
        text = resp.choices[0].message.content.strip()
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end+1]
        data = json.loads(text)
        return data.get("title", title), data.get("description", "")
    except Exception as e:
        log(f"[WARN] Meta generation failed: {e}")
        return title, f"Explore {title} tips from The Saxon Blog."

def safe_put(client, url, data, retries=3):
    """Retry PUT requests safely up to 3 times."""
    for attempt in range(1, retries + 1):
        try:
            r = client.session.put(url, json=data, timeout=25)
            if r.status_code in (200, 201):
                return True
            else:
                log(f"[WARN] PUT failed ({r.status_code}): {r.text[:120]}")
        except requests.exceptions.RequestException as e:
            log(f"[WARN] Connection error on attempt {attempt}: {e}")
        time.sleep(2)
    log("[ERROR] Max retries reached, skipping post.")
    return False

# === MAIN ===
def main():
    client = WordPressClient()
    page, per_page = 1, 25
    products = load_affiliate_products()

    while True:
        url = f"{BASE}/wp-json/wp/v2/posts?status=publish&per_page={per_page}&page={page}"
        try:
            r = requests.get(url, auth=(USERNAME, APP_PASS), timeout=30)
            if r.status_code == 400:
                log("[DONE] No more posts found. Exiting.")
                break
            r.raise_for_status()
        except Exception as e:
            log(f"[WARN] Failed to fetch page {page}: {e}")
            time.sleep(5)
            continue

        posts = r.json()
        if not posts:
            log("[DONE] No posts returned, ending run.")
            break

        for p in posts:
            pid, title = p["id"], p["title"]["rendered"]
            content = p["content"]["rendered"]
            changed = []
            log(f"[PROCESSING] Post {pid}: {title}")

            # === 1️⃣ FEATURED IMAGE ===
            if not p.get("featured_media") or p["featured_media"] == 0:
                media_id = get_featured_image_id(title)
                if media_id:
                    safe_put(client, f"{client.api_url}/posts/{pid}", {"featured_media": media_id})
                    changed.append("featured_image")

            # === 2️⃣ EXCERPT ===
            if not p.get("excerpt") or not p["excerpt"]["rendered"].strip():
                excerpt = generate_excerpt(content, title)
                safe_put(client, f"{client.api_url}/posts/{pid}", {"excerpt": excerpt})
                changed.append("excerpt")

            # === 3️⃣ META ===
            meta_title, meta_desc = generate_meta(title)
            safe_put(client, f"{client.api_url}/posts/{pid}",
                     {"meta": {"_yoast_wpseo_title": meta_title, "_yoast_wpseo_metadesc": meta_desc}})
            changed.append("meta")

            # === 4️⃣ AFFILIATE + INTERNAL LINKS ===
            product_names = generate_product_suggestions(content)
            dynamic_products = create_amazon_links(product_names)
            all_products = dynamic_products + products
            updated_content = inject_affiliate_links(content, all_products)

            cats = p.get("categories", [])
            if cats:
                cat_id = cats[0]
                try:
                    related = requests.get(
                        f"{BASE}/wp-json/wp/v2/posts?categories={cat_id}&per_page=3",
                        auth=(USERNAME, APP_PASS), timeout=20
                    ).json()
                    for rpost in related:
                        if rpost["id"] != pid:
                            link = rpost["link"]
                            if link not in updated_content:
                                updated_content += f'<p>Related: <a href="{link}">{rpost["title"]["rendered"]}</a></p>'
                except Exception as e:
                    log(f"[WARN] Related post fetch failed: {e}")

            safe_put(client, f"{client.api_url}/posts/{pid}", {"content": updated_content})
            changed.append("links")

            if changed:
                log(f"[FIXED] Post {pid} ({title}): {', '.join(changed)}")

            # Add delay to avoid rate limit
            time.sleep(3)

        total_pages = int(r.headers.get("X-WP-TotalPages", page))
        if page >= total_pages:
            break
        page += 1

    log("[COMPLETE] All posts processed successfully.")

if __name__ == "__main__":
    main()
