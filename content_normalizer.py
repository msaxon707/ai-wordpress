import re

def normalize_content(text: str) -> str:
    """Clean and format the AI-generated article into valid HTML for WordPress."""
    if not text:
        return ""

    # --- Remove placeholders like [HEAD], [META], [BODY] ---
    text = re.sub(r'\[(HEAD|META|TITLE|BODY)\]', '', text, flags=re.IGNORECASE)

    # --- Fix headings ---
    text = re.sub(r'###\s*(.+)', r'<h3>\1</h3>', text)
    text = re.sub(r'##\s*(.+)', r'<h2>\1</h2>', text)
    text = re.sub(r'#\s*(.+)', r'<h1>\1</h1>', text)

    # --- Clean markdown links and ensure plain text URLs stay visible ---
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)

    # --- Wrap paragraphs in <p> tags ---
    parts = [p.strip() for p in text.split('\n') if p.strip()]
    html = ''.join(f"<p>{p}</p>" for p in parts)

    # --- Final cleanup ---
    html = re.sub(r'<p>\s*</p>', '', html)
    html = re.sub(r'\s+', ' ', html)

    return html.strip()
