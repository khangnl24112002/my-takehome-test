import requests
from slugify import slugify
from bs4 import BeautifulSoup

BASE = "https://support.optisigns.com"
LOCALE = "en-us"


import os

def fetch_articles():
    page = 1
    all_articles = []
    max_articles = int(os.environ.get("MAX_ARTICLES", "0"))  # 0 means no limit
    while True:
        url = f"{BASE}/api/v2/help_center/{LOCALE}/articles.json?page={page}&per_page=30"
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        data = res.json()
        articles = data.get("articles", [])
        all_articles.extend(articles)
        if max_articles > 0 and len(all_articles) >= max_articles:
            all_articles = all_articles[:max_articles]
            break
        if not data.get("next_page"):
            break
        page += 1
    return all_articles


def html_to_md(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    # giữ nguyên code block
    for pre in soup.find_all("pre"):
        code = pre.get_text()
        pre.replace_with(f"\n```\n{code.strip()}\n```\n")
    text = soup.get_text("\n").strip()
    return text


def fetch_and_convert():
    """
    Fetch all articles and return list of dict:
    {slug, title, md, url}
    """
    articles = fetch_articles()
    results = []

    for a in articles:
        title = (a.get("title") or "untitled").strip()
        slug = slugify(title, lowercase=True) or str(a["id"])
        body_html = a.get("body") or ""
        md_body = html_to_md(body_html)
        md = f"# {title}\n\n{md_body}\n\n---\n[Article URL]({a['html_url']})\n"

        results.append({
            "slug": slug,
            "title": title,
            "md": md,
            "url": a["html_url"]
        })

    return results
