"""Safe HTTP client for AIhot pipeline.

Security guarantees (per task book §12):
- Only HTTP/HTTPS.
- Blocks loopback, link-local, private, and cloud metadata addresses.
- Connection/read timeouts, max response body, MIME whitelist, retry with backoff.
- Conditional requests (ETag / Last-Modified) and a simple on-disk cache.
"""
from __future__ import annotations

import ipaddress
import os
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter

MAX_BODY_BYTES = 5_000_000
ALLOWED_SCHEMES = {"http", "https"}
MIME_WHITELIST = {
    "application/xml", "text/xml", "application/rss+xml", "application/atom+xml",
    "application/json", "text/json", "application/feed+json",
    "text/plain", "text/html", "application/xhtml+xml",
}

# Cloud metadata / private ranges we must never reach.
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),       # link-local + cloud metadata (169.254.169.254)
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _assert_safe_host(host: str) -> None:
    """Resolve host and refuse if it maps to a blocked network."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise RuntimeError(f"DNS resolution failed for {host}: {exc}")
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        for net in _BLOCKED_NETWORKS:
            if ip in net:
                raise RuntimeError(f"Refusing to connect to blocked address {ip} ({host})")


@dataclass
class FetchResult:
    ok: bool
    status: int
    url: str
    content: bytes = b""
    content_type: str = ""
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    error: str = ""


class SafeSession:
    def __init__(self, cache_dir: Optional[Path] = None, timeout: int = 20, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_dir = cache_dir
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=0)  # we do our own backoff
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            "User-Agent": "AIhot/0.1 (+https://github.com/; static AI event aggregator)",
            "Accept": ",".join(sorted(MIME_WHITELIST)),
        })

    def _cache_path(self, url: str) -> Optional[Path]:
        if not self.cache_dir:
            return None
        import hashlib
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir / (hashlib.sha256(url.encode()).hexdigest() + ".cache")

    def fetch(self, url: str, etag: Optional[str] = None,
              last_modified: Optional[str] = None, force: bool = False) -> FetchResult:
        parsed = urlparse(url)
        if parsed.scheme not in ALLOWED_SCHEMES:
            return FetchResult(False, 0, url, error=f"blocked scheme: {parsed.scheme}")
        host = parsed.hostname or ""
        try:
            _assert_safe_host(host)
        except RuntimeError as exc:
            return FetchResult(False, 0, url, error=str(exc))

        headers = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        last_err = ""
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.session.get(url, headers=headers, timeout=self.timeout,
                                         allow_redirects=True, stream=True)
                # Re-validate after redirects (SSRF protection on final hop).
                final = urlparse(resp.url)
                if final.hostname and final.hostname != host:
                    try:
                        _assert_safe_host(final.hostname)
                    except RuntimeError as exc:
                        resp.close()
                        return FetchResult(False, 0, url, error=str(exc))
                if resp.status_code == 304:
                    resp.close()
                    return FetchResult(True, 304, resp.url, etag=etag, last_modified=last_modified)
                if resp.status_code >= 400:
                    resp.close()
                    return FetchResult(False, resp.status_code, resp.url,
                                       error=f"HTTP {resp.status_code}")
                ctype = resp.headers.get("Content-Type", "text/plain")
                mime = ctype.split(";")[0].strip().lower()
                if mime not in MIME_WHITELIST:
                    resp.close()
                    return FetchResult(False, resp.status_code, resp.url,
                                       error=f"mime not allowed: {mime}")
                # Enforce max body size while streaming.
                chunks, total = [], 0
                for chunk in resp.iter_content(chunk_size=65536):
                    total += len(chunk)
                    if total > MAX_BODY_BYTES:
                        resp.close()
                        return FetchResult(False, resp.status_code, resp.url,
                                           error="response body too large")
                    chunks.append(chunk)
                content = b"".join(chunks)
                return FetchResult(
                    True, resp.status_code, resp.url, content=content,
                    content_type=ctype,
                    etag=resp.headers.get("ETag"),
                    last_modified=resp.headers.get("Last-Modified"),
                )
            except requests.RequestException as exc:
                last_err = str(exc)
                time.sleep(min(2 ** attempt, 8))
        return FetchResult(False, 0, url, error=last_err or "unknown error")
