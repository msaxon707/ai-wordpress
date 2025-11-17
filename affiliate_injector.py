import json
import random
import re
from urllib.parse import urlparse, urlencode, urlunparse

AFFILIATE_TAG = "thesaxonblog01-20"
AFFILIATE_LINK_FREQUENCY = 3  # insert a link every 3 paragraphs


def load_affiliate_products(json_path="affiliate_products.json"):
    """Load affiliate products from JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_amazon_link(url):
    """Check if a given URL is a valid Amazon product link."""
    parsed = urlparse(url)
    return "amazon." in parsed.netloc and "/dp/" in parsed.path


def build_affiliate_link(product_url):
    """Append or replace Amazon tag in the URL."""
    if not verify_amazon_link(product_url):
        return product_url

    parsed = urlparse(product_url)
    query = dict([(k.lower(), v) for k, v in [q.split("=") for q in parsed.query.split("&") if "=" in q]]) if parsed.query else {}
    query["tag"] = AFFILIATE_TAG
    new_query = urlencode(query)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

import openai
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def match_products_to_text(text, products):
    """Use semantic similarity to find products that best match the paragraph context."""
    text_lower = text.lower()

    # Quick keyword-based filter first
    matched = [
        p for p in products
        if any(tag.lower() in text_lower for tag in p.get("tags", []))
    ]

    # If no keyword match, use semantic fallback
    if not matched:
        try:
            response = openai.Embedding.create(
                model="text-embedding-3-small",
                input=text_lower,
            )
            text_vector = response['data'][0]['embedding']

            # Simple semantic scoring by overlapping tags and description
            def relevance_score(prod):
                desc = " ".join(prod.get("tags", [])) + " " + prod.get("name", "")
                resp = openai.Embedding.create(model="text-embedding-3-small", input=desc)
                prod_vector = resp['data'][0]['embedding']
                # cosine similarity simplified
                dot = sum(a*b for a, b in zip(text_vector, prod_vector))
                return dot

            ranked = sorted(products, key=relevance_score, reverse=True)
            return ranked[:5]  # top 5 most relevant products
        except Exception as e:
            print(f"[WARN] Semantic match fallback failed: {e}")
            return []

    return matched



def choose_anchor_text():
    """Select a random phrase for affiliate anchor text."""
    options = [
        "Check it out here",
        "See it in action",
        "Find it on Amazon",
        "View this recommended gear",
        "Grab yours now",
    ]
    return random.choice(options)


def inject_affiliate_links(content, products):
    """Insert affiliate links into article content."""
    paragraphs = re.split(r"(?:\n{1,}|\</p\>)", content)
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
                print("[INFO] No relevant product match — using fallback list.")
                relevant_products = products  # fallback to full product list

            product = random.choice(relevant_products)
            product_name = product.get("name", "View Product")
            product_url = build_affiliate_link(product.get("url", "#"))

            if verify_amazon_link(product_url):
                anchor_text = choose_anchor_text()
                injected.append(
                    f'\n\n<a href="{product_url}" target="_blank" rel="nofollow noopener">'
                    f'{anchor_text}: {product_name}</a>\n\n'
                )
            else:
                print(f"[WARN] Skipping non-Amazon product: {product_name}")

    return "\n".join(injected)
