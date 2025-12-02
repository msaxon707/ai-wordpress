"""
image_handler.py — Generates and uploads post images using DALL·E.
"""

import io
import base64
import requests
from openai import OpenAI
from config import OPENAI_MODEL, WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD

client = OpenAI()


def generate_image(topic):
    prompt = f"A realistic rustic country-style photo related to: {topic}."
    result = client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1024")
    image_base64 = result.data[0].b64_json
    return base64.b64decode(image_base64)


def upload_image_to_wordpress(image_bytes, filename):
    url = f"{WP_BASE_URL}/wp-json/wp/v2/media"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    response = requests.post(
        url,
        headers=headers,
        data=image_bytes,
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        timeout=60,
    )
    response.raise_for_status()
    return response.json().get("id")


def get_featured_image_id(topic):
    image_bytes = generate_image(topic)
    filename = f"{topic.replace(' ', '_')}.png"
    image_id = upload_image_to_wordpress(image_bytes, filename)
    print(f"[image_handler] 🖼️ Uploaded image {filename} (ID {image_id})")
    return image_id
