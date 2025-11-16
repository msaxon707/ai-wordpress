#!/usr/bin/env python3
import os
import sys
import logging
import random
import json
import openai

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from wordpress_client import WordPressClient
from image_handler import search_image
from content_normalizer import format_content

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

def load_affiliate_products(json_path="affiliate_products.json"):
    """Load affiliate products from a JSON file. Returns a dict mapping categories to product list."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            logger.debug(f"Loaded affiliate products from {json_path}")
            return data
    except FileNotFoundError:
        logger.error(f"Affiliate products file not found: {json_path}")
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing affiliate products JSON: {e}")
    return {}

def choose_topic(categories):
    """Choose a topic (category) to generate content for. Currently selects a random category from the list."""
    if not categories:
        return None
    return random.choice(categories)

def generate_content(topic):
    """
    Use the OpenAI API to generate a blog post about the given topic.
    Returns (title, content_markdown) if successful, otherwise (None, None).
    """
    if not topic:
        logger.error("No topic provided for content generation.")
        return None, None
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        logger.error("OpenAI API key is not set in environment.")
        return None, None
    openai.api_key = openai_api_key
    prompt = (f"Write a detailed blog post about {topic} for a lifestyle and outdoors blog. "
              f"Include an introduction and several informative sections with tips or advice about {topic}. "
              f"Provide a catchy title for the post as an H1 heading at the top, followed by the content in Markdown format.")
    try:
        logger.info(f"Generating blog content for topic: {topic}")
        response = openai.ChatCompletion.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4'),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500
        )
    except Exception as e:
        logger.error(f"OpenAI API request failed: {e}")
        return None, None
    # Extract the content
    content = response['choices'][0]['message']['content']
    if not content:
        logger.error("OpenAI returned empty content.")
        return None, None
    # Split title and content if title is included as first line (e.g., Markdown H1)
    title = None
    content_markdown = content
    lines = content.splitlines()
    if lines:
        first_line = lines[0].strip()
        if first_line.startswith("#"):
            # Use as title (remove leading '# ' characters)
            title = first_line.lstrip('# ').strip()
            content_markdown = "\n".join(lines[1:]).strip()
    if title is None:
        # If no title found in content, create a simple title
        title = topic.title()
    logger.info(f"Generated title: {title}")
    return title, content_markdown

def main():
    # Load affiliate products data
    affiliate_data = load_affiliate_products()
    # Determine topic/categories available
    categories = list(affiliate_data.keys())
    topic = choose_topic(categories)
    if not topic:
        logger.error("No topic could be chosen. Ensure affiliate_products.json has at least one category.")
        return
    # Generate content using OpenAI
    title, content_markdown = generate_content(topic)
    if not content_markdown:
        logger.error("Content generation failed, aborting.")
        return
    # Format content to HTML and inject affiliate links for the topic
    products_for_topic = affiliate_data.get(topic, [])
    if products_for_topic:
        # Select 5 to 10 related products (or fewer if not enough available)
        if len(products_for_topic) < 5:
            selected_products = products_for_topic
        else:
            count = random.randint(5, min(10, len(products_for_topic)))
            selected_products = random.sample(products_for_topic, count) if len(products_for_topic) >= count else products_for_topic
    else:
        selected_products = []
    content_html = format_content(content_markdown, affiliate_products=selected_products)
    # Fetch a relevant image for the topic
    image_content, image_filename, image_alt = search_image(topic)
    # Initialize WordPress client
    try:
        wp_client = WordPressClient()
    except Exception as e:
        logger.error(f"WordPress client initialization failed: {e}")
        return
    # If an image was fetched, upload it to WordPress and get media ID
    featured_media_id = None
    if image_content:
        featured_media_id = wp_client.upload_media(image_content, image_filename, alt_text=image_alt)
        if not featured_media_id:
            logger.warning("Proceeding without featured image due to upload failure.")
    else:
        logger.info("No image fetched, proceeding without featured image.")
    # Ensure we have the category ID for the topic
    category_id = wp_client.get_or_create_category(topic)
    category_ids = [category_id] if category_id else None
    # Post to WordPress
    post_response = wp_client.create_post(title, content_html, category_ids=category_ids, featured_media_id=featured_media_id, status=os.getenv('WP_POST_STATUS', 'publish'))
    if post_response:
        post_id = post_response.get('id')
        post_link = post_response.get('link')
        logger.info(f"Successfully posted to WordPress (ID: {post_id}). URL: {post_link}")
    else:
        logger.error("Failed to post to WordPress.")

if __name__ == "__main__":
    main()
