"""AIhot pipeline orchestrator.

Usage:
    python -m pipeline run            # fetch -> normalize -> dedupe -> cluster -> score -> build
    python -m pipeline run --once     # same, single pass
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from .config import Config
from .httpclient import SafeSession
from .normalize import normalize_url, clean_text, now_iso, iso_to_unix  # noqa
from . import models
from .connectors import parse_source
from .dedupe import Deduplicator
from .cluster import Clusterer
from .entities import extract_entities
from .build import build

ROOT = Path(__file__).resolve().parents[1]


def run_once(force: bool = False) -> dict:
    cfg = Config(ROOT)
    sources_def = cfg.load_sources()
    scoring = cfg.load_scoring()
    overrides = cfg.load_overrides()
    cache_dir = ROOT / ".cache"
    session = SafeSession(cache_dir=cache_dir, timeout=20)

    sources_out = []
    items = []
    dedup = Deduplicator()
    now = now_iso()

    ok, fail = 0, 0
    for sd in sources_def:
        if not sd.get("enabled", True):
            continue
        src = models.Source(**{k: sd[k] for k in models.Source.__dataclass_fields__ if k in sd})
        res = session.fetch(sd["url"], force=force)
        if not res.ok:
            src.consecutiveFailures += 1
            src.healthStatus = "failed"
            src.lastError = res.error
            if res.status:
                src.lastHttpStatus = res.status
            sources_out.append(src.to_dict())
            fail += 1
            continue
        # degraded if 304 with no new content or low item count
        try:
            entries = parse_source(sd, res.content, session)
        except Exception as e:
            src.healthStatus = "failed"
            src.lastError = f"parse error: {e}"
            src.consecutiveFailures += 1
            sources_out.append(src.to_dict())
            fail += 1
            continue

        added = 0
        for e in entries:
            iid = models.make_item_id(sd["id"], e.get("externalId", e.get("url", "")))
            it = models.Item(
                id=iid,
                sourceId=sd["id"],
                externalId=str(e.get("externalId", e.get("url", ""))),
                canonicalUrl=normalize_url(e.get("url", "")),
                titleOriginal=clean_text(e.get("title", "")),
                titleZh=clean_text(e.get("title", "")),
                excerpt=clean_text(e.get("excerpt", "")),
                author=clean_text(e.get("author", "")),
                language=e.get("language", "en"),
                publishedAt=e.get("publishedAt"),
                discoveredAt=now,
                contentHash=models._sha256((e.get("title", "") + e.get("excerpt", ""))[:500]),
                category=e.get("category", sd.get("category", "industry")),
                entities=sorted(set(extract_entities(e.get("title", ""), e.get("excerpt", ""))
                                    + (e.get("entities", []) or []))),
                metrics=e.get("metrics", {}) or {},
                sourceRole=sd.get("role", "media"),
                trustTier=sd.get("trustTier", 1),
            )
            if dedup.add(it):
                items.append(it.to_dict())
                added += 1
        src.lastSuccessAt = now
        src.lastHttpStatus = res.status
        src.lastItemCount = len(entries)
        src.consecutiveFailures = 0
        src.healthStatus = "ok" if added else "degraded"
        src.lastError = ""
        sources_out.append(src.to_dict())
        ok += 1

    # cluster
    item_objs = [models.Item(**i) for i in items]
    focused = _focus_recent(item_objs, scoring)
    items_dicts = [it.to_dict() for it in focused]
    clusterer = Clusterer(overrides)
    stories_raw = clusterer.cluster(focused)
    stories_raw = [s.to_dict() for s in stories_raw]

    window_h = int(scoring.get("ingest", {}).get("windowHours", 72))
    report = build(items_dicts, stories_raw, sources_out, scoring, ROOT / "public" / "data", window_hours=window_h)
    report["sources_ok"] = ok
    report["sources_fail"] = fail
    report["success_rate"] = round(ok / (ok + fail), 4) if (ok + fail) else 0.0
    _write_run_log(report)
    return report


def _write_run_log(report: dict):
    log = ROOT / "pipeline" / "last_run.json"
    with open(log, "w", encoding="utf-8") as f:
        import json
        json.dump({"generatedAt": report.get("generatedAt"), **report}, f, ensure_ascii=False, indent=2)


def _focus_recent(item_objs: list, scoring: dict) -> list:
    """Keep the dataset focused on a recent window (task book §1: past 24h).

    - Limit each source to its N most recent entries.
    - Drop entries whose publishedAt is older than the ingest window,
      unless they have no publishedAt (treated as recent on first run).
    """
    import time as _t
    cfg = scoring.get("ingest", {})
    window_h = int(cfg.get("windowHours", 72))
    per_source = int(cfg.get("perSourceLimit", 20))
    now_unix = _t.time()
    cutoff = now_unix - window_h * 3600

    by_src = {}
    for it in item_objs:
        by_src.setdefault(it.sourceId, []).append(it)
    focused = []
    for src, group in by_src.items():
        group.sort(key=lambda x: iso_to_unix(x.publishedAt), reverse=True)
        group = group[:per_source]
        for it in group:
            pu = iso_to_unix(it.publishedAt)
            if pu and pu < cutoff:
                continue
            focused.append(it)
    return focused


def main():
    ap = argparse.ArgumentParser(description="AIhot pipeline")
    ap.add_argument("command", nargs="?", default="run", choices=["run", "notify"])
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--top", type=int, default=None, help="notify: how many top stories")
    args = ap.parse_args()
    if args.command == "notify":
        from .notify import notify
        rep = notify(args.top or 10)
        print("NOTIFY_DONE", rep)
        return
    try:
        rep = run_once(force=args.once)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"PIPELINE_ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    print("PIPELINE_OK", {
        "items": rep["items"], "stories": rep["stories"],
        "sources_ok": rep["sources_ok"], "sources_fail": rep["sources_fail"],
        "success_rate": rep["success_rate"], "generatedAt": rep["generatedAt"],
    })


if __name__ == "__main__":
    main()
