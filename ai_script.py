import os
import openai
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")

# New API client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

prompts = [
    "Write a short SEO-friendly blog post about deer hunting for a family-friendly outdoors blog.",
    "Write a blog post about the best deer hunting gear for beginners.",
    "Write a blog post with tips for tracking deer in the wild.",
    "Write a blog post about safety tips during deer hunting season.",
    "Write a blog post about the best deer hunting locations in the United States."
]

def generate_content(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful AI content writer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

def post_to_wordpress(title, content):
    post_data = {
        "title": title,
        "content": content,
        "status": "draft"
    }
    response = requests.post(
        WP_URL,
        json=post_data,
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )
    if response.status_code in [200, 201]:
        print(f"Post '{title}' created successfully!")
    else:
        print(f"Failed to create post '{title}': {response.text}")

for i, prompt in enumerate(prompts, start=1):
    title = f"Deer Hunting Post {i} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    content = generate_content(prompt)
    post_to_wordpress(title, content)

