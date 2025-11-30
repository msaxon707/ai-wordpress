import os
import httpx
import base64
import time
from logger_setup import setup_logger
from wordpress_client import upload_image_to_wordpress

# === CONFIG ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_IMAGE_MODEL = "gpt-image-1"  # OpenAI’s photorealistic model
API_URL = "https://api.openai.com/v1/images/generations"

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

logger = setup_logger()


def generate_image(topic, retries=3, delay=10):
    """
    Generate a realistic AI image based on the article topic.
    Retries on failure up to 3 times.
    """
    prompt = (
        f"Create a realistic, high-quality photo that visually represents the topic: "
        f"'{topic}'. The photo should fit a blog post about home decor, "
        f"country living, or outdoor lifestyle — bright, warm, and inviting. "
        f"Style: natural lighting, realistic textures, no text overlay."
    )

    payload = {
        "model": OPENAI_IMAGE_MODEL,
        "prompt": prompt,
        "size": "1024x1024"
    }

    for attempt in range(1, retries + 1):
        try:
            response = httpx.post(API_URL, headers=HEADERS, json=payload, timeout=90)
            response.raise_for_status()

            data = response.json()
            if "data" in data and data["data"]:
                image_base64 = data["data"][0].get("b64_json")
                if not image_base64:
                    logger.warning("⚠️ No image data returned.")
                    continue

                image_bytes = base64.b64decode(image_base64)
                image_filename = f"{topic.replace(' ', '_')}.png"

                # Save temporarily
                with open(image_filename, "wb") as f:
                    f.write(image_bytes)

                logger.info(f"🖼️ Image generated successfully for topic: {topic}")
                return image_filename

        except Exception as e:
            logger.warning(f"⚠️ Image generation attempt {attempt}/{retries} failed: {e}")
            time.sleep(delay)

    logger.error(f"❌ Failed to generate image for topic: {topic}")
    return None


def get_featured_image_id(topic):
    """
    Generate and upload the featured image for a WordPress post.
    Returns the uploaded image ID, or None on failure.
    """
    logger.info(f"🎨 Generating featured image for: {topic}")
    image_path = generate_image(topic)

    if not image_path:
        logger.warning("⚠️ No image generated; skipping upload.")
        return None

    # Upload image to WordPress
    try:
        image_id = upload_image_to_wordpress(image_path)
        if image_id:
            logger.info(f"🖼️ Uploaded featured image: {image_path} (ID: {image_id})")
            os.remove(image_path)  # cleanup
            return image_id
        else:
            logger.warning("⚠️ Image upload returned no ID.")
            return None
    except Exception as e:
        logger.error(f"❌ Failed to upload image to WordPress: {e}")
        return None


if __name__ == "__main__":
    test_topic = "Rustic farmhouse living room decor with natural light"
    img_id = get_featured_image_id(test_topic)
    print(f"Test upload complete. Image ID: {img_id}")
