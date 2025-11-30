from openai import OpenAI
import requests
import base64
import time
import os
from requests.auth import HTTPBasicAuth
from logger_setup import setup_logger

logger = setup_logger()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_featured_image(topic: str, wp_credentials: HTTPBasicAuth, wp_base_url: str):
    prompt = (
        f"A high-quality rustic photograph representing '{topic}', "
        "style: warm farmhouse tones, natural lighting."
    )

    for attempt in range(3):
        try:
            result = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size="1024x1024"
            )

            image_base64 = result.data[0].b64_json
            image_data = base64.b64decode(image_base64)
            filename = f"{topic.replace(' ', '_')}.png"
            media_endpoint = f"{wp_base_url}/wp-json/wp/v2/media"

            response = requests.post(
                media_endpoint,
                headers={"Content-Disposition": f"attachment; filename={filename}"},
                auth=wp_credentials,
                files={"file": (filename, image_data, "image/png")},
                timeout=60
            )

            if response.status_code == 201:
                image_id = response.json()["id"]
                logger.info(f"🖼️ Uploaded featured image: {filename} (ID: {image_id})")
                return image_id
            else:
                logger.error(f"❌ Image upload failed: {response.text}")
                time.sleep(5)
        except Exception as e:
            logger.error(f"Error in image generation/upload: {e}")
            time.sleep(5)
    return None
