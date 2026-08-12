"""Connectors: turn a Source into a list of raw entry dicts.

Each connector returns entries with CAMELCASE keys:
  externalId, url, title, excerpt, author, publishedAt, language, category,
  entities(list), metrics(dict)
The pipeline layer normalizes these into Item objects.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Optional
import feedparser

from ..normalize import clean_text, normalize_time


def _entry_id(feed_url: str, entry) -> str:
    cand = getattr(entry, "id", None) or getattr(entry, "link", None) or getattr(entry, "title", None)
    return str(cand or entry.get("title", "unknown"))


def parse_rss(source: dict, content: bytes, client=None) -> list:
    feed = feedparser.parse(content)
    out = []
    for e in feed.entries:
        link = e.get("link") or ""
        title = clean_text(e.get("title", ""))
        summary = e.get("summary") or e.get("description") or ""
        summary = clean_text(re.sub(r"<[^>]+>", " ", summary))[:400]
        author = clean_text(e.get("author", ""))
        published = e.get("published") or e.get("updated") or e.get("pubDate")
        out.append({
            "externalId": _entry_id(source["url"], e),
            "url": link,
            "title": title,
            "excerpt": summary,
            "author": author,
            "publishedAt": normalize_time(published),
            "language": source.get("language", "en"),
            "category": source.get("category", "industry"),
            "entities": [],
            "metrics": {},
        })
    return out


def parse_github_release(source: dict, content: bytes, client=None) -> list:
    try:
        data = json.loads(content)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    out = []
    for rel in data:
        tag = rel.get("tag_name") or rel.get("name") or "unknown"
        name = rel.get("name") or tag
        body = clean_text(re.sub(r"<[^>]+>", " ", rel.get("body", "") or ""))[:400]
        url = rel.get("html_url") or source["url"]
        published = rel.get("published_at") or rel.get("created_at")
        out.append({
            "externalId": f"rel-{tag}",
            "url": url,
            "title": f"{source.get('name', 'repo')} 发布 {tag}",
            "excerpt": body or name,
            "author": source.get("name", ""),
            "publishedAt": normalize_time(published),
            "language": source.get("language", "en"),
            "category": "developer",
            "entities": [],
            "metrics": {"prerelease": bool(rel.get("prerelease"))},
        })
    return out


def parse_github_atom(source: dict, content: bytes, client=None) -> list:
    """Parse a public GitHub *releases* Atom feed.

    Uses https://github.com/{owner}/{repo}/releases.atom which is NOT subject
    to the api.github.com 60 req/hour unauthenticated rate limit, so it is the
    robust default for the MVP (no token required).
    """
    feed = feedparser.parse(content)
    out = []
    for e in feed.entries:
        tag = (e.get("title") or "unknown").strip()
        link = e.get("link") or source["url"].replace(".atom", "")
        updated = e.get("updated") or e.get("published")
        body = ""
        if e.get("content"):
            body = clean_text(re.sub(r"<[^>]+>", " ", e["content"][0].get("value", "")))[:400]
        elif e.get("summary"):
            body = clean_text(re.sub(r"<[^>]+>", " ", e["summary"]))[:400]
        out.append({
            "externalId": f"rel-{tag}",
            "url": link,
            "title": f"{source.get('name', 'repo')} 发布 {tag}",
            "excerpt": body or tag,
            "author": source.get("name", ""),
            "publishedAt": normalize_time(updated),
            "language": source.get("language", "en"),
            "category": "developer",
            "entities": [],
            "metrics": {},
        })
    return out


def parse_hn(source: dict, content: bytes, client=None) -> list:
    try:
        data = json.loads(content)
    except Exception:
        return []
    hits = data.get("hits", [])
    out = []
    for h in hits:
        title = clean_text(h.get("title") or h.get("story_title") or "")
        if not title:
            continue
        object_id = h.get("objectID") or str(h.get("id"))
        url = h.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
        points = h.get("points") or 0
        num_comments = h.get("num_comments") or 0
        out.append({
            "externalId": f"hn-{object_id}",
            "url": url,
            "title": title,
            "excerpt": clean_text(h.get("story_text") or h.get("comment_text") or "")[:400],
            "author": clean_text(h.get("author") or ""),
            "publishedAt": normalize_time(h.get("created_at")),
            "language": "en",
            "category": source.get("category", "industry"),
            "entities": [],
            "metrics": {"points": points, "comments": num_comments},
        })
    return out


def parse_arxiv(source: dict, content: bytes, client=None) -> list:
    feed = feedparser.parse(content)
    out = []
    for e in feed.entries:
        link = e.get("link") or ""
        title = clean_text(e.get("title", ""))
        summary = clean_text(re.sub(r"<[^>]+>", " ", e.get("summary", "")))[:400]
        authors = ", ".join([a.get("name", "") for a in e.get("authors", [])][:3])
        cat = source.get("category", "research")
        for c in e.get("tags", []):
            if c.get("term", "").startswith("cs."):
                cat = "research"
                break
        out.append({
            "externalId": e.get("id", link),
            "url": link,
            "title": title,
            "excerpt": summary,
            "author": authors,
            "publishedAt": normalize_time(e.get("published")),
            "language": "en",
            "category": cat,
            "entities": [c.get("term", "") for c in e.get("tags", [])][:5],
            "metrics": {},
        })
    return out


def parse_api(source: dict, content: bytes, client=None) -> list:
    try:
        data = json.loads(content)
    except Exception:
        return []
    items = source.get("itemsPath")
    if items:
        for key in items.split("."):
            if isinstance(data, dict):
                data = data.get(key, [])
            else:
                break
    if not isinstance(data, list):
        data = [data] if isinstance(data, dict) else []
    out = []
    for d in data[:50]:
        if not isinstance(d, dict):
            continue
        out.append({
            "externalId": str(d.get("id") or d.get("guid") or d.get("url") or len(out)),
            "url": d.get("url") or d.get("link") or source["url"],
            "title": clean_text(str(d.get("title") or d.get("name") or "")),
            "excerpt": clean_text(str(d.get("summary") or d.get("description") or d.get("excerpt") or ""))[:400],
            "author": clean_text(str(d.get("author") or "")),
            "publishedAt": normalize_time(d.get("publishedAt") or d.get("date") or d.get("createdAt")),
            "language": source.get("language", "en"),
            "category": source.get("category", "industry"),
            "entities": [],
            "metrics": {},
        })
    return out


CONNECTORS = {
    "rss": parse_rss,
    "atom": parse_rss,
    "github_release": parse_github_release,
    "github_release_atom": parse_github_atom,
    "hn": parse_hn,
    "arxiv": parse_arxiv,
    "api": parse_api,
}


def parse_source(source: dict, content: bytes, client=None) -> list:
    fn = CONNECTORS.get(source.get("type"), parse_rss)
    return fn(source, content, client)
