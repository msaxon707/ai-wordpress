import os
import base64
import logging
import requests

logger = logging.getLogger(__name__)

class WordPressClient:
    """
    A client for interacting with the WordPress REST API, including creating posts and uploading media.
    Uses Basic Auth (username and application password) for authentication.
    """
    def __init__(self, base_url=None, username=None, password=None):
        # Load connection details from environment if not provided explicitly 
        self.base_url = (base_url or os.getenv('WP_BASE_URL', '')).rstrip('/')
        self.username = username or os.getenv('WP_USERNAME')
        self.password = password or os.getenv('WP_APP_PASSWORD')
       if not (self.base_url and self.username and self.password):
            logger.error("WordPressClient initialization failed due to missing credentials or base_url.")
            raise ValueError("WordPress base URL, username, or password not provided.")
        # Prepare base API endpoint
        if not self.base_url.endswith('/wp-json/wp/v2'):
            # If base_url is the site root, append the REST API path
            self.api_base = self.base_url + '/wp-json/wp/v2'
        else:
            self.api_base = self.base_url
        # Initialize a session for persistent connection
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        # Set a reasonable timeout for all requests
        self.timeout = 15
        logger.debug(f"Initialized WordPressClient for {self.base_url}")

    def create_post(self, title, content, category_ids=None, featured_media_id=None, status='publish'):
        """
        Create a WordPress post with the given title, HTML content, category IDs, and optional featured media.
        Returns the JSON response from WordPress if successful.
        """
        url = f"{self.api_base}/posts"
        post_data = {
            "title": title,
            "content": content,
            "status": status
        }
        if category_ids:
            if isinstance(category_ids, list):
                post_data["categories"] = category_ids
            else:
                post_data["categories"] = [category_ids]
        if featured_media_id:
            post_data["featured_media"] = featured_media_id
        logger.info(f"Creating WordPress post '{title}'")
        try:
            response = self.session.post(url, json=post_data, timeout=self.timeout)
        except requests.RequestException as e:
            logger.error(f"Failed to create post: {e}")
            return None
        if response.status_code not in (200, 201):
            logger.error(f"Failed to create post. Status: {response.status_code}, Response: {response.text}")
            return None
        logger.info(f"Post created successfully: '{title}' (ID: {response.json().get('id')})")
        return response.json()

    def upload_media(self, image_content, filename, alt_text=None):
        """
        Upload an image to WordPress media library.
        image_content: Binary content of the image.
        filename: Filename to use for the image on WordPress.
        alt_text: Optional alt text for the image.
        Returns the media ID if upload successful, otherwise None.
        """
        url = f"{self.api_base}/media"
        headers = {
            'Content-Type': 'image/jpeg',  # assuming JPEG; adjust if needed
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        logger.info(f"Uploading image '{filename}' to WordPress media library")
        try:
            response = self.session.post(url, headers=headers, data=image_content, timeout=self.timeout)
        except requests.RequestException as e:
            logger.error(f"Failed to upload media: {e}")
            return None
        if response.status_code not in (200, 201):
            logger.error(f"Media upload failed. Status: {response.status_code}, Response: {response.text}")
            return None
        media_id = response.json().get('id')
        logger.info(f"Image uploaded successfully. Media ID: {media_id}")
        # If alt_text provided, update the media with alt text (title and alt)
        if media_id and alt_text:
            media_url = f"{self.api_base}/media/{media_id}"
            meta = {"alt_text": alt_text, "title": alt_text}
            try:
                self.session.post(media_url, json=meta, timeout=self.timeout)
            except requests.RequestException as e:
                logger.warning(f"Failed to set alt text for media {media_id}: {e}")
        return media_id

    def get_or_create_category(self, category_name):
        """
        Get the WordPress category ID for the given category name. If it doesn't exist, attempt to create it.
        Returns the category ID, or None if not found/created.
        """
        if not category_name:
            return None
        slug = category_name.strip().lower().replace(' ', '-')
        get_url = f"{self.api_base}/categories?slug={slug}"
        try:
            resp = self.session.get(get_url, timeout=self.timeout)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch category '{category_name}': {e}")
            return None
        if resp.status_code == 200:
            categories = resp.json()
            if categories:
                cat_id = categories[0]['id']
                logger.debug(f"Found existing category '{category_name}' with ID {cat_id}")
                return cat_id
        # If not found, create the category
        post_url = f"{self.api_base}/categories"
        cat_data = {"name": category_name, "slug": slug}
        try:
            resp = self.session.post(post_url, json=cat_data, timeout=self.timeout)
        except requests.RequestException as e:
            logger.error(f"Failed to create category '{category_name}': {e}")
            return None
        if resp.status_code in (200, 201):
            cat_id = resp.json().get('id')
            logger.info(f"Created new WordPress category '{category_name}' (ID: {cat_id})")
            return cat_id
        else:
            logger.error(f"Could not create category '{category_name}'. Status: {resp.status_code}, Response: {resp.text}")
            return None
# helper to keep backward compatibility with older scripts
def post_to_wordpress(title, content, category_id=None, featured_image_id=None):
    """
    Convenience wrapper for WordPressClient.create_post().
    Pulls credentials and base URL from environment variables.
    """
    client = WordPressClient()
    return client.create_post(
        title=title,
        content=content,
        category_ids=category_id,
        featured_media_id=featured_image_id,
        status="publish",
    )
            
