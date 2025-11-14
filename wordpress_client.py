import requests
import base64
import os
import re
from config import CATEGORIES, AUTO_CATEGORY_MAP, TOPIC_POOL

SITE_BASE = os.getenv("SITE_BASE", "")


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def _resolve_category(topic, manual_category):
    # 1. If topic has manually assigned category
    if manual_category:
        return CATEGORIES.get(manual_category)

    # 2. Auto-infer category based on keywords
    lower = topic.lower()
    for key, cat in AUTO_CATEGORY_MAP.items():
        if key in lower:
            return CATEGORIES.get(cat)

    # fallback
    return CATEGORIES.get("outdoors")


def create_wordpress_post(
    wp_url,
    username,
    password,
    title,
    content,
    image_url=None,
    image_alt=None,
    mime_type="image/jpeg",
    affiliate_tag=None,
    category=None,
):
    # Affiliate Section
    if affiliate_tag:
        content += f"""
        <p><strong>Looking for gear?</strong> 
        <a href="{SITE_BASE}?tag={affiliate_tag}" target="_blank" rel="noopener">
        Shop recommended products here.</a></p>
        """

    # Duplicate check
    slug = _slugify(title)
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {"Authorization": "Basic " + auth}

    check = requests.get(wp_url, headers=headers, params={"slug": slug})
    if check.ok and check.json():
        print(f"⚠️ Post with slug '{slug}' already exists. Skipping publish.")
        return None

    # Upload image
    featured_media_id = None
    if image_url:
        try:
            print("📸 Downloading featured image...")
            img = requests.get(image_url, timeout=15)
            mime = mime_type or "image/jpeg"

            print("📤 Uploading featured image to WordPress...")
            media_endpoint = wp_url.replace("/posts", "/media")

            media_headers = {
                "Authorization": "Basic " + auth,
                "Content-Disposition": f"attachment; filename=feature.{mime.split('/')[-1]}",
                "Content-Type": mime,
            }

            upload = requests.post(media_endpoint, headers=media_headers, data=img.content)

            if upload.status_code in [200, 201]:
                featured_media_id = upload.json().get("id")
                print(f"✅ Uploaded image ID: {featured_media_id}")

                # update alt text
                if image_alt:
                    requests.post(
                        f"{media_endpoint}/{featured_media_id}",
                        headers={"Authorization": "Basic " + auth, "Content-Type": "application/json"},
                        json={"alt_text": image_alt},
                    )

            else:
                print(f"⚠️ Failed to upload image: {upload.status_code} - {upload.text}")

        except Exception as e:
            print(f"❌ Error uploading image: {e}")

    # Determine category
    resolved_category = _resolve_category(title, category)

    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [resolved_category] if resolved_category else [],
    }
    if featured_media_id:
        post_data["featured_media"] = featured_media_id

    print("📰 Publishing post to WordPress...")
    final = requests.post(wp_url, headers={**headers, "Content-Type": "application/json"}, json=post_data)

    if final.status_code in [200, 201]:
        post_id = final.json().get("id")
        print(f"🎉 Successfully posted! ID: {post_id}")
        return post_id

    print(f"❌ Failed to publish post: {final.status_code} - {final.text}")
    return None