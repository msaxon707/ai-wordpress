# content_normalizer.py
from bs4 import BeautifulSoup

def normalize_content(html_content: str) -> str:
    """Clean up and format HTML output for WordPress posting."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Ensure paragraphs and spacing
    for tag in soup.find_all(["p", "h2", "h3"]):
        if not tag.text.strip():
            tag.decompose()

    # Add <p> where missing
    for text in soup.find_all(string=True):
        if text.parent.name not in ["p", "h1", "h2", "h3", "a"]:
            text.replace_with(f"<p>{text}</p>")

    clean_html = str(soup)
    return clean_html.strip()