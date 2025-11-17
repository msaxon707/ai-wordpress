import re

def normalize_content(text: str) -> str:
    """
    Cleans GPT-generated text into valid HTML for WordPress.
    Removes markdown, hashtags, and unnecessary formatting.
    """

    if not text:
        return ""

    # Remove markdown headings like "###", "##"
    text = re.sub(r"#+\s*", "", text)

    # Remove hashtags (#outdoors #decor)
    text = re.sub(r"#\w+", "", text)

    # Replace markdown-style bold/italic
    text = text.replace("**", "").replace("*", "")

    # Replace line breaks with proper paragraph tags
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    html_paragraphs = [f"<p>{p}</p>" for p in paragraphs]
    text = "\n".join(html_paragraphs)

    # Normalize whitespace
    text = re.sub(r"\s{2,}", " ", text)
    text = text.strip()

    # Basic sanitization
    text = text.replace("<p><p>", "<p>").replace("</p></p>", "</p>")

    return text
