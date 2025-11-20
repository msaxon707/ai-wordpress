import os, requests, openai, json

BASE = os.getenv("WP_BASE_URL").rstrip("/")
USERNAME = os.getenv("WP_USERNAME")
APP_PASS = os.getenv("WP_APP_PASSWORD")

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def get_posts(page=1, per_page=25):
    url = f"{BASE}/wp-json/wp/v2/posts?status=publish&per_page={per_page}&page={page}"
    r = requests.get(url, auth=(USERNAME, APP_PASS))
    r.raise_for_status()
    return r.json()

def generate_meta(title, text):
    prompt = f"Generate SEO meta title and description for a blog post titled '{title}'. Return JSON."
    try:
        resp = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )
        data = json.loads(resp.choices[0].message.content)
        return data.get("title"), data.get("description")
    except Exception as e:
        print("[WARN]", e)
        return title, f"Discover more about {title.lower()} at The Saxon Blog."

def audit_post(p):
    result = {"id": p["id"], "title": p["title"]["rendered"], "fixes": []}
    content = p["content"]["rendered"]

    if not p.get("excerpt") or not p["excerpt"]["rendered"].strip():
        result["fixes"].append("excerpt missing")

    if not p.get("featured_media") or p["featured_media"] == 0:
        result["fixes"].append("no featured image")

    if "amazon.com" not in content:
        result["fixes"].append("no affiliate links")

    if content.count("href=\"https://thesaxonblog.com") < 2:
        result["fixes"].append("less than 2 internal links")

    return result

def main():
    page = 1
    per_page = 25
    while True:
        url = f"{BASE}/wp-json/wp/v2/posts?status=publish&per_page={per_page}&page={page}"
        r = requests.get(url, auth=(USERNAME, APP_PASS))
        if r.status_code == 400:
            print(f"[DONE] Reached end of posts at page {page}. Audit complete.")
            break
        r.raise_for_status()
        posts = r.json()
        if not posts:
            print(f"[DONE] No more posts found at page {page}. Audit complete.")
            break

        for p in posts:
            report = audit_post(p)
            if report["fixes"]:
                print(f"\nPost {report['id']} - {report['title']}")
                for f in report["fixes"]:
                    print("  →", f)

        total_pages = int(r.headers.get("X-WP-TotalPages", page))
        if page >= total_pages:
            print(f"[DONE] Processed all {total_pages} pages.")
            break
        page += 1
if __name__ == "__main__":
    main()
