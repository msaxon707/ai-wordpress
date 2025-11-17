import os
import openai

# Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
AFFILIATE_TAG = "thesaxonblog01-20"

openai.api_key = OPENAI_API_KEY


def generate_product_suggestions(article_text):
    """
    Uses AI to extract 3-6 relevant products from the article text.
    Works for both outdoor and decor topics.
    """
    prompt = f"""
    You are an assistant that identifies relevant shopping products from text.
    From the following article, extract 3 to 6 product ideas that someone reading this post might want to buy.
    Focus only on physical products, not abstract things.
    Return a short list of concise product keywords (no sentences).
    
    ARTICLE:
    {article_text}
    """

    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7,
            timeout=40
        )
        raw_output = response.choices[0].message["content"]
        product_names = [
            p.strip("•-– \n").lower()
            for p in raw_output.split("\n")
            if p.strip()
        ]
        # Remove duplicates and empty lines
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
    Convert product names into working Amazon search URLs.
    Example:
        "camping stove" -> "https://www.amazon.com/s?k=camping+stove&tag=thesaxonblog01-20"
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
    # Test function
    test_text = "I love camping trips, especially when I bring my favorite tent and hiking boots."
    products = generate_product_suggestions(test_text)
    links = create_amazon_links(products)
    print(products)
    for l in links:
        print(l)
