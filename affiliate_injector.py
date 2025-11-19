import random

AFFILIATE_LINK_FREQUENCY = 3

def inject_affiliate_links(content, products):
    """Insert contextual Amazon affiliate links into the article content."""
    if not products:
        print("[WARN] No affiliate products available to inject.")
        return content

    paragraphs = content.split("</p>")
    injected = []
    counter = 0

    for paragraph in paragraphs:
        if not paragraph.strip():
            continue

        injected.append(paragraph + "</p>")
        counter += 1

        if counter % AFFILIATE_LINK_FREQUENCY == 0:
            product = random.choice(products)
            product_name = product.get("name", "View on Amazon")
            product_url = product.get("url", "#")

            link_html = (
                f'<p><a href="{product_url}" target="_blank" rel="nofollow noopener">'
                f'🔗 View {product_name} on Amazon</a></p>'
            )

            injected.append(link_html)

    return "".join(injected)
