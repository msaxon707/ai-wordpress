import os
import requests
import openai
import random
from urllib.parse import urlencode

# ENV VARIABLES
WP_URL = os.getenv("WP_URL", "https://thesaxonblog.com/wp-json/wp/v2/posts")
WP_USER = os.getenv("WP_USERNAME")
WP_PASS = os.getenv("WP_PASSWORD")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
SITE_BASE = os.getenv("SITE_BASE", "https://thesaxonblog.com")
AUTH = (WP_USER, WP_PASS)
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-3.5-turbo"

def get_all_posts():
    posts = []
    page = 1
    while True:
        res = requests.get(WP_URL, params={"per_page": 100, "page": page, "status": "publish"})
        if res.status_code != 200 or not res.json():
            break
        posts.extend(res.json())
        page += 1
    return posts

def fetch_featured_image(topic):
    query = urlencode({"query": topic, "per_page": 1})
    res = requests.get(f"https://api.pexels.com/v1/search?{query}", headers={"Authorization": PEXELS_API_KEY})
    if res.status_code == 200 and res.json().get("photos"):
        return res.json()["photos"][0]["src"]["large"]
    return None

def upload_image_to_wp(image_url, title):
    img_data = requests.get(image_url).content
    filename = f"{title[:40].replace(' ', '_')}.jpg"
    media_url = SITE_BASE + "/wp-json/wp/v2/media"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    res = requests.post(media_url, headers=headers, data=img_data, auth=AUTH)
    return res.json().get("id") if res.status_code == 201 else None

def generate_meta(title, content):
    """Fix or generate SEO meta title/description."""
    prompt = f"Generate an SEO title (≤60 chars) and a 160-character meta description for: {title}\n\n{content[:800]}"
    completion = openai.ChatCompletion.create(model=MODEL, messages=[{"role": "user", "content": prompt}])
    response = completion.choices[0].message["content"].split("\n")
    seo_title = response[0][:60]
    meta_desc = response[-1][:160]
    return seo_title, meta_desc

def ensure_links(content):
    """Guarantee at least two internal and two external links."""
    res = requests.get(WP_URL, params={"per_page": 10, "status": "publish"})
    if res.status_code == 200:
        posts = res.json()
        if posts:
            internal_links = [f'<a href="{p["link"]}" target="_blank">{p["title"]["rendered"]}</a>' for p in random.sample(posts, min(2, len(posts)))]
            for link in internal_links:
                if link not in content:
                    content += f"\n<p>{link}</p>"
    if "amazon.com" not in content.lower():
        content += '\n<p><a href="https://www.amazon.com/" target="_blank" rel="nofollow noopener">Buy on Amazon</a></p>'
    return content

def repair_post(post):
    title = post["title"]["rendered"]
    content = post["content"]["rendered"]
    needs_update = False

    # Featured image fix
    if not post.get("featured_media"):
        image_url = fetch_featured_image(title)
        if image_url:
            img_id = upload_image_to_wp(image_url, title)
            post["featured_media"] = img_id
            needs_update = True

    # Category fix
    if not post.get("categories"):
        post["categories"] = ["Outdoors"]
        needs_update = True

    # SEO meta fix
    meta = post.get("meta", {})
    if "_aioseo_description" not in meta or not meta["_aioseo_description"]:
        seo_title, meta_desc = generate_meta(title, content)
        meta["_aioseo_title"] = seo_title
        meta["_aioseo_description"] = meta_desc
        meta["_aioseo_keywords"] = title.split()[0]
        post["meta"] = meta
        needs_update = True

    # Internal + external links fix
    if "href=" not in content or "amazon" not in content.lower():
        post["content"]["rendered"] = ensure_links(content)
        needs_update = True

    if needs_update:
        data = {
            "title": title,
            "content": post["content"]["rendered"],
            "meta": post.get("meta", {}),
            "categories": post.get("categories", []),
            "featured_media": post.get("featured_media")
        }
        res = requests.post(f"{WP_URL}/{post['id']}", auth=AUTH, json=data)
        if res.status_code in [200, 201]:
            print(f"✅ Repaired: {title}")
        else:
            print(f"⚠️ Failed: {title} ({res.text})")

def main():
    print("🔧 Repairing all posts on The Saxon Blog...")
    posts = get_all_posts()
    print(f"Found {len(posts)} posts.")
    for p in posts:
        repair_post(p)
    print("✅ All posts repaired successfully!")

if __name__ == "__main__":
    main()