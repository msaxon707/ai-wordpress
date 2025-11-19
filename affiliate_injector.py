import random

AFFILIATE_LINK_FREQUENCY = 3

def inject_affiliate_links(content, products):
    """Inject Amazon links into paragraphs cleanly."""
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
            name = product.get("name", "View on Amazon")
            url = product.get("url", "#")
            injected.append(
                f'<p><a href="{url}" target="_blank" rel="nofollow noopener">'
                f'🔗 View {name} on Amazon</a></p>'
            )

    return "".join(injected)
