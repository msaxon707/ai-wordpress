import random
from logger_setup import setup_logger

logger = setup_logger()

def inject_affiliate_links(content: str, products: list):
    """Insert affiliate links naturally throughout the article."""
    if not products:
        logger.warning("⚠️ No products provided to inject.")
        return content

    for product in random.sample(products, min(3, len(products))):
        link_html = f'<a href="{product["url"]}" target="_blank" rel="nofollow noopener">{product["name"]}</a>'
        sentences = content.split(". ")
        insert_point = random.randint(1, len(sentences) - 1)
        sentences.insert(insert_point, f"Check out {link_html} for more info.")
        content = ". ".join(sentences)
    logger.info(f"🔗 Inserted {min(3, len(products))} affiliate links.")
    return content
