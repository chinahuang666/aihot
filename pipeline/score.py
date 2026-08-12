"""Scoring: Heat / Importance / Confidence (task book §9).

Each score is computed independently from explicit sub-signals. Weights are
readable config (config/scoring.yaml) with an algorithm version. Time decay
uses category-specific half-lives. All signals are normalized to [0,1].
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from .normalize import iso_to_unix

# half-life hours per category (news/tools decay faster than research/papers)
HALF_LIFE_H = {
    "model": 18, "product": 18, "developer": 30,
    "research": 72, "industry": 36, "safety": 48,
}


def _norm(x, lo=0.0, hi=1.0):
    if hi == lo:
        return 0.0
    return max(0.0, min(1.0, (x - lo) / (hi - lo)))


def _freshness(pub_iso, now_unix, half_life_h):
    pu = iso_to_unix(pub_iso)
    if not pu:
        return 0.5
    age_h = max(0.0, (now_unix - pu) / 3600.0)
    return 0.5 ** (age_h / max(1.0, half_life_h))


def _spread_velocity(story, now_unix):
    """Heuristic: how fast independent sources appeared after first seen."""
    unix_times = [iso_to_unix(t) for t in story["item_times"] if t]
    if len(unix_times) < 2:
        return 0.3
    span_h = (max(unix_times) - min(unix_times)) / 3600.0
    # faster accumulation => higher velocity
    if span_h <= 0.1:
        return 1.0
    return _norm(1.0 / (span_h / 24.0 + 0.01), 0, 1)


def compute_scores(story, sources_by_id: dict, now_unix: float, weights: dict) -> dict:
    n_sources = len(story["independentSources"])
    roles = story["roles"]
    tiers = story["trustTiers"]
    primary_firsthand = story["primaryRole"] == "primary"
    category = story["category"]

    # --- Heat ---
    velocity = _spread_velocity(story, now_unix)
    coverage = _norm(n_sources, 1, 6)            # 6+ independent sources -> full
    interaction = _norm(story["totalEngagement"], 0, 500)
    fresh = _freshness(story["firstSeenAt"], now_unix, HALF_LIFE_H.get(category, 36))
    heat = (weights["heat"]["velocity"] * velocity +
            weights["heat"]["coverage"] * coverage +
            weights["heat"]["interaction"] * interaction +
            weights["heat"]["freshness"] * fresh)

    # --- Importance ---
    industry_impact = _norm(n_sources, 1, 5) * 0.6 + (0.4 if category in ("model", "safety") else 0.2)
    originality = 1.0 if primary_firsthand else 0.4
    authority = _norm(sum(tiers) / max(1, len(tiers)), 1, 3)
    endurance = 0.5 + 0.5 * coverage
    importance = (weights["importance"]["industryImpact"] * min(1, industry_impact) +
                  weights["importance"]["originality"] * originality +
                  weights["importance"]["authority"] * authority +
                  weights["importance"]["endurance"] * endurance)

    # --- Confidence ---
    firsthand = 1.0 if primary_firsthand else 0.3
    cross_confirm = _norm(n_sources, 1, 4)        # >=4 independent => strong
    hist_quality = _norm(sum(tiers) / max(1, len(tiers)), 1, 3)
    meta_complete = 1.0 if (story["primaryPublished"] and story["primaryUrl"]) else 0.5
    penalty = 0.0
    if story["hasContradiction"]:
        penalty += 0.2
    if n_sources <= 1:
        penalty += 0.15   # single repost chain
    confidence = (weights["confidence"]["firsthand"] * firsthand +
                  weights["confidence"]["crossConfirm"] * cross_confirm +
                  weights["confidence"]["histQuality"] * hist_quality +
                  weights["confidence"]["metaComplete"] * meta_complete - penalty)
    confidence = max(0.0, min(1.0, confidence))

    reasons = build_reasons(story, heat, importance, confidence, n_sources)
    return {
        "heat": round(heat, 4),
        "importance": round(importance, 4),
        "confidence": round(confidence, 4),
        "reasons": reasons,
    }


def build_reasons(story, heat, importance, confidence, n_sources) -> list:
    r = []
    if n_sources >= 2:
        r.append(f"{n_sources} 小时内出现 {n_sources} 个独立来源")
    if story["primaryRole"] == "primary":
        r.append("包含官方/一手来源")
    if story["hasRelease"]:
        r.append("包含 GitHub Release / 官方发布")
    if story["hasContradiction"]:
        r.append("来源说法存在不一致，已标记")
    if confidence >= 0.7:
        r.append("多源交叉确认，可信度较高")
    elif confidence < 0.5:
        r.append("目前以单一来源为主，可信度待提升")
    if importance >= 0.7:
        r.append("潜在行业影响较大")
    return r[:5]
