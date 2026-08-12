"""Data models and schema version for AIhot.

All entities follow the data contract in the task book §7 (camelCase field names).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional
import hashlib
import json

SCHEMA_VERSION = "1.0.0"
ALGO_VERSION = "rule-1.0.0"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()


@dataclass
class Source:
    id: str
    name: str
    type: str
    role: str
    trustTier: int
    url: str
    category: str
    language: str
    pollMinutes: int = 30
    enabled: bool = True
    # runtime health
    lastSuccessAt: Optional[str] = None
    healthStatus: str = "unknown"   # ok | degraded | failed | unknown
    lastHttpStatus: Optional[int] = None
    lastItemCount: int = 0
    consecutiveFailures: int = 0
    lastError: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class Item:
    id: str
    sourceId: str
    externalId: str
    canonicalUrl: str
    titleOriginal: str
    titleZh: str
    excerpt: str
    author: str
    language: str
    publishedAt: Optional[str]
    discoveredAt: str
    contentHash: str
    category: str
    entities: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    sourceRole: str = ""
    trustTier: int = 1

    def to_dict(self):
        return asdict(self)


@dataclass
class Claim:
    text: str
    supportingItemIds: list


@dataclass
class Story:
    id: str
    slug: str
    headline: str
    whatHappened: str
    whyItMatters: str
    category: str
    entities: list
    firstSeenAt: str
    lastUpdatedAt: str
    status: str
    heatScore: float
    importanceScore: float
    confidenceScore: float
    rankingReasons: list
    itemIds: list
    primaryItemId: str
    claims: list
    summaryVersion: str
    headlineZh: str = ""

    def to_dict(self):
        return asdict(self)


def make_item_id(source_id: str, external_id: str) -> str:
    return _sha256(f"{source_id}|{external_id}")[:16]


def validate_story(story: Story) -> list:
    """Return list of problems (empty if ok)."""
    problems = []
    if not story.itemIds:
        problems.append("story has no itemIds")
    if not story.primaryItemId:
        problems.append("story missing primaryItemId")
    for claim in story.claims:
        for cid in claim.supportingItemIds:
            if cid not in story.itemIds:
                problems.append(f"claim evidence {cid} not in story.itemIds")
    return problems
