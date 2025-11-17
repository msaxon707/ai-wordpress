import os
from openai import OpenAI

# === Environment Variables ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
AFFILIATE_TAG = "thesaxonblog01-20"

# === OpenAI Client Initialization ===
client = OpenAI(api_key=OPENAI_API_KEY)


def generate_product_suggestions(article_text):
    """
    Uses AI to extract 3–6 relevant physical product ideas from the given article text.
    Works for both decor and outdoor topics.
    """
    prompt = f"""
    You are a product recommendation assistant.
    From the following article, extract 3 to 6 relevant product ideas
    that a reader might be interested in buying.
    Focus on real, physical items (not abstract concepts or experiences).
    Return a plain list, one item per line. No numbers, no extra words.

    ARTICLE:
    {article_text}
    """

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )

        raw_output = response.choices[0].message.content
        product_names = [
            p.strip("•-– \n").lower()
            for p in raw_output.split("\n")
            if p.strip()
        ]

        # Remove duplicates and blanks
        clean = []
        for p in product_names:
            if p and p not in clean:
                clean.append(p)
        return clean

    except Exception as e:
        print(f"[ERROR] Failed to generate product suggestions: {e}")
        return []


def create_amazon_links(product_names):
    """
    Convert product names into working Amazon affiliate search URLs.
    Example: "camping stove" -> "https://www.amazon.com/s?k=camping+stove&tag=thesaxonblog01-20"
    """
    links = []
    for name in product_names:
        if not name:
            continue
        formatted = name.replace(" ", "+")
        url = f"https://www.amazon.com/s?k={formatted}&tag={AFFILIATE_TAG}"
        links.append({
            "name": name.title(),
            "url": url
        })
    return links


if __name__ == "__main__":
    # Quick test
    test_text = "I love decorating my porch with rustic lights and cozy furniture."
    products = generate_product_suggestions(test_text)
    links = create_amazon_links(products)
    print(products)
    for l in links:
        print(l)
