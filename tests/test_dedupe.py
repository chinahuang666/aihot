"""Phase 2 tests: near-duplicate detection logic."""
from __future__ import annotations

from pipeline.dedupe import is_near_duplicate, Deduplicator
from tests.fixtures.items import make_item


def _ent(title, excerpt="", source_id="s"):
    return make_item(source_id, title, "2026-08-11T10:00:00Z", excerpt=excerpt)


def test_exact_content_hash_merges():
    a = _ent("OpenAI launches GPT-5", "same body", source_id="a")
    b = _ent("Different headline", "same body", source_id="b")
    # force identical content hash
    b.contentHash = a.contentHash
    assert is_near_duplicate(a, b) is True


def test_shared_strong_entity_merges():
    a = _ent("OpenAI launches GPT-5", "flagship model", source_id="theverge")
    b = _ent("GPT-5 released by OpenAI", "new model out", source_id="techcrunch")
    assert is_near_duplicate(a, b) is True


def test_no_merge_without_shared_entity():
    a = _ent("OpenAI launches GPT-5", "flagship")
    b = _ent("Google releases Gemini 2.0", "new model")
    assert is_near_duplicate(a, b) is False


def test_title_only_high_jaccard_merges():
    a = _ent("Local bakery opens on Main Street", "fresh bread", source_id="n1")
    b = _ent("Local bakery opens on Main Street today", "fresh bread daily", source_id="n2")
    assert is_near_duplicate(a, b) is True


def test_low_jaccard_no_shared_entity_no_merge():
    a = _ent("Apple pie recipe", "cinnamon")
    b = _ent("Quantum computing breakthrough", "qubits")
    assert is_near_duplicate(a, b) is False


def test_time_window_excludes_old_items():
    a = _ent("OpenAI launches GPT-5", "flagship")
    b = _ent("GPT-5 released by OpenAI", "new model")
    # place b far in the past -> out of the 2-day window
    b.publishedAt = "2020-01-01T00:00:00Z"
    pairs = Deduplicator().near_duplicate_pairs([a, b])
    assert pairs == []


def test_same_source_distinct_releases_do_not_merge():
    """Regression: a repo's consecutive releases (templated titles, same source)
    must stay separate; only cross-source coverage should collapse."""
    a = _ent("vLLM Releases 发布 v0.27.0", "release notes", source_id="vllm_rel")
    b = _ent("vLLM Releases 发布 v0.27.1", "release notes", source_id="vllm_rel")
    assert is_near_duplicate(a, b) is False


def test_cross_source_same_release_merges():
    a = _ent("vLLM 发布 v0.27.0", "release", source_id="vllm_rel")
    b = _ent("vLLM v0.27.0 is now available", "out now", source_id="news_site")
    assert is_near_duplicate(a, b) is True
