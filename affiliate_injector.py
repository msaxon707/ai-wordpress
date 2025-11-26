# affiliate_injector.py
import random
from logger_setup import setup_logger

logger = setup_logger()

def load_affiliate_products():
    """Load static affiliate products to insert into posts."""
    return [
        {
            "name": "Rustic Wooden Coffee Table",
            "description": "A farmhouse-style centerpiece for your living room.",
            "url": "https://amzn.to/example1"
        },
        {
            "name": "LED Hunting Flashlight",
            "description": "Durable, waterproof flashlight ideal for night hunting or camping.",
            "url": "https://amzn.to/example2"
        },
        {
            "name": "Farmhouse Wall Decor",
            "description": "Rustic metal and wood wall art for your home.",
            "url": "https://amzn.to/example3"
        }
    ]

def inject_affiliate_links(content, products):
    """Randomly insert affiliate links naturally throughout article HTML."""
    if not products:
        return content

    paragraphs = content.split("</p>")
    insert_count = random.randint(1, 3)

    for _ in range(insert_count):
        if len(paragraphs) > 2:
            index = random.randint(1, len(paragraphs) - 1)
            product = random.choice(products)
            link_html = (
                f'<p><strong>Check this out:</strong> '
                f'<a href="{product["url"]}" target="_blank" rel="nofollow sponsored">'
                f'{product["name"]}</a> - {product["description"]}</p>'
            )
            paragraphs.insert(index, link_html)
    logger.info(f"🔗 Inserted {insert_count} affiliate links.")
    return "</p>".join(paragraphs)