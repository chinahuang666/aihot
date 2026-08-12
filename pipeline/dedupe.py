"""Deduplication and near-duplicate detection (task book §8)."""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict

from .models import Item, make_item_id

_STOP = set("的 了 是 在 和 与 及 a an the of to in on for and or is are was were be with 发布 推出 宣布 模型 开源".split())


def _prod_entities(entity_list) -> set:
    return {e for e in (entity_list or []) if e.startswith("prod:")}


def _ver_entities(entity_list) -> set:
    return {e for e in (entity_list or []) if e.startswith("ver:")}


def title_tokens(title: str) -> set:
    t = re.sub(r"[^\w\u4e00-\u9fff]+", " ", (title or "").lower())
    toks = set(t.split())
    return {w for w in toks if w and w not in _STOP and len(w) > 1}


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def content_hash(text: str) -> str:
    norm = re.sub(r"\s+", "", text or "")
    return hashlib.sha256(norm.encode("utf-8", "replace")).hexdigest()


def is_near_duplicate(a: Item, b: Item, title_jac: float = 0.6,
                      strong_jac: float = 0.2, ver_jac: float = 0.1) -> bool:
    """Decide whether two items describe the same event.

    Merge when ANY of:
      * exact content hash (same text), OR
      * title Jaccard >= title_jac (very similar wording), OR
      * they share a *product* entity AND title Jaccard >= strong_jac, OR
      * they share BOTH a product entity AND a version AND title Jaccard >= ver_jac
        (this lets "vLLM v0.27.0" / "vLLM 0.27.0 is available" merge even when
         wording barely overlaps, while a bare version collision across two
         DIFFERENT products never merges).

    Two items from the SAME source are NEVER merged: a single source's distinct
    entries are distinct events (e.g. consecutive releases of one repo). Only
    cross-source coverage of one event should collapse. Sharing only a company
    (org:) is also deliberately NOT enough, so generic "OpenAI news" items don't
    collapse together (keeps duplicate rate < 5%).
    """
    if a.sourceId == b.sourceId:
        return False
    if a.contentHash and b.contentHash and a.contentHash == b.contentHash:
        return True
    ja = jaccard(title_tokens(a.titleOriginal), title_tokens(b.titleOriginal))
    if ja >= title_jac:
        return True
    shared_prod = _prod_entities(a.entities) & _prod_entities(b.entities)
    if shared_prod and ja >= strong_jac:
        return True
    if shared_prod and (_ver_entities(a.entities) & _ver_entities(b.entities)) and ja >= ver_jac:
        return True
    return False


class Deduplicator:
    def __init__(self):
        self.by_source_external: dict = {}
        self.by_url: dict = {}
        self.by_content: dict = {}

    def add(self, item: Item) -> bool:
        """Return True if item is new (not duplicate)."""
        key_se = (item.sourceId, item.externalId)
        if key_se in self.by_source_external:
            return False
        self.by_source_external[key_se] = item
        if item.canonicalUrl:
            self.by_url.setdefault(item.canonicalUrl, []).append(item)
        if item.contentHash:
            self.by_content.setdefault(item.contentHash, []).append(item)
        return True

    def near_duplicate_pairs(self, items: list, time_window_sec: int = 86400 * 2,
                             title_jac: float = 0.6) -> list:
        """Return candidate (a, b) pairs that are near-duplicates."""
        pairs = []
        n = len(items)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = items[i], items[j]
                # time window: out-of-window items are unrelated events
                ta, tb = _to_unix(a.publishedAt), _to_unix(b.publishedAt)
                if ta and tb and abs(ta - tb) > time_window_sec:
                    continue
                if is_near_duplicate(a, b, title_jac=title_jac):
                    pairs.append((a, b))
        return pairs


def _to_unix(iso):
    if not iso:
        return 0
    try:
        from .normalize import iso_to_unix
        return iso_to_unix(iso)
    except Exception:
        return 0
