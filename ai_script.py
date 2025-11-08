import os
import requests
import openai

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

# Example AI post content
prompt = "Write a 500-word blog post about duck hunting for beginners in a friendly tone."
response = openai.Completion.create(
model="text-davinci-003",
prompt=prompt,
max_tokens=700,
api_key=OPENAI_API_KEY
)
content = response.choices[0].text.strip()

# Post to WordPress
data = {
"title": "AI Generated Post",
"content": content,
"status": "draft"
}
r = requests.post(f"{WP_URL}/wp-json/wp/v2/posts", json=data, auth=(WP_USER, WP_APP_PASSWORD))
print(r.json())