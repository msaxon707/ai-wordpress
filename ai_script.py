import os
import requests
from openai import OpenAI

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_URL = os.getenv("WP_URL")          # e.g., 'https://yourdomain.com/wp-json/wp/v2/posts'
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")
MODEL = os.getenv("MODEL", "gpt-4-turbo")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_content(topic):
    prompt = (
        f"Write a detailed, SEO-optimized blog post about '{topic}'. "
        "Target 700-800 words. Use short paragraphs, headings, and subheadings. "
        "Make it engaging and informative for outdoors/deer hunting enthusiasts."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a professional blog writer and SEO expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content

def post_to_wordpress(title, content):
    data = {
        "title": title,
        "content": content,
        "status": "publish"  # use 'draft' if you want to review before publishing
    }
    response = requests.post(
        WP_URL,
        json=data,
        auth=(WP_USERNAME, WP_PASSWORD)
    )
    if response.status_code == 201:
        print(f"Post '{title}' successfully published!")
    else:
        print("Error publishing post:", response.text)

if __name__ == "__main__":
    topics = [
        "Deer hunting tips for beginners",
        "Best deer hunting gear in 2025",
        "How to track deer effectively",
        # add more topics as you like
    ]
    
    for topic in topics:
        print(f"Generating content for: {topic}")
        content = generate_content(topic)
        post_to_wordpress(topic, content)

