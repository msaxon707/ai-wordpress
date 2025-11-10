import os
import logging
import re
import requests
from urllib.parse import quote_plus

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ---------- Environment ----------
WP_URL = os.getenv("WP_URL")  # should be .../wp-json/wp/v2/posts
WP_USERNAME = os.getenv("WP_USERNAME") or os.getenv("WORDPRESS_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD") or os.getenv("WORDPRESS_APP_PASSWORD")
SITE_BASE = os.getenv("SITE_BASE", "https://thesaxonblog.com")
AFFILIATE_TAG = os.getenv("AFFILIATE_TAG", "meganmcanespy-20")

if not (WP_URL and WP_USERNAME and WP_PASSWORD):
    logging.error("Missing WP_URL or WP_USERNAME or WP_PASSWORD")
    raise SystemExit(1)

# ---------- Categories ----------
CATEGORIES = {
    "dogs": 11,
    "deer-season": 36,
    "hunting": 38,
    "recipes": 54,
    "fishing": 91,
    "outdoor-living": 90,
    "survival-bushcraft": 92,
}


def guess_category_from_title(title: str):
    t = title.lower()
    if any(w in t for w in ["dog", "puppy", "bird dog", "gsp"]):
        return CATEGORIES["dogs"]
    if any(w in t for w in ["recipe", "smoked", "fried", "campfire", "cook", "grill"]):
        return CATEGORIES["recipes"]
    if any(w in t for w in ["trout", "bass", "crappie", "fishing", "river", "lake"]):
        return CATEGORIES["fishing"]
    if any(w in t for w in ["rut", "deer season", "early season", "late season"]):
        return CATEGORIES["deer-season"]
    if any(w in t for w in ["bushcraft", "survival"]):
        return CATEGORIES["survival-bushcraft"]
    if any(w in t for w in ["camp", "tent", "gear review", "gear"]):
        return CATEGORIES["outdoor-living"]
    if any(w in t for w in ["deer", "bowhunting", "rifle", "muzzleloader", "hunt"]):
        return CATEGORIES["hunting"]
    return None


def derive_focus_keyword_from_title(title: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", title)
    return cleaned.lower().strip()


def build_affiliate_cta_from_title(title: str) -> str:
    t = title.lower()
    if "dog" in t or "puppy" in t:
        term = "hunting dog supplies"
    elif "trout" in t or "bass" in t or "fishing" in t:
        term = "fishing tackle"
    elif "recipe" in t or "smoked" in t or "campfire" in t:
        term = "campfire cooking gear"
    elif "bushcraft" in t or "survival" in t:
        term = "survival gear"
    elif "deer" in t:
        term = "deer hunting gear"
    else:
        term = "outdoor gear"

    url = f"https://www.amazon.com/s?k={quote_plus(term)}&tag={AFFILIATE_TAG}"
    return f"""
<div class="affiliate-cta">
  <p><strong>Recommended gear:</strong> Want to upgrade your setup? Check out our favorite
    <a href="{url}" target="_blank" rel="nofollow sponsored noopener">Amazon picks</a> before your next trip.
  </p>
</div>
""".strip()


def clean_html_content(html: str) -> str:
    # Remove ```html, ``` and stray “`html etc.
    html = re.sub(r"`{3,}.*?`{3,}", "", html, flags=re.DOTALL)
    html = re.sub(r"[“”]`?html", "", html, flags=re.IGNORECASE)
    html = re.sub(r"</?html[^>]*>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"</?body[^>]*>", "", html, flags=re.IGNORECASE)
    return html.strip()


def extract_first_image_src(html: str):
    m = re.search(r'src="([^"]+)"', html)
    if m:
        return m.group(1)
    return None


def get_all_posts():
    all_posts = []
    page = 1
    while True:
        logging.info("Fetching posts page %d...", page)
        resp = requests.get(
            WP_URL,
            params={"per_page": 100, "page": page},
            auth=(WP_USERNAME, WP_PASSWORD),
            timeout=30,
        )
        if resp.status_code == 400 and "rest_post_invalid_page_number" in resp.text:
            break
        if resp.status_code != 200:
            logging.error("Error fetching posts page %d: %s", page, resp.text[:300])
            break
        batch = resp.json()
        if not batch:
            break
        all_posts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    logging.info("Total posts found: %d", len(all_posts))
    return all_posts


def repair_post(post: dict):
    post_id = post.get("id")
    title = post.get("title", {}).get("rendered", "")
    content = post.get("content", {}).get("rendered", "")
    categories = post.get("categories", []) or []
    meta = post.get("meta", {}) or {}

    original_content = content
    original_categories = list(categories)
    original_meta = dict(meta)

    # 1) Clean weird HTML wrappers
    content = clean_html_content(content)

    # 2) Ensure FIFU featured image from first <img> if missing
    if not meta.get("fifu_image_url"):
        img_src = extract_first_image_src(content)
        if img_src:
            meta["fifu_image_url"] = img_src

    # 3) Guess category if missing
    if not categories:
        guessed = guess_category_from_title(title)
        if guessed:
            categories = [guessed]

    # 4) Ensure affiliate CTA exists
    if "affiliate-cta" not in content:
        cta_html = build_affiliate_cta_from_title(title)
        content = content.strip() + "\n\n" + cta_html

    # 5) Add simple focus keyword for AIOSEO (best effort)
    focus_kw = derive_focus_keyword_from_title(title)
    if focus_kw:
        meta["_aioseo_focus_keyphrase"] = focus_kw

    # Check if anything changed
    changed = (
        content != original_content
        or categories != original_categories
        or meta != original_meta
    )

    if not changed:
        logging.info("Post %s: nothing to change.", post_id)
        return

    payload = {"content": content}
    if categories:
        payload["categories"] = categories
    if meta:
        payload["meta"] = meta

    logging.info("Updating post %s (%s)...", post_id, title)
    resp = requests.post(
        f"{WP_URL}/{post_id}",
        json=payload,
        auth=(WP_USERNAME, WP_PASSWORD),
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        logging.error("Error updating post %s: %s", post_id, resp.text[:500])
    else:
        logging.info("✅ Repaired post %s", post_id)


def main():
    logging.info("🔧 Repairing all posts on The Saxon Blog...")
    posts = get_all_posts()
    if not posts:
        logging.info("No posts found.")
        return

    for p in posts:
        try:
            repair_post(p)
        except Exception as e:
            logging.exception("Error repairing post %s: %s", p.get("id"), e)

    logging.info("✅ All posts repaired successfully!")


if __name__ == "__main__":
    main()
