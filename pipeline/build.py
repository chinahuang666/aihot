"""Build stage: enrich stories with scores + write all static JSON outputs.

Outputs (task book §7):
  manifest.json, latest-selected.json, latest-all.json, hot.json,
  stories.json, daily/YYYY-MM-DD.json, source-status.json, search-index.json
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from .models import SCHEMA_VERSION, ALGO_VERSION
from .normalize import iso_to_unix
from . import score as score_mod

WINDOW_HOURS = 24


def _story_aux(story: dict, items_by_id: dict) -> dict:
    items = [items_by_id[i] for i in story["itemIds"] if i in items_by_id]
    src_ids = []
    roles, tiers = [], []
    times, engages = [], []
    primary_firsthand = False
    has_release = False
    has_contradiction = False
    for it in items:
        if it["sourceId"] not in src_ids:
            src_ids.append(it["sourceId"])
        roles.append(it.get("sourceRole", ""))
        tiers.append(it.get("trustTier", 1))
        if it.get("publishedAt"):
            times.append(it["publishedAt"])
        engages.append(sum(it.get("metrics", {}).values() or [0]))
        if it["id"] == story["primaryItemId"]:
            primary_firsthand = it.get("sourceRole") == "primary"
        eid = (it.get("externalId", "") or "").lower()
        url = (it.get("canonicalUrl", "") or "").lower()
        if eid.startswith("rel-") or "release" in url or "release" in eid:
            has_release = True
    aux = {
        "independentSources": src_ids,
        "roles": roles,
        "trustTiers": tiers,
        "item_times": times,
        "totalEngagement": sum(engages),
        "primaryRole": "primary" if primary_firsthand else "media",
        "hasRelease": has_release,
        "hasContradiction": has_contradiction,
        "primaryPublished": bool(items_by_id.get(story["primaryItemId"], {}).get("publishedAt")),
        "primaryUrl": bool(items_by_id.get(story["primaryItemId"], {}).get("canonicalUrl")),
    }
    return aux


def _status(story: dict, now_unix: float) -> str:
    if story.get("hasContradiction"):
        return "disputed"
    first = iso_to_unix(story["firstSeenAt"])
    age_h = (now_unix - first) / 3600.0 if first else 0
    heat = story["heatScore"]
    if age_h > 24 * 7:
        return "archived"
    if heat >= 0.7:
        return "hot"
    if heat >= 0.45:
        return "warming"
    if age_h > 24:
        return "cooling"
    return "new"


def build(items: list, stories_raw: list, sources: list, scoring: dict, out_dir: Path, window_hours: int = 72):
    out_dir = Path(out_dir)
    (out_dir / "daily").mkdir(parents=True, exist_ok=True)
    items_by_id = {it["id"]: it for it in items}
    weights = scoring.get("weights", {
        "heat": {"velocity": 0.35, "coverage": 0.25, "interaction": 0.20, "freshness": 0.20},
        "importance": {"industryImpact": 0.35, "originality": 0.25, "authority": 0.20, "endurance": 0.20},
        "confidence": {"firsthand": 0.40, "crossConfirm": 0.30, "histQuality": 0.20, "metaComplete": 0.10},
    })
    now = datetime.now(timezone.utc)
    now_unix = now.timestamp()
    generated_at = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    window_start = (now - timedelta(hours=window_hours)).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    stories = []
    for s in stories_raw:
        aux = _story_aux(s, items_by_id)
        sc = score_mod.compute_scores({**s, **aux}, {}, now_unix, weights)
        s.update({
            "heatScore": sc["heat"],
            "importanceScore": sc["importance"],
            "confidenceScore": sc["confidence"],
            "rankingReasons": sc["reasons"],
            "status": _status({**s, **aux}, now_unix),
        })
        stories.append(s)

    # sort: selected by combined score desc
    def combined(s):
        return 0.4 * s["heatScore"] + 0.4 * s["importanceScore"] + 0.2 * s["confidenceScore"]
    stories.sort(key=combined, reverse=True)

    selected = stories[: min(20, len(stories))]
    hot = sorted(stories, key=lambda s: s["heatScore"], reverse=True)[: min(15, len(stories))]

    today = now.strftime("%Y-%m-%d")
    daily_path = out_dir / "daily" / f"{today}.json"

    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": generated_at,
        "window": {"start": window_start, "end": generated_at, "hours": window_hours},
        "algoVersion": ALGO_VERSION,
        "data": {
            "files": [
                "manifest.json", "latest-selected.json", "latest-all.json",
                "hot.json", "stories.json", f"daily/{today}.json",
                "source-status.json", "search-index.json",
            ],
            "sourceCount": len(sources),
            "storyCount": len(stories),
            "itemCount": len(items),
        },
    }
    _write(out_dir / "manifest.json", manifest)
    _write(out_dir / "latest-selected.json", _envelope(SCHEMA_VERSION, generated_at, window_start,
                                                       "storyCount", len(selected), selected))
    _write(out_dir / "latest-all.json", _envelope(SCHEMA_VERSION, generated_at, window_start,
                                                  "storyCount", len(stories), stories))
    _write(out_dir / "hot.json", _envelope(SCHEMA_VERSION, generated_at, window_start,
                                           "storyCount", len(hot), hot))
    _write(out_dir / "stories.json", _envelope(SCHEMA_VERSION, generated_at, window_start,
                                               "storyCount", len(stories), stories))
    _write(daily_path, _envelope(SCHEMA_VERSION, generated_at, window_start,
                                 "storyCount", len(selected), selected))
    _write(out_dir / "source-status.json", _envelope(SCHEMA_VERSION, generated_at, window_start,
                                                    "sourceCount", len(sources), sources))
    # search index: flat list of story + item tokens
    search_index = []
    for s in stories:
        search_index.append({
            "type": "story", "id": s["id"], "slug": s["slug"],
            "title": s["headline"], "category": s["category"],
            "text": (s["whatHappened"] + " " + s["whyItMatters"]),
        })
    for it in items:
        search_index.append({
            "type": "item", "id": it["id"], "title": it.get("titleOriginal", ""),
            "sourceId": it.get("sourceId", ""),
            "text": it.get("excerpt", ""),
        })
    _write(out_dir / "search-index.json", _envelope(SCHEMA_VERSION, generated_at, window_start,
                                                    "entryCount", len(search_index), search_index))
    return {
        "stories": len(stories), "items": len(items), "sources": len(sources),
        "generatedAt": generated_at, "daily": str(daily_path),
    }


def _envelope(schema, gen, window_start, count_key, count, data):
    return {
        "schemaVersion": schema,
        "generatedAt": gen,
        "window": {"start": window_start, "end": gen},
        count_key: count,
        "data": data,
    }


def _write(path: Path, obj: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
