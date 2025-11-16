import logging
import markdown
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def format_content(markdown_text, affiliate_products=None):
    """
    Convert the given markdown text to HTML, sanitize it, and optionally append affiliate product links.
    `affiliate_products` should be a list of product dicts with keys: name, url, (optional description).
    Returns a safe HTML string ready for posting.
    """
    if markdown_text is None:
        return ""
    # Convert Markdown to HTML
    try:
        html = markdown.markdown(markdown_text, extensions=['extra'], output_format='html5')
    except Exception as e:
        logger.error(f"Markdown conversion error: {e}")
        # Fallback: replace line breaks with <br> as minimal formatting
        html = markdown_text.replace("\n", "<br>\n")
    # Sanitize HTML by removing any potentially harmful tags
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "iframe", "object"]):
        tag.decompose()
    safe_html = str(soup.body) if soup.body else str(soup)
    # Remove the enclosing <body> tags if present
    if safe_html.startswith("<body"):
        safe_html = safe_html[safe_html.find('>')+1 : safe_html.rfind('</body>')]
    # Append affiliate product links if provided
    if affiliate_products:
        logger.info("Injecting affiliate product links into content")
        product_list_items = []
        for prod in affiliate_products:
            name = prod.get("name") or "Product"
            url = prod.get("url") or "#"
            desc = prod.get("description") or ""
            link_html = f'<a href="{url}" target="_blank" rel="nofollow noopener">{name}</a>'
            if desc:
                item_html = f"<li>{link_html} - {desc}</li>"
            else:
                item_html = f"<li>{link_html}</li>"
            product_list_items.append(item_html)
        if product_list_items:
            products_html = "<ul>\n" + "\n".join(product_list_items) + "\n</ul>"
            safe_html += "\n<h3>Recommended Products:</h3>\n" + products_html
    return safe_html
