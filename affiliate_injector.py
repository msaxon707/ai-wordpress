import random

def inject_affiliate_links(article_html, products):
    """
    Injects affiliate buttons into the article HTML every few paragraphs.
    Buttons are formatted for clean display in WordPress.
    """
    if not products:
        print("[WARN] No affiliate products available to inject.")
        return article_html

    paragraphs = article_html.split("</p>")
    enhanced_paragraphs = []
    used = set()

    # Randomize order of product links for variety
    random.shuffle(products)

    print("[affiliate_injector] Adding Amazon links to article:")

    for i, paragraph in enumerate(paragraphs):
        if not paragraph.strip():
            continue

        # Append paragraph content
        enhanced_paragraphs.append(paragraph + "</p>")

        # Every 2-3 paragraphs, insert a product link
        if i % 2 == 1 and products:
            product = None

            # Pick a product not used yet
            for p in products:
                if p["name"] not in used:
                    product = p
                    used.add(p["name"])
                    break

            # If all used, reset (ensures multiple buttons still appear)
            if not product:
                used.clear()
                product = random.choice(products)

            # Button HTML block
            button_html = f"""
            <div style="margin:10px 0;">
              <a href="{product['url']}" 
                 target="_blank" 
                 rel="nofollow sponsored noopener" 
                 style="background-color:#1b5e20;
                        color:#fff;
                        padding:10px 15px;
                        border-radius:6px;
                        text-decoration:none;
                        font-weight:bold;
                        display:inline-block;">
                 🔗 View {product['name']} on Amazon
              </a>
            </div>
            """
            enhanced_paragraphs.append(button_html.strip())
            print(f"[affiliate_injector] Added Amazon link: {product['url']}")

    # Combine all content back into one string
    injected_html = "\n".join(enhanced_paragraphs)
    return injected_html
