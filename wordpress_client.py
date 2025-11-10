import os
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin
import random

# Environment variables
WP_URL = os.getenv("WP_URL", "").strip()
WP_USERNAME = os.getenv("WP_USERNAME", "").strip()
WP_PASSWORD = os.getenv("WP_PASSWORD", "").strip()
SITE_BASE = os.getenv("SITE_BASE", "").strip()


# ----------------------------
# 🔹 Helper: Upload Image to WP
# ----------------------------
def upload_image_to_wordpress(image_url, alt_text="Featured Image"):
    """
    Downloads an image from a remote URL and uploads it to WordPress media library.
    Returns the uploaded image ID if successful.
    """
    try:
        image_data = requests.get(image_url).content
        filename = image_url.split("/")[-1]
        media_endpoint = WP_URL.replace("/posts", "/media")

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "image/jpeg",
        }

        response = requests.post(
            media_endpoint,
            headers=headers,
            data=image_data,
            auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD),
        )

        if response.status_code in [200, 201]:
            media_id = response.json().get("id")
            print(f"✅ Uploaded image {filename} (ID: {media_id})")
            return media_id
        else:
            print(f"⚠️ Failed to upload image: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Image upload error: {e}")
        return None


# ----------------------------
# 🔹 Helper: Get Random Posts
# ----------------------------
def get_existing_posts(limit=10):
    """
    Fetches a few existing published posts to create internal links.
    """
    try:
        response = requests.get(
            WP_URL + "?per_page=" + str(limit) + "&status=publish",
            auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD),
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"⚠️ Could not fetch posts for internal links: {e}")
        return []


# ----------------------------
# 🔹 Helper: Add Internal/External Links
# ----------------------------
def add_links_to_content(content):
    """
    Inserts 2 internal and 1 external link in the article body.
    """
    internal_links = []
    posts = get_existing_posts(limit=15)

    for post in posts:
        if "link" in post:
            internal_links.append(post["link"])

    if internal_links:
        selected = random.sample(internal_links, min(2, len(internal_links)))
        for link in selected:
            content += f'\n<p>Read more: <a href="{link}">{link.split("/")[-2].replace("-", " ").title()}</a></p>'

    # External link example (Amazon)
    content += '\n<p>Check out our favorite picks on <a href="https://www.amazon.com" target="_blank" rel="nofollow noopener">Amazon</a>.</p>'
    return content


# ----------------------------
# 🔹 Main: Create WordPress Post
# ----------------------------
def create_wordpress_post(title, content, image_url=None, image_alt=None, focus_keyword=None, meta_description=None, category_ids=None, tags=None):
    """
    Publishes a new post with SEO, image, and linking.
    """
    try:
        # Add internal & external links
        content = add_links_to_content(content)

        # Upload image
        featured_media = None
        if image_url:
            featured_media = upload_image_to_wordpress(image_url, alt_text=image_alt or title)

        # Enforce meta character limits
        if meta_description and len(meta_description) > 160:
            meta_description = meta_description[:157] + "..."

        if len(title) > 60:
            title = title[:57] + "..."

        data = {
            "title": title,
            "content": content,
            "status": "publish",
        }

        if featured_media:
            data["featured_media"] = featured_media
        if category_ids:
            data["categories"] = category_ids
        if tags:
            data["tags"] = tags

        # Add SEO meta fields (AIOSEO/Yoast)
        meta_fields = {}
        if focus_keyword:
            meta_fields["aioseo_focus_keyphrase"] = focus_keyword
        if meta_description:
            meta_fields["aioseo_description"] = meta_description

        if meta_fields:
            data["meta"] = meta_fields

        # Post to WP
        response = requests.post(
            WP_URL,
            json=data,
            auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD),
        )

        if response.status_code in [200, 201]:
            post_id = response.json().get("id")
            print(f"✅ WordPress post published successfully: {title} (ID: {post_id})")
            return post_id
        else:
            print(f"⚠️ Failed to create post: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error creating post: {e}")
        return None