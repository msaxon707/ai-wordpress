import requests, random, time

# === CONFIG ===
WORDPRESS_URL = "https://thesaxonblog.com"
USERNAME = "megansaxon9@gmail.com"
APP_PASSWORD = "YGUQ xn3F p3gm Haf2 lzzS j66Q"
UNSPLASH_TOPICS = ["hunting", "deer", "duck", "outdoors", "dogs", "country"]
HEADERS = {"Content-Type": "application/json"}
WP_API = f"{WORDPRESS_URL}/wp-json/wp/v2/posts"
MEDIA_API = f"{WORDPRESS_URL}/wp-json/wp/v2/media"

def get_posts():
    r = requests.get(WP_API, auth=(USERNAME, APP_PASSWORD), params={"per_page": 50})
    r.raise_for_status()
    return r.json()

def get_unsplash_image(keyword):
    try:
        key = random.choice(UNSPLASH_TOPICS)
        url = f"https://source.unsplash.com/random/1600x900/?{keyword or key}"
        return url
    except:
        return None

def upload_image(image_url, title):
    img_data = requests.get(image_url).content
    filename = title.replace(" ", "_") + ".jpg"
    r = requests.post(
        MEDIA_API,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
        data=img_data,
        auth=(USERNAME, APP_PASSWORD)
    )
    if r.status_code == 201:
        return r.json()["id"]
    return None

def fix_post(post):
    pid = post["id"]
    title = post["title"]["rendered"]
    modified = False

    # Fix missing featured image
    if not post.get("featured_media") or post["featured_media"] == 0:
        img_url = get_unsplash_image(title)
        media_id = upload_image(img_url, title)
        if media_id:
            requests.post(f"{WP_API}/{pid}", json={"featured_media": media_id}, auth=(USERNAME, APP_PASSWORD))
            print(f"🖼️ Added image for {title}")
            modified = True

    # Fix broken Amazon links
    content = post["content"]["rendered"]
    if "amazon.com" in content and "href=''" in content:
        content = content.replace("href=''", "")
        requests.post(f"{WP_API}/{pid}", json={"content": content}, auth=(USERNAME, APP_PASSWORD))
        print(f"🔗 Fixed links in {title}")
        modified = True

    # Add SEO keyword (All in One SEO)
    keyword = title.split(":")[0].split(" ")[0]
    requests.post(f"{WP_API}/{pid}", json={"aioseo_focuskw": keyword}, auth=(USERNAME, APP_PASSWORD))
    print(f"⚙️ SEO keyword added: {keyword}")

    if modified:
        print(f"✅ Updated {title}")
    else:
        print(f"➡️ No change for {title}")

def main():
    posts = get_posts()
    print(f"🦌 Checking {len(posts)} posts...")
    for post in posts:
        try:
            fix_post(post)
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ Error on {post['id']}: {e}")

if __name__ == "__main__":
    main()
