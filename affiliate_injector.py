import random
import re
from logger_setup import setup_logger

logger = setup_logger()

def inject_affiliate_links(content: str, products: list):
    """Insert affiliate links naturally throughout the article at paragraph breaks."""
    if not products:
        logger.warning("⚠️ No products provided to inject.")
        return content

    # Split by paragraph for safer HTML injection
    paragraphs = re.split(r'(</p>|<br\s*/?>)', content)
    num_inserts = min(3, len(products))
    insert_points = random.sample(range(1, len(paragraphs)), num_inserts)

    for i, idx in enumerate(sorted(insert_points)):
        if i < len(products):
            product = products[i]
            link_html = (
                f'<p>Check out '
                f'<a href="{product["url"]}" target="_blank" rel="nofollow noopener">'
                f'{product["name"]}</a> for more info.</p>'
            )
            paragraphs.insert(idx, link_html)

    combined = "".join(paragraphs)

    logger.info(f"🔗 Inserted {num_inserts} affiliate links across the article.")
    return combined
