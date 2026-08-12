"""Normalization: URL, fields, time."""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import re

# Query params that carry no semantic meaning and should be stripped for dedup.
_STRIP_QUERY_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "spm", "from", "share", "sharefrom", "scene", "click", "timestamp", "t",
}


def normalize_url(url: str) -> str:
    """Strip tracking params, fragments; lowercase host; sort remaining query."""
    try:
        p = urlparse(url)
    except Exception:
        return url
    if not p.scheme or not p.netloc:
        return url
    netloc = p.netloc.lower()
    path = p.path or "/"
    path = re.sub(r"/+", "/", path)
    if path.endswith("/") and len(path) > 1:
        path = path.rstrip("/")
    qs = parse_qsl(p.query, keep_blank_values=False)
    kept = [(k, v) for k, v in qs if k.lower() not in _STRIP_QUERY_PARAMS]
    kept.sort()
    query = urlencode(kept)
    return urlunparse((p.scheme.lower(), netloc, path, "", query, ""))


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_time(value) -> Optional[str]:
    """Parse many time formats to ISO 8601 UTC, preserving naive-as-original.

    Returns ISO string with UTC 'Z' when tz known, else naive ISO.
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        s = str(value).strip()
        if not s:
            return None
        # Try RFC822 (feeds)
        try:
            dt = parsedate_to_datetime(s)
            if dt is None:
                raise ValueError
        except Exception:
            # Try ISO
            try:
                dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            except Exception:
                # Last resort: look for a date-ish token
                m = re.search(r"(\d{4}-\d{2}-\d{2})", s)
                if not m:
                    return None
                try:
                    dt = datetime.fromisoformat(m.group(1))
                except Exception:
                    return None
    if dt.tzinfo is None:
        return dt.replace(microsecond=0).isoformat()
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iso_to_unix(iso: Optional[str]) -> float:
    if not iso:
        return 0.0
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return 0.0
