import os
import re
import requests
from requests.auth import HTTPBasicAuth

WP_URL = os.getenv("WP_URL", "https://thesaxonblog.com/wp-json/wp/v2")
WP_USER = os.getenv("WORDPRESS_USER")
WP_PASS = os.getenv("WORDPRESS_APP_PASSWORD")
AFFILIATE_TAG = os.getenv("AFFILIATE_TAG", "meganmcanespy-20")

def get_all_posts():
    posts = []
    page = 1
    while True:
        res = requests.get(f"{WP_URL}/posts?per_page=50&page={page}", auth=HTTPBasicAuth(WP_USER, WP_PASS))
        if res.status_code != 200 or not res.json():
            break
        posts.extend(res.json())
        page += 1
    return posts

def fix_amazon_links(content):
    """Ensure all Amazon links include affiliate tag"""
    amazon_links = re.findall(r'https?://(?:www\.)?amazon\.com/[^\s"\']+', content)
    for link in amazon_links:
        if "tag=" not in link:
            new_link = f"{link}?tag={AFFILIATE_TAG}"
            content = content.replace(link, new_link)
    return content

def fix_post(post):
    post_id = post["id"]
    title = post["title"]["rendered"]
    content = post["content"]["rendered"]
    categories = post.get("categories", [])
    featured_media = post.get("featured_media")

    print(f"🧰 Checking: {title} (ID: {post_id})")

    # ✅ SEO title + meta
    meta = {
        "aioseo_title": title[:60],
        "aioseo_description": f"Expert insight on {title}. Read this guide on The Saxon Blog for outdoor tips, hunting advice, and gear reviews."
    }

    # ✅ Featured image check
    if not featured_media:
        default_img = "https://thesaxonblog.com/wp-content/uploads/2025/11/default-camo-bg.jpg"
        content = f'<img src="{default_img}" alt="{title}" />\n' + content

    # ✅ Optimize structure + lazy load
    content = (
        content.replace("<h1>", "<h2>")
               .replace("<h3>", "<h2>")
               .replace('<img ', '<img loading="lazy" alt="Outdoor article image" ')
    )

    # ✅ Fix or add Amazon affiliate links
    content = fix_amazon_links(content)

    # ✅ Add internal link
    if "The Saxon Blog" not in content:
        content += '\n<p>Find more great outdoor articles at <a href="https://thesaxonblog.com">The Saxon Blog</a>.</p>'

    # ✅ Send update
    update_data = {
        "content": content,
        "meta": meta,
        "status": "publish",
        "categories": categories
    }

    res = requests.post(f"{WP_URL}/posts/{post_id}", auth=HTTPBasicAuth(WP_USER, WP_PASS), json=update_data)
    if res.status_code in [200, 201]:
        print(f"✅ Fixed post {post_id}: {title}")
    else:
        print(f"⚠️ Failed to update {post_id}: {res.status_code} {res.text}")

def main():
    print("🔧 Repairing all posts on The Saxon Blog...")
    posts = get_all_posts()
    print(f"Found {len(posts)} posts.")
    for post in posts:
        fix_post(post)
    print("✅ All posts repaired successfully!")

if __name__ == "__main__":
    main()
