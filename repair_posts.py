import os
import re
import requests
from requests.auth import HTTPBasicAuth

# In your Coolify env, WP_URL is already the posts endpoint:
# https://thesaxonblog.com/wp-json/wp/v2/posts
WP_POSTS_ENDPOINT = os.getenv(
    "WP_URL", "https://thesaxonblog.com/wp-json/wp/v2/posts"
)

WORDPRESS_USER = os.getenv("WORDPRESS_USER")
WORDPRESS_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")
AFFILIATE_TAG = os.getenv("AFFILIATE_TAG", "meganmcanespy-20")

auth = HTTPBasicAuth(WORDPRESS_USER, WORDPRESS_APP_PASSWORD)


def get_all_posts():
    posts = []
    page = 1
    while True:
        url = f"{WP_POSTS_ENDPOINT}?per_page=50&page={page}"
        res = requests.get(url, auth=auth)

        if res.status_code != 200:
            print(f"⚠️ Error fetching page {page}: {res.status_code} {res.text[:200]}")
            break

        data = res.json()
        if not data:
            break

        posts.extend(data)
        page += 1

    return posts


def fix_amazon_links(content: str) -> str:
    """Ensure all Amazon links include your affiliate tag."""
    amazon_links = re.findall(r'https?://(?:www\.)?amazon\.com/[^\s"\']+', content)
    for link in amazon_links:
        if "tag=" not in link:
            sep = "&" if "?" in link else "?"
            new_link = f"{link}{sep}tag={AFFILIATE_TAG}"
            content = content.replace(link, new_link)
    return content


def fix_post(post: dict):
    post_id = post["id"]
    title = post.get("title", {}).get("rendered", f"Post {post_id}")
    content = post.get("content", {}).get("rendered", "")
    categories = post.get("categories", [])
    featured_media = post.get("featured_media")

    print(f"🧰 Checking: {title} (ID: {post_id})")

    # ✅ SEO title + meta
    meta = {
        "aioseo_title": title[:60],
        "aioseo_description": (
            f"Expert insight on {title}. Read this guide on The Saxon Blog "
            f"for outdoor tips, hunting advice, and gear reviews."
        ),
    }

    # ✅ Featured image fallback (only if none set)
    if not featured_media:
        default_img = (
            "https://thesaxonblog.com/wp-content/uploads/2025/11/default-camo-bg.jpg"
        )
        if default_img not in content:
            content = f'<p><img src="{default_img}" alt="{title}" loading="lazy" /></p>\n' + content

    # ✅ Clean heading structure & lazy-loading
    content = (
        content.replace("<h1>", "<h2>")
        .replace("</h1>", "</h2>")
        .replace("<h3>", "<h2>")
        .replace("</h3>", "</h2>")
        .replace('<img ', '<img loading="lazy" ')
    )

    # ✅ Fix / add Amazon affiliate links
    content = fix_amazon_links(content)

    # ✅ Add internal link to home if missing
    if "thesaxonblog.com" not in content:
        content += (
            '\n<p>Find more great outdoor articles at '
            '<a href="https://thesaxonblog.com">The Saxon Blog</a>.</p>'
        )

    update_data = {
        "content": content,
        "meta": meta,
        "status": "publish",
        "categories": categories,
    }

    res = requests.post(
        f"{WP_POSTS_ENDPOINT}/{post_id}", auth=auth, json=update_data
    )
    if res.status_code in (200, 201):
        print(f"✅ Fixed post {post_id}: {title}")
    else:
        print(f"⚠️ Failed to update {post_id}: {res.status_code} {res.text[:200]}")


def main():
    if not WORDPRESS_USER or not WORDPRESS_APP_PASSWORD:
        print("❌ Missing WORDPRESS_USER or WORDPRESS_APP_PASSWORD")
        return

    print("🔧 Repairing all posts on The Saxon Blog...")
    posts = get_all_posts()
    print(f"Found {len(posts)} posts.")
    for post in posts:
        fix_post(post)
    print("✅ All posts repaired (loop finished).")


if __name__ == "__main__":
    main()
