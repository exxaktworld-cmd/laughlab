from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus, urlsplit, urlunsplit
import feedparser
import requests

HEADERS = {"User-Agent": "LaughLabAI/0.1 (public RSS research; contact: project owner)"}

def _date(entry):
    for key in ("published", "updated", "created"):
        raw = entry.get(key)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)

def _clean_url(url):
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))

def _fetch(url, source_name):
    try:
        response = requests.get(url, headers=HEADERS, timeout=18)
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
    except requests.RequestException as exc:
        print(f"[WARN] Feed unavailable ({source_name}): {exc}")
        return []
    items = []
    for e in parsed.entries[:30]:
        link = e.get("link", "")
        title = e.get("title", "").strip()
        if not link or not title:
            continue
        excerpt = e.get("summary", e.get("description", ""))
        items.append({
            "source": source_name,
            "title": title,
            "url": _clean_url(link),
            "excerpt": str(excerpt)[:1800],
            "published": _date(e).isoformat(),
            "engagement": int(e.get("num_comments", 0) or 0) + int(e.get("score", 0) or 0),
        })
    return items

def collect_stories(source_config):
    stories = []
    for sub in source_config.get("reddit_subreddits", []):
        url = f"https://www.reddit.com/r/{sub}/.rss?limit=25"
        stories.extend(_fetch(url, f"Reddit r/{sub}"))
    for query in source_config.get("google_news_queries", []):
        url = "https://news.google.com/rss/search?q=" + quote_plus(query) + "&hl=en-US&gl=US&ceid=US:en"
        stories.extend(_fetch(url, "Google News: " + query))
    seen, unique = set(), []
    for item in stories:
        key = item["url"] or item["title"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique
