import os
import openai
import random
import re
import textwrap

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-3.5-turbo"

def generate_meta(title, topic):
    """Generate SEO title (≤60 chars) and meta description (≤160 chars)."""
    seo_title = (title[:57] + "...") if len(title) > 60 else title
    prompt = f"Write a concise 160-character meta description for a blog post about {topic}."
    completion = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    meta_desc = completion.choices[0].message["content"].strip()
    if len(meta_desc) > 160:
        meta_desc = meta_desc[:157] + "..."
    return seo_title, meta_desc

def generate_content(topic, keyword_list, affiliate_links):
    """Generate full post content with headings, affiliate links, and internal link placeholder."""
    keyword_text = ", ".join(keyword_list)
    affiliate_text = " ".join(
        [f'<p><a href="{link}" target="_blank" rel="nofollow noopener">Buy on Amazon</a></p>' for link in affiliate_links]
    )

    prompt = f"""
    Write a detailed, SEO-optimized blog post about '{topic}'.
    Include H2 and H3 headings, a conversational intro, and a conclusion.
    Use the following keywords naturally: {keyword_text}.
    Do not include a top image.
    Add a credit line at the end that says "Image courtesy of Pexels."
    Add {affiliate_text} naturally within the content.
    Include this placeholder at the bottom for internal links: {{internal_links}}
    """

    completion = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    content = completion.choices[0].message["content"].strip()

    # Ensure it has at least one H2
    if "<h2>" not in content:
        content = re.sub(r"(\n|$)", "\n<h2>Key Takeaways</h2>", content, count=1)

    return textwrap.dedent(content)

def extract_focus_keyword(title):
    """Extract focus keyword from the post title."""
    keyword = re.sub(r"[^\w\s]", "", title).strip()
    return keyword
def generate_blog_post(topic):
    title = f"{topic.title()}"
    focus = topic.lower().replace(" ", ", ")
    html_body = f"<h2>{title}</h2><p>This article covers {topic} in detail for readers interested in outdoor living, hunting, and family life.</p>"
    return title, focus, html_body