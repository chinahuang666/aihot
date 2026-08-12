"""Phase 2 tests: event clustering quality.

Acceptance (task book §14):
  * duplicate reports of the same event become ONE story with expandable sources
  * distinct events stay separate (duplicate/over-merge rate < 5%)
"""
from __future__ import annotations

from pipeline.cluster import Clusterer
from tests.fixtures.items import (
    duplicate_scenario, update_scenario, commentary_scenario,
    contradiction_scenario, distinct_scenario,
    stress_merge_scenario, stress_distinct_scenario,
)


def _cluster(items):
    return Clusterer({}).cluster(items)


def test_duplicate_merges_to_one_story():
    stories = _cluster(duplicate_scenario())
    assert len(stories) == 1
    s = stories[0]
    assert len(s.itemIds) == 2
    src_ids = {it.sourceId for it in duplicate_scenario()}
    assert len({i for i in s.itemIds}) == 2  # two distinct source items


def test_update_merges_same_release():
    stories = _cluster(update_scenario())
    assert len(stories) == 1
    assert len(stories[0].itemIds) == 2


def test_commentary_links_to_event():
    stories = _cluster(commentary_scenario())
    assert len(stories) == 1
    assert len(stories[0].itemIds) == 2


def test_contradiction_stays_one_event():
    stories = _cluster(contradiction_scenario())
    assert len(stories) == 1
    assert len(stories[0].itemIds) == 2


def test_distinct_events_stay_separate():
    stories = _cluster(distinct_scenario())
    assert len(stories) == 2


def test_stress_merge_exact():
    n = 10
    items = stress_merge_scenario(n)
    stories = _cluster(items)
    # every event's 2 reports collapse; no distinct events wrongly merge
    assert len(stories) == n
    for s in stories:
        assert len(s.itemIds) == 2


def test_stress_distinct_no_false_merge():
    n = 20
    items = stress_distinct_scenario(n)
    stories = _cluster(items)
    assert len(stories) == n  # duplicate/over-merge rate == 0%


def test_duplicate_rate_below_threshold():
    """Over-merge rate must stay under 5% on the merge stress set."""
    n = 10
    items = stress_merge_scenario(n)
    stories = _cluster(items)
    over_merge = max(0, n - len(stories)) / n
    assert over_merge < 0.05


def test_story_sources_are_expandable():
    """Each merged story must carry independent source ids for the UI."""
    stories = _cluster(duplicate_scenario())
    s = stories[0]
    srcs = set()
    for it in duplicate_scenario():
        if it.id in s.itemIds:
            srcs.add(it.sourceId)
    assert len(srcs) == 2
