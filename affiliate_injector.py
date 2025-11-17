import json
import random
import re
from config import AMAZON_TAG, AFFILIATE_LINK_FREQUENCY

def load_affiliate_products(file_path="affiliate_products.json"):
    """Load affiliate products from JSON."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[WARN] affiliate_products.json not found.")
        return []
    except json.JSONDecodeError:
        print("[ERROR] affiliate_products.json is malformed.")
        return []

def build_affiliate_link(url):
    """Append Amazon affiliate tag if not already present."""
    if "amazon.com" in url:
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}tag={AMAZON_TAG}"
    return url

def choose_anchor_text():
    """Randomized call-to-action text for link variation."""
    options = [
        "Check it on Amazon",
        "See the latest price",
        "View details here",
        "Grab it on Amazon",
        "See it in action",
        "Shop now",
    ]
    return random.choice(options)

def inject_affiliate_links(content, products):
    """
    Inserts affiliate links inline every few paragraphs.
    """
    if not products:
        return content

    paragraphs = re.split(r'(?:\n{1,}|</p>)', content)  # split but keep paragraph breaks
    injected = []
    paragraph_counter = 0

    for segment in paragraphs:
        injected.append(segment)
        if segment.strip() == "":
            continue

        paragraph_counter += 1
        if paragraph_counter % AFFILIATE_LINK_FREQUENCY == 0:
            product = random.choice(products)
            product_name = product.get("name", "View Product")
            product_url = build_affiliate_link(product.get("url", "#"))
            anchor_text = choose_anchor_text()

            # inline HTML link injection
            affiliate_html = (
                f'\n\n<a href="{product_url}" target="_blank" rel="nofollow noopener">'
                f'{anchor_text}: {product_name}</a>\n\n'
            )
            injected.append(affiliate_html)

    return "".join(injected)
