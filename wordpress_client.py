import os
import requests
from requests.auth import HTTPBasicAuth

# Environment variables
WP_URL = os.getenv("WP_URL", "").strip()
WP_USERNAME = os.getenv("WP_USERNAME", "").strip()
WP_PASSWORD = os.getenv("WP_PASSWORD", "").strip()


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
            print(f"✅ Uploaded image {filename} to WordPress (ID: {media_id})")
            return media_id
        else:
            print(f"⚠️ Failed to upload image: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Image upload error: {e}")
        return None


def create_wordpress_post(title, content, image_url=None, image_alt=None, focus_keyword=None, affiliate_tag=None):
    """
    Publishes a new WordPress post with SEO metadata and featured image.
    """
    try:
        # Upload featured image if provided
        featured_image_id = None
        if image_url:
            featured_image_id = upload_image_to_wordpress(image_url, image_alt or title)

        # Prepare post data
        data = {
            "title": title,
            "content": content,
            "status": "publish",
        }

        if featured_image_id:
            data["featured_media"] = featured_image_id

        # Add SEO meta fields if plugin (like AIOSEO) supports them
        meta_fields = {}
        if focus_keyword:
            meta_fields["aioseo_focus_keyphrase"] = focus_keyword
        if affiliate_tag:
            meta_fields["affiliate_tag"] = affiliate_tag

        if meta_fields:
            data["meta"] = meta_fields

        response = requests.post(
            WP_URL,
            json=data,
            auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD),
        )

        if response.status_code in [200, 201]:
            post_id = response.json().get("id")
            print(f"✅ WordPress post published: {title} (ID: {post_id})")
            return post_id
        else:
            print(f"⚠️ WordPress post failed: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error posting to WordPress: {e}")
        return None