import random
import re


def inject_affiliate_links(content, products):
    """
    Insert affiliate products naturally into the article text.
    Instead of standalone links, weave them into sentences.
    """
    if not products:
        print("[WARN] No affiliate products available to inject.")
        return content

    # Clean out any leftover placeholders (safety net)
    content = re.sub(r'\[(HEAD|META|TITLE|BODY)\]', '', content, flags=re.IGNORECASE)

    paragraphs = [p.strip() for p in content.split("</p>") if p.strip()]
    injected = []
    used = set()

    for p in paragraphs:
        if not p:
            continue

        # Randomly decide whether to inject a link into this paragraph
        if random.random() < 0.35 and len(products) > 0:
            product = random.choice(products)
            name = product.get("name", "this product")
            url = product.get("url", "#")

            # Skip duplicates
            if name in used:
                injected.append(f"<p>{p}</p>")
                continue

            used.add(name)

            # Create a natural inline mention
            mention = (
                f'<a href="{url}" target="_blank" rel="nofollow noopener">{name}</a>'
            )

            # Try to place link naturally in sentence
            sentences = re.split(r'(?<=[.!?]) +', p)
            if len(sentences) > 1:
                insert_idx = random.randint(0, len(sentences) - 1)
                sentences[insert_idx] += f" I personally recommend checking out {mention}."
                new_p = " ".join(sentences)
            else:
                new_p = f"{p} You might also like {mention}."

            injected.append(f"<p>{new_p}</p>")
        else:
            injected.append(f"<p>{p}</p>")

    final_content = "".join(injected)

    # Final cleanup for any duplicate paragraph tags
    final_content = re.sub(r"<p>\s*</p>", "", final_content)
    return final_content


def load_affiliate_products():
    """
    (Optional fallback) Load product list from affiliate_products.json
    if dynamic generation fails.
    """
    import json
    import os

    file_path = os.path.join(os.path.dirname(__file__), "affiliate_products.json")

    if not os.path.exists(file_path):
        print("[WARN] affiliate_products.json not found. Returning empty list.")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"[affiliate_injector] Loaded {len(data)} static products.")
            return data
    except Exception as e:
        print(f"[ERROR] Could not load affiliate products: {e}")
        return []


def build_affiliate_link(base_keyword):
    """
    Build an Amazon search link using the affiliate tag from environment variable.
    """
    import os
    tag = os.getenv("AMAZON_ASSOC_TAG", "thesaxonblog01-20")
    keyword = base_keyword.replace(" ", "+")
    return f"https://www.amazon.com/s?k={keyword}&tag={tag}"
