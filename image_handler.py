# image_handler.py
import openai
import requests
import base64
import time
from requests.auth import HTTPBasicAuth
from logger_setup import setup_logger
import os

logger = setup_logger()
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_featured_image(topic: str, wp_credentials: HTTPBasicAuth, wp_base_url: str):
    """Generate a featured image for the post using OpenAI Image API (v1.3.7 compatible)."""
    prompt = (
        f"A high-quality rustic digital photograph that represents the theme: '{topic}'. "
        "Style: cozy country living, warm tones, farmhouse, natural lighting."
    )

    for attempt in range(3):
        try:
            logger.info(f"🎨 Generating featured image for topic: {topic}")
            result = openai.Image.create(
                prompt=prompt,
                n=1,
                size="1024x1024",
                response_format="b64_json"
            )
            image_data = base64.b64decode(result["data"][0]["b64_json"])
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
                logger.info(f"🖼️ Image uploaded successfully: {filename} (ID {image_id})")
                return image_id
            else:
                logger.error(f"❌ Failed to upload image: {response.text}")
                time.sleep(5)
        except Exception as e:
            logger.error(f"Error generating/uploading image: {e}")
            time.sleep(5)
    return None
