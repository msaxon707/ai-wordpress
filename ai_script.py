import os
import openai
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

# -------------------------
# Environment variables (do NOT hardcode your API keys or WordPress credentials)
# -------------------------
# In Coolify, set these under Configuration -> Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Your OpenAI API key
WP_URL = os.getenv("WP_URL") # Example: https://thesaxonbelong.com/wp-json/wp/v2/posts
WP_USERNAME = os.getenv("WP_USERNAME") # Your WordPress admin username
WP_PASSWORD = os.getenv("WP_PASSWORD") # Your WordPress application password

# -------------------------
# OpenAI Setup
# -------------------------
openai.api_key = OPENAI_API_KEY

# -------------------------
# List of prompts for multiple posts
# -------------------------
prompts = [
"Write a short SEO-friendly blog post about deer hunting for a family-friendly outdoors blog.",
"Write a blog post about choosing the best deer hunting gear.",
"Write a blog post about tips for beginners in deer hunting.",
"Write a blog post about the importance of safety in deer hunting.",
"Write a blog post about the best duck hunting spots in the USA."
]

# -------------------------
# Function to generate AI content
# -------------------------
def generate_content(prompt):
response = openai.ChatCompletion.create(
model="gpt-3.5-turbo",
messages=[
{"role": "system", "content": "You are a helpful AI content writer."},
{"role": "user", "content": prompt}
],
max_tokens=500,
)
return response.choices[0].message.content.strip()

# -------------------------
# Function to post to WordPress
# -------------------------
def post_to_wordpress(title, content):
post_data = {
"title": title,
"content": content,
"status": "draft" # Change to "publish" if you want posts live immediately
}
response = requests.post(
WP_URL,
json=post_data,
auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
)
if response.status_code in [200, 201]:
print(f"Post '{title}' created successfully!")
else:
print(f"Failed to create post '{title}':", response.text)

# -------------------------
# Main loop to create posts
# -------------------------
for i, prompt in enumerate(prompts, start=1):
title = f"AI Post {i} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
content = generate_content(prompt)
post_to_wordpress(title, content)
