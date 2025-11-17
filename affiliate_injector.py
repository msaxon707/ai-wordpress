import json
import random
import re
import requests
from config import AMAZON_TAG, AFFILIATE_LINK_FREQUENCY

# --- Load product data ---
def load_affiliate_products(file_path="affiliate_products.json"):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = list(data.values())
        return data
    except Exception as e:
        print(f"[WARN] Could not load affiliate_products.json: {e}")
        return []

# --- Verify Amazon links ---
def verify_amazon_link(url):
    try:
        r = requests.head(url, allow_redirects=True, timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False

# --- Ensure one tag param only ---
def build_affiliate_link(url):
    if "amazon.com" not in url:
        return url
    import urllib.parse as up
    parsed = up.urlparse(url)
    q = dict(up.parse_qsl(parsed.query))
    q["tag"] = AMAZON_TAG
    return up.urlunparse(parsed._replace(query=up.urlencode(q)))

# --- Contextual match ---
def match_products_to_text(paragraph, products):
    paragraph_lower = paragraph.lower()
    matching = [
        p for p in products
        if any(tag.lower() in paragraph_lower for tag in p.get("tags", []))
    ]
    if not matching:
        matching = [p for p in products if "outdoor" in p.get("tags", [])]
    return matching

# --- Random anchor text options ---
def choose_anchor_text():
    options = [
        "Check it on Amazon",
        "See the latest price",
        "Grab it here",
        "View details on Amazon",
        "Get yours today",
        "See this gear on Amazon"
    ]
    return random.choice(options)

# --- Inject contextual affiliate links ---
def inject_affiliate_links(content, products):
    if not products:
        return content

    # Split paragraphs on newlines or <p> breaks
    paragraphs = re.split(r'(?:\n{1,}|</p>)', content)
    injected = []
    counter = 0

    for paragraph in paragraphs:
        injected.append(paragraph)
        if not paragraph.strip():
            continue

        counter += 1
        if counter % AFFILIATE_LINK_FREQUENCY == 0:
            relevant_products = match_products_to_text(paragraph, products)

            # ✅ Prevent empty sequence crash
            if not relevant_products:
            relevant_products = products  # fallback to full product list

            product = random.choice(relevant_products)

            product_name = product.get("name", "View Product")
            product_url = build_affiliate_link(product.get("url", "#"))
            if not relevant_products:
            print("[INFO] No relevant product match — using fallback list.")
            relevant_products = products


            if verify_amazon_link(product_url):
                anchor_text = choose_anchor_text()
                injected.append(
                    f'\n\n<a href="{product_url}" target="_blank" rel="nofollow noopener">'
                    f'{anchor_text}: {product_name}</a>\n\n'
                )
            else:
                print(f"[SKIP] Dead link skipped: {product_url}")

    return "".join(injected)
