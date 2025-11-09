import os, re, logging, requests, urllib.parse
from datetime import datetime, timedelta

WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")
AMAZON_TAG = os.getenv("AMAZON_TAG", "meganmcanespy-20")
SITE_NAME = os.getenv("SITE_NAME", "The Saxon Blog")
REPAIR_DAYS = int(os.getenv("REPAIR_DAYS", "3650"))

if not all([WP_URL, WP_USERNAME, WP_PASSWORD]):
    raise RuntimeError("Missing WordPress credentials.")

API_BASE = WP_URL.rsplit("/posts", 1)[0]
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

IMG_SRC_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.I)


def build_cta(title):
    query = urllib.parse.quote_plus(title or "outdoor gear")
    return f'<div class="affiliate-cta"><p><strong>Recommended Gear:</strong> <a href="https://www.amazon.com/s?k={query}&tag={AMAZON_TAG}" target="_blank" rel="nofollow noopener">View Amazon picks</a>.</p></div>'


def list_posts():
    cutoff = datetime.utcnow() - timedelta(days=REPAIR_DAYS)
    page = 1
    while True:
        r = requests.get(f"{API_BASE}/posts", params={"per_page": 100, "page": page}, auth=(WP_USERNAME, WP_PASSWORD))
        if r.status_code != 200:
            break
        posts = r.json()
        if not posts:
            break
        for p in posts:
            date_str = p.get("date_gmt") or p.get("date")
            if not date_str:
                continue
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if dt >= cutoff:
                yield p["id"]
        page += 1


def fix_post(pid):
    r = requests.get(f"{API_BASE}/posts/{pid}", params={"context": "edit"}, auth=(WP_USERNAME, WP_PASSWORD))
    if r.status_code != 200:
        return False
    post = r.json()
    html = post.get("content", {}).get("rendered", "")
    title = post["title"]["rendered"]
    meta = post.get("meta", {})

    changed = False
    if "affiliate-cta" not in html:
        html += "\n\n" + build_cta(title)
        changed = True
    if not meta.get("fifu_image_url"):
        m = IMG_SRC_RE.search(html)
        if m:
            meta["fifu_image_url"] = m.group(1)
            changed = True
    if not meta.get("_aioseo_focus_keyword"):
        meta["_aioseo_focus_keyword"] = title[:60]
        changed = True

    if not changed:
        return False

    payload = {"content": html, "meta": meta}
    r = requests.post(f"{API_BASE}/posts/{pid}", json=payload, auth=(WP_USERNAME, WP_PASSWORD))
    if r.status_code in (200, 201):
        logger.info(f"✅ Repaired {pid}: {title}")
        return True
    return False


def main():
    logger.info(f"Repairing posts for {SITE_NAME}")
    updated = 0
    for pid in list_posts():
        if fix_post(pid):
            updated += 1
    logger.info(f"Finished — {updated} posts updated.")


if __name__ == "__main__":
    main()
