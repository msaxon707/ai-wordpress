import os
import re
import base64
import requests
from openai import OpenAI
from config import OPENAI_API_KEY
from logger_setup import setup_logger
from wordpress_client import upload_image_to_wordpress

logger = setup_logger()
client = OpenAI(api_key=OPENAI_API_KEY)

def sanitize_filename(name: str) -> str:
    """Sanitize filename for safe upload."""
    name = re.sub(r'[^\w\s-]', '', name).strip()
    return re.sub(r'[-\s]+', '_', name).lower()

def get_featured_image_id(topic: str):
    """Generate and upload a featured image for the given topic."""
    try:
        prompt = f"Generate a realistic image that represents the topic: {topic}"
        logger.info(f"🎨 Generating featured image for: {topic}")
        result = client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1024")

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        safe_name = sanitize_filename(topic)[:80]
        filename = f"{safe_name}.png"

        with open(filename, "wb") as f:
            f.write(image_bytes)

        image_id = upload_image_to_wordpress(filename)
        os.remove(filename)

        if image_id:
            logger.info(f"🖼️ Uploaded featured image for '{topic}' (ID: {image_id})")
            return image_id
        else:
            raise Exception("Upload returned no ID")

    except Exception as e:
        logger.error(f"⚠️ Image upload failed: {e}")
        return None
