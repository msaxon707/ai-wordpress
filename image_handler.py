import requests
from config import PEXELS_API_KEY

def fetch_image(query):
    """Fetch an image from Pexels."""
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 1, "orientation": "landscape"}
    res = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params)
    if res.status_code == 200 and res.json()["photos"]:
        photo = res.json()["photos"][0]
        return photo["src"]["large"], photo.get("alt", query)
    return None, None
