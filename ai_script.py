import osimport os
import requests
from requests.auth import HTTPBasicAuth
import openai
from openai.error import RateLimitError, APIError

# Load environment variables
WP_URL = os.getenv("WP_URL", "https://thesaxonbelong.com/wp-json/wp/v2/posts")
WP_USERNAME = os.getenv("WP_USERNAME", "megansaxon9@gmail.com")
WP_PASSWORD = os.getenv("WP_PASSWORD", "Brayden2012$")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

openai.api_key = OPENAI_API_KEY

def generate_content(prompt):
    """
    Attempts to generate content using OpenAI Chat API.
    If quota is exceeded or API fails, raises the exception.
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except RateLimitError:
        print("OpenAI quota exceeded. Falling back to placeholder content.")
        raise
    except APIError as e:
        print(f"OpenAI API error: {e}. Using placeholder content.")
        raise

def post_to_wordpress(title, content, status="draft"):
    """
    Posts a draft to WordPress.
    """
    payload = {
        "title": title,
        "content": content,
        "status": status
    }
    response = requests.post(
        WP_URL,
        json=payload,
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )
    if response.status_code == 201:
        print(f"Draft successfully created! Post ID: {response.json().get('id')}")
    else:
        print(f"Failed to create draft. Status code: {response.status_code}")
        print("Response:", response.text)

if __name__ == "__main__":
    prompt = "Write a short blog post about deer hunting tips."
    
    try:
        content = generate_content(prompt)
    except Exception:
        # Fallback content if OpenAI fails
        content = "This is a placeholder draft post about deer hunting. OpenAI API quota exceeded or API error occurred."

    post_to_wordpress("Deer Hunting Tips", content)

