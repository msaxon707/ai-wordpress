# ai_script.py
from openai import OpenAI
import random
import re
import time
from logger_setup import setup_logger
from category_detector import detect_category
from config import Config

logger = setup_logger()
client = OpenAI()

EXTERNAL_LINKS = [
    "https://www.outdoorlife.com/",
    "https://www.countryliving.com/",
    "https://www.fieldandstream.com/",
]

def generate_article(topic: str, internal_links: list[str]) -> tuple[str, str, dict]:
    """Generate a complete SEO-optimized article with links and meta tags."""
    for attempt in range(3):
        try:
            include_affiliate = random.random() < Config.AFFILIATE_RATIO
            affiliate_text = (
                "\n\nIf you're looking for the best rustic gear and home essentials, "
                "check out our favorites [here](https://amzn.to/affiliate)."
                if include_affiliate else ""
            )

            prompt = f"""
            Write a 900-word SEO-optimized blog post titled '{topic}'.
            Include a strong H1 title, keyword-rich H2/H3s, and natural keyword placement.
            Add 2 internal links to these: {internal_links}.
            Add 2 external links from: {EXTERNAL_LINKS}.
            Maintain a warm, rustic, country-living tone.
            End with a call to action or reflection.
            {affiliate_text}
            """

            response = client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9
            )

            content = response.choices[0].message.content.strip()
            category = detect_category(content)

            # Extract SEO-friendly metadata
            h1_match = re.search(r"^# (.+)$", content, re.MULTILINE)
            title = h1_match.group(1) if h1_match else topic
            seo_meta = {
                "title": title,
                "description": f"Learn about {topic.lower()} and rustic living tips from The Saxon Blog.",
                "focus_keyphrase": topic.split()[0],
            }

            logger.info(f"📝 Article generated for topic: {topic} in category {category}")
            return content, category, seo_meta

        except Exception as e:
            logger.error(f"Error generating article: {e}")
            time.sleep(10)

    raise RuntimeError(f"❌ Failed to generate article for topic: {topic}")
