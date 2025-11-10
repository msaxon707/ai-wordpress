from openai import OpenAI
import re
from config import MODEL, OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_title_and_focus(topic: str):
    """Generate blog title and SEO keyword."""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": f"Create an SEO blog title and focus keyword for: {topic}"}],
    )
    content = resp.choices[0].message.content.strip()
    title_match = re.search(r'"title":\s*"([^"]+)"', content)
    focus_match = re.search(r'"focus_keyword":\s*"([^"]+)"', content)
    title = title_match.group(1) if title_match else topic.title()
    focus = focus_match.group(1) if focus_match else topic.lower()
    return title, focus


def generate_html_body(topic: str, category: str):
    """Generate HTML post body."""
    prompt = f"""
Write a 900-1100 word blog post for The Saxon Blog about '{topic}'.
Include HTML headings (h2, h3), short paragraphs, friendly tone.
Focus on {category}. Include tips, insights, and readability.
Return only HTML content.
"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()
