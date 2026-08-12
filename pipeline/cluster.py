"""Event clustering (task book §8).

Groups near-duplicate items into Stories, identifies independent sources,
and applies manual overrides (merge / split / hide / source-trust).
Relationship types: same_event, update_of, commentary_on, contradicts.
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional
from .dedupe import Deduplicator, title_tokens, jaccard
from .models import Item, Story, make_item_id, SCHEMA_VERSION, ALGO_VERSION
from .normalize import now_iso

SLUG_RE = re.compile(r"[^a-z0-9\u4e00-\u9fff]+")


def make_slug(text: str) -> str:
    base = SLUG_RE.sub("-", (text or "story").lower()).strip("-")
    base = base[:60]
    return base or "story"


class Clusterer:
    def __init__(self, overrides: dict = None):
        self.overrides = overrides or {}
        self.hide = set(self.overrides.get("hide", {}).get("itemIds", []) or
                        self.overrides.get("hide", {}).get("storyIds", []) or [])

    def cluster(self, items: list) -> list:
        # 1) apply explicit splits: keep some items separate
        split_ids = set(self.overrides.get("split", {}).get("itemIds", []) or [])
        # 2) union-find over near-duplicate pairs
        parent = {it.id: it.id for it in items}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        dd = Deduplicator()
        dd.by_source_external = {(it.sourceId, it.externalId): it for it in items}
        pairs = dd.near_duplicate_pairs(items)
        for a, b in pairs:
            if a.id in split_ids or b.id in split_ids:
                continue
            union(a.id, b.id)

        # group
        groups = defaultdict(list)
        for it in items:
            if it.id in self.hide:
                continue
            groups[find(it.id)].append(it)

        stories = []
        for gid, group in groups.items():
            if not group:
                continue
            story = self._build_story(group)
            stories.append(story)

        # explicit merges: move items from one story into another
        merge = self.overrides.get("merge", {})
        merge_map = merge.get("into", {}) if isinstance(merge, dict) else {}
        if merge_map:
            by_id = {s.id: s for s in stories}
            for target_id, sources in merge_map.items():
                if target_id not in by_id:
                    continue
                tgt = by_id[target_id]
                for sid in sources:
                    src = by_id.pop(sid, None)
                    if not src:
                        continue
                    tgt.item_ids = sorted(set(tgt.item_ids) | set(src.item_ids))
                    tgt.entities = sorted(set(tgt.entities) | set(src.entities))
                stories = list(by_id.values())

        return stories

    def _build_story(self, group: list) -> Story:
        # primary = earliest published, then most authoritative
        def pub(it):
            return it.publishedAt or it.discoveredAt
        ordered = sorted(group, key=lambda it: (pub(it) or ""))
        primary = ordered[0]
        # first_seen = min published, last_updated = max published/discovered
        times = [it.publishedAt for it in group if it.publishedAt] + \
                [it.discoveredAt for it in group]
        first_seen = min(times) if times else now_iso()
        last_updated = max(times) if times else now_iso()
        # independent sources = distinct sourceId
        src_ids = sorted({it.sourceId for it in group})
        entities = sorted({e for it in group for e in it.entities})
        # rule-based summary
        from . import summarize
        summ = summarize.rule_summary(group, primary)
        headline = summ["headline"]
        story_id = make_item_id("story", primary.canonicalUrl or primary.titleOriginal)[:12]
        return Story(
            id=story_id,
            slug=make_slug(headline) or story_id,
            headline=headline,
            headlineZh=summ.get("headline_zh", ""),
            whatHappened=summ["whatHappened"],
            whyItMatters=summ["whyItMatters"],
            category=primary.category,
            entities=entities,
            firstSeenAt=first_seen,
            lastUpdatedAt=last_updated,
            status="new",
            heatScore=0.0, importanceScore=0.0, confidenceScore=0.0,
            rankingReasons=[],
            itemIds=[it.id for it in ordered],
            primaryItemId=primary.id,
            claims=summ["claims"],
            summaryVersion=ALGO_VERSION,
        )
