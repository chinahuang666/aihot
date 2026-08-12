"""Rule-based summarization and pluggable LLM interface (task book §10).

Default behavior: rule-based summary, no LLM. LLM is only invoked when an API
key + budget are explicitly configured (budget default 0 => disabled).
Every claim carries supporting_item_ids; claims without evidence are dropped.
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Optional

MAX_EXCERPT = 280


def _clip(text: str, n: int = MAX_EXCERPT) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:n] + ("…" if len(text) > n else "")


def rule_summary(group: list, primary) -> dict:
    """Deterministic, model-free summary. Returns structured dict."""
    title = primary.titleOriginal or primary.titleZh or "未命名事件"
    excerpt = primary.excerpt or ""
    # what happened = primary title (the core fact) + short excerpt if available
    what = title if len(title) <= 60 else title[:60] + "…"
    why = _clip(excerpt, 120) if excerpt else "来源已发布相关信息，需关注后续进展。"
    # claims: each backed by an item id
    claims = []
    # primary claim from the headline
    claims.append({
        "text": _clip(title, 200),
        "supporting_item_ids": [primary.id],
    })
    # add one claim per distinct extra source (evidence strengthening)
    seen = {primary.id}
    for it in group[1:]:
        if it.id in seen:
            continue
        seen.add(it.id)
        if it.excerpt:
            claims.append({
                "text": _clip(it.excerpt, 200),
                "supporting_item_ids": [it.id],
            })
    return {
        "headline": title,
        "headline_zh": title,
        "whatHappened": what,
        "whyItMatters": why,
        "claims": claims,
        "uncertainties": [],
        "entities": primary.entities,
        "is_ai": False,
    }


def llm_summary(group: list, primary, provider=None) -> Optional[dict]:
    """Placeholder for pluggable LLM. Disabled unless configured.

    Returns None to signal 'use rule_summary'. When enabled, the provider must
    return the strict schema and we validate claims have evidence.
    """
    api_key = os.environ.get("AIHOT_LLM_API_KEY")
    budget = float(os.environ.get("AIHOT_LLM_BUDGET", "0") or "0")
    if not api_key or budget <= 0:
        return None
    # Provider integration point. On any failure return None (rule fallback).
    return None
