import base64
import requests
from io import BytesIO
from openai import OpenAI
from config import OPENAI_API_KEY, WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD, OPENAI_MODEL
from logger_setup import setup_logger

logger = setup_logger()
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_image(prompt):
    """Generate blog image using DALL·E 3."""
    logger.info(f"🎨 Generating featured image for: {prompt}")
    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )
        image_base64 = response.data[0].b64_json
        return base64.b64decode(image_base64)
    except Exception as e:
        logger.error(f"[DALL·E] Image generation failed: {e}")
        return None

def upload_to_wordpress(image_data, filename):
    """Upload generated image to WordPress."""
    try:
        url = f"{WP_BASE_URL}/wp-json/wp/v2/media"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        auth = (WP_USERNAME, WP_APP_PASSWORD)
        res = requests.post(url, headers=headers, data=image_data, auth=auth)
        res.raise_for_status()
        media_id = res.json().get("id")
        logger.info(f"🖼️ Uploaded featured image: {filename} (ID: {media_id})")
        return media_id
    except Exception as e:
        logger.error(f"[Upload] Failed: {e}")
        return None

def get_featured_image_id(topic):
    image_data = generate_image(topic)
    if not image_data:
        return None
    filename = f"{topic.replace(' ', '_')}.png"
    return upload_to_wordpress(image_data, filename)
