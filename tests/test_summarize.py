"""Phase 3 tests: rule-based summary + graceful LLM fallback.

Per the plan, the MVP uses rule-based summarization only. The LLM path is a
placeholder that must ALWAYS fall back to the rule summary when no key/budget
is configured (and on any failure). These tests lock that contract.
"""
from __future__ import annotations

import os
from pipeline.summarize import rule_summary, llm_summary
from pipeline.models import Item, make_item_id


def _item(title, excerpt=""):
    return Item(
        id=make_item_id("s", title), sourceId="s", externalId=title,
        canonicalUrl="https://example.com/x", titleOriginal=title, titleZh=title,
        excerpt=excerpt, author="", language="en", publishedAt=None,
        discoveredAt="", contentHash="", category="industry",
        entities=[], metrics={}, sourceRole="media", trustTier=1,
    )


def test_rule_summary_has_claims_with_evidence():
    it = _item("OpenAI launches GPT-5", "A new flagship model.")
    group = [it]
    s = rule_summary(group, it)
    assert s["headline"]
    assert len(s["claims"]) >= 1
    # every claim must carry the supporting item id
    for c in s["claims"]:
        assert c["supporting_item_ids"]


def test_llm_disabled_without_key_returns_none():
    os.environ.pop("AIHOT_LLM_API_KEY", None)
    os.environ["AIHOT_LLM_BUDGET"] = "0"
    assert llm_summary([_item("x")], _item("x")) is None


def test_llm_disabled_with_zero_budget_returns_none():
    os.environ["AIHOT_LLM_API_KEY"] = "sk-test"
    os.environ["AIHOT_LLM_BUDGET"] = "0"
    assert llm_summary([_item("x")], _item("x")) is None
