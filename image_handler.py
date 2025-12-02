import base64
import requests
import re
from io import BytesIO
from openai import OpenAI
from config import OPENAI_API_KEY, WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD
from logger_setup import setup_logger

logger = setup_logger()
client = OpenAI(api_key=OPENAI_API_KEY)


def clean_filename(text: str) -> str:
    """Cleans up a topic name for safe use in filenames and headers."""
    clean = re.sub(r'[\*\n\r\"“”‘’]+', '', text).strip()
    clean = re.sub(r'[^a-zA-Z0-9 _-]', '', clean)
    clean = "_".join(clean.split())[:80]
    return clean or "image"


def generate_image(prompt):
    """Generate a DALL·E 3 image safely."""
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
    """Upload binary image data to WordPress."""
    try:
        url = f"{WP_BASE_URL}/wp-json/wp/v2/media"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "image/png"
        }
        auth = (WP_USERNAME, WP_APP_PASSWORD)
        res = requests.post(url, headers=headers, data=image_data, auth=auth, timeout=60)
        res.raise_for_status()
        media_id = res.json().get("id")
        logger.info(f"🖼️ Uploaded featured image: {filename} (ID: {media_id})")
        return media_id
    except Exception as e:
        logger.error(f"[Upload] Failed: {e}")
        return None


def fetch_fallback_image(topic):
    """Get a royalty-free fallback image from Unsplash."""
    try:
        logger.info(f"🌄 Fetching fallback image for: {topic}")
        clean_topic = "+".join(topic.split())
        unsplash_url = f"https://source.unsplash.com/1024x1024/?{clean_topic},rustic,country"
        res = requests.get(unsplash_url, timeout=30)
        if res.status_code == 200:
            return res.content
    except Exception as e:
        logger.error(f"[Unsplash Fallback] Failed: {e}")
    return None


def get_featured_image_id(topic):
    """Generate (or fetch) and upload a featured image for a given topic."""
    clean_topic = clean_filename(topic)
    image_data = generate_image(clean_topic)

    if not image_data:
        logger.warning("⚠️ DALL·E failed — using Unsplash fallback.")
        image_data = fetch_fallback_image(clean_topic)

    if not image_data:
        logger.error("❌ No image could be generated or fetched.")
        return None

    filename = f"{clean_topic}.png"
    media_id = upload_to_wordpress(image_data, filename)

    if not media_id:
        logger.warning("⚠️ Upload to WordPress failed — retrying with fallback image.")
        fallback = fetch_fallback_image(clean_topic)
        if fallback:
            media_id = upload_to_wordpress(fallback, f"fallback_{filename}")

    return media_id
