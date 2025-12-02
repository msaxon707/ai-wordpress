import random
from logger_setup import setup_logger

logger = setup_logger()

def inject_affiliate_links(content: str, products: list):
    """Insert affiliate links naturally throughout the article and add a Recommended Gear section."""
    if not products:
        logger.warning("⚠️ No products provided to inject.")
        return content

    # Inline placement (2–3 spots)
    for product in random.sample(products, min(3, len(products))):
        link_html = f'<a href="{product["url"]}" target="_blank" rel="nofollow noopener">{product["name"]}</a>'
        sentences = content.split(". ")
        insert_point = random.randint(1, len(sentences) - 1)
        sentences.insert(insert_point, f"Check out {link_html} for more info.")
        content = ". ".join(sentences)

    # Recommended Gear section
    gear_items = "\n".join(
        [f'<li><a href="{p["url"]}" target="_blank" rel="nofollow noopener">{p["name"]}</a></li>'
         for p in products]
    )

    gear_block = f"""
    <h3>Recommended Gear</h3>
    <ul>
    {gear_items}
    </ul>
    """

    logger.info(f"🔗 Inserted {min(3, len(products))} inline links and added Recommended Gear section.")
    return content + "\n\n" + gear_block
