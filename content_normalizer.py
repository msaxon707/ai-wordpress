import re

def normalize_content(text):
    """Clean up AI-generated text and format into proper HTML for WordPress."""
    if not text:
        return ""

    # Remove unwanted placeholders or tags like [HEAD], [META], etc.
    text = re.sub(r'\[.*?\]', '', text)

    # Convert markdown-style headings (###, ##) to HTML <h2>, <h3>
    text = re.sub(r'###\s*(.*)', r'<h3>\1</h3>', text)
    text = re.sub(r'##\s*(.*)', r'<h2>\1</h2>', text)

    # Ensure paragraphs are wrapped correctly
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    text = "".join(f"<p>{p}</p>" for p in paragraphs)

    # Clean up double tags or excess spaces
    text = re.sub(r'<p>\s*</p>', '', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()
