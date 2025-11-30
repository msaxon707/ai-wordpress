"""
image_handler.py — Generates AI images with DALL·E and uploads to WordPress.
"""

import io
import base64
import requests
from openai import OpenAI
from config import OPENAI_API_KEY, WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD, IMAGE_STYLE

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_featured_image(topic):
    prompt = f"{topic}, {IMAGE_STYLE}"
    result = client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1024")
    image_data = base64.b64decode(result.data[0].b64_json)
    return io.BytesIO(image_data)


def upload_image_to_wordpress(image_stream, filename):
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    r = requests.post(
        f"{WP_BASE_URL}/wp-json/wp/v2/media",
        headers=headers,
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        files={"file": (filename, image_stream, "image/png")}
    )
    if r.status_code == 201:
        image_id = r.json()["id"]
        print(f"[image_handler] 🖼️ Uploaded featured image: {filename} (ID: {image_id})")
        return image_id
    print(f"[image_handler] ⚠️ Failed to upload image: {r.status_code}")
    return None


def get_featured_image_id(topic):
    image_stream = generate_featured_image(topic)
    filename = topic.replace(" ", "_") + ".png"
    return upload_image_to_wordpress(image_stream, filename)
