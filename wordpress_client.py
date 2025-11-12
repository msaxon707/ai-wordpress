import requests
import base64
import os

SITE_BASE = os.getenv("SITE_BASE", "")

def create_wordpress_post(
    wp_url,
    username,
    password,
    title,
    content,
    image_url=None,
    image_alt=None,
    affiliate_tag=None,
    focus_keyword=None
):
    """
    Creates a post on WordPress with optional featured image, affiliate tag, and SEO focus keyword.
    """

    # ✅ Add affiliate section if tag is provided
    if affiliate_tag:
        affiliate_section = f"""
        <p><strong>Looking for gear?</strong> 
        <a href="{SITE_BASE}?tag={affiliate_tag}" target="_blank" rel="noopener">
        Shop our recommended products here.</a></p>
        """
        content += affiliate_section

    # ✅ Add SEO focus keyword if provided
    if focus_keyword:
        seo_meta = f"""
        <!-- SEO Focus Keyword: {focus_keyword} -->
        <meta name="keywords" content="{focus_keyword}">
        """
        content += seo_meta

    # ✅ Upload the image to WordPress media if available
    featured_media_id = None
    if image_url:
        try:
            print("📸 Uploading featured image...")
            img_data = requests.get(image_url).content
            media_endpoint = wp_url.replace("/posts", "/media")

            headers = {
                "Content-Disposition": f"attachment; filename={os.path.basename(image_url)}",
                "Authorization": "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode(),
                "Content-Type": "image/jpeg"
            }

            media_response = requests.post(media_endpoint, headers=headers, data=img_data)
            if media_response.status_code == 201:
                featured_media_id = media_response.json().get("id")
                print(f"✅ Featured image uploaded with ID: {featured_media_id}")
            else:
                print(f"⚠️ Failed to upload image: {media_response.status_code} - {media_response.text}")
        except Exception as e:
            print(f"❌ Error uploading image: {e}")

    # ✅ Prepare post data
    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
    }
    if featured_media_id:
        post_data["featured_media"] = featured_media_id

    # ✅ Send post to WordPress
    try:
        headers = {
            "Authorization": "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode(),
            "Content-Type": "application/json"
        }
        print("📰 Publishing post to WordPress...")
        response = requests.post(wp_url, headers=headers, json=post_data)

        if response.status_code in [200, 201]:
            post_id = response.json().get("id")
            print(f"🎉 Successfully published post: {title} (ID: {post_id})")
            return post_id
        else:
            print(f"❌ Failed to publish post: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error posting to WordPress: {e}")
        return None