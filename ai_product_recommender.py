import openai
import urllib.parse
from config import OPENAI_API_KEY, OPENAI_MODEL, AMAZON_TAG

def generate_product_suggestions(article_text):
    """
    Ask OpenAI to suggest relevant outdoor/hunting gear
    based on the article content.
    """
    openai.api_key = OPENAI_API_KEY

    prompt = f"""
    You are an experienced outdoors gear reviewer.
    Based on the following article content, list 5 specific products
    that would be relevant for readers. Focus on items someone might
    buy on Amazon related to the article’s topic (hunting, fishing, camping, etc).

    Only output the product names (one per line), no explanations.

    ARTICLE:
    {article_text[:2500]}  # limit to prevent token overload
    """

    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=150
    )

    raw_output = response.choices[0].message["content"]
    lines = [line.strip("-• ") for line in raw_output.split("\n") if line.strip()]
    return lines[:5]  # keep top 5 results


def create_amazon_links(product_names):
    """
    Turn product names into Amazon search links with affiliate tag.
    """
    links = []
    for name in product_names:
        search_query = urllib.parse.quote_plus(name)
        url = f"https://www.amazon.com/s?k={search_query}&tag={AMAZON_TAG}"
        links.append({"name": name, "url": url})
    return links
