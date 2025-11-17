import random

def inject_affiliate_links(article_html, products):
    """
    Inserts affiliate buttons evenly throughout the article HTML.
    Each product is used only once.
    """

    if not products:
        print("[WARN] No affiliate products available to inject.")
        return article_html

    paragraphs = article_html.split("</p>")
    enhanced_paragraphs = []
    used = set()

    # Shuffle products for variety
    random.shuffle(products)
    max_links = min(len(products), 5)  # Use max 5 unique links per post

    print("[affiliate_injector] Adding Amazon links to article:")

    # Spacing: one button every 3 paragraphs
    insert_every = 3
    product_index = 0

    for i, paragraph in enumerate(paragraphs):
        if not paragraph.strip():
            continue

        enhanced_paragraphs.append(paragraph + "</p>")

        # Time to inject a link?
        if (i + 1) % insert_every == 0 and product_index < max_links:
            product = products[product_index]
            product_index += 1

            used.add(product["name"])
            print(f"[affiliate_injector] Added Amazon link: {product['url']}")

            # Styled button HTML block
            button_html = f"""
            <div style="margin:12px 0; text-align:left;">
              <a href="{product['url']}"
                 target="_blank"
                 rel="nofollow sponsored noopener"
                 style="background-color:#1b5e20;
                        color:#fff;
                        padding:10px 16px;
                        border-radius:8px;
                        text-decoration:none;
                        font-weight:bold;
                        display:inline-block;">
                 🔗 View {product['name']} on Amazon
              </a>
            </div>
            """
            enhanced_paragraphs.append(button_html.strip())

    injected_html = "\n".join(enhanced_paragraphs)
    return injected_html
