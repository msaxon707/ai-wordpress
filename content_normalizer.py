import re

def normalize_content(content: str) -> str:
    """Clean up AI-generated HTML and ensure SEO-friendly formatting."""
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = re.sub(r"(#+\s)", "<h2>", content)
    content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content)
    content = content.replace("#", "").replace("**", "")
    content = content.strip()

    if not content.startswith("<p>"):
        content = f"<p>{content}</p>"
    return content
