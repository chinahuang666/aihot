"""Reusable fixture builders for clustering / dedupe tests.

These build real ``pipeline.models.Item`` objects with entity extraction
applied (just like the live pipeline does), so tests exercise the same code
path that production uses.
"""
from __future__ import annotations

from pipeline.models import Item, make_item_id
from pipeline.entities import extract_entities
from pipeline.normalize import now_iso


def make_item(source_id: str, title: str, published_at: str, *, excerpt: str = "",
              url: str = None, category: str = "industry", role: str = "media",
              trust_tier: int = 1) -> Item:
    eid = make_item_id(source_id, title)
    return Item(
        id=eid,
        sourceId=source_id,
        externalId=title,
        canonicalUrl=url or f"https://example.com/{source_id}/{eid}",
        titleOriginal=title,
        titleZh=title,
        excerpt=excerpt,
        author="",
        language="en",
        publishedAt=published_at,
        discoveredAt=published_at,
        contentHash=make_item_id("body", title + excerpt),
        category=category,
        entities=extract_entities(title, excerpt),
        metrics={},
        sourceRole=role,
        trustTier=trust_tier,
    )


# --- Scenario builders -------------------------------------------------------

def duplicate_scenario():
    """Same event reported by two outlets (different wording)."""
    return [
        make_item("theverge", "OpenAI launches GPT-5", "2026-08-11T10:00:00Z",
                  excerpt="The company unveiled its most powerful model yet."),
        make_item("techcrunch", "GPT-5 released by OpenAI", "2026-08-11T11:30:00Z",
                  excerpt="OpenAI's newest flagship model is now available."),
    ]


def update_scenario():
    """Same product + same version, announcement plus follow-up."""
    return [
        make_item("github", "vLLM v0.27.0 released", "2026-08-11T09:00:00Z",
                  excerpt="High-throughput inference engine v0.27.0 is out.", role="primary"),
        make_item("qbitai", "vLLM 0.27.0 is now available", "2026-08-11T12:00:00Z",
                  excerpt="The v0.27.0 release brings performance improvements."),
    ]


def commentary_scenario():
    """Opinion/analysis piece about an event, plus the event itself."""
    return [
        make_item("openai", "Anthropic launches Claude 3.5 Opus", "2026-08-11T08:00:00Z",
                  excerpt="Anthropic debuts a new flagship model.", role="primary"),
        make_item("wired", "Why Claude 3.5 Opus changes the AI race", "2026-08-11T15:00:00Z",
                  excerpt="Analysts say the new model narrows the gap with rivals."),
    ]


def contradiction_scenario():
    """Two studies that disagree about the same product."""
    return [
        make_item("arxiv", "Study shows GPT-5 outperforms humans on reasoning",
                  "2026-08-11T07:00:00Z", excerpt="Benchmark results look strong."),
        make_item("techcrunch", "New study: GPT-5 fails basic reasoning tasks",
                  "2026-08-11T18:00:00Z", excerpt="A separate evaluation paints a weaker picture."),
    ]


def distinct_scenario():
    """Two unrelated products -> must NOT merge."""
    return [
        make_item("openai", "OpenAI launches GPT-5", "2026-08-11T10:00:00Z"),
        make_item("google", "Google releases Gemini 2.0", "2026-08-11T10:05:00Z"),
    ]


def stress_merge_scenario(n_events: int = 10):
    """Each event has 1 primary + 1 duplicate from another outlet -> n stories."""
    items = []
    products = [
        ("OpenAI", "GPT-5"), ("Google", "Gemini 2.0"), ("Anthropic", "Claude 3.5 Opus"),
        ("Meta", "Llama 3.1"), ("DeepSeek", "DeepSeek V3"), ("Mistral", "Mistral Large"),
        ("xAI", "Grok 3"), ("Alibaba", "Qwen2.5"), ("Microsoft", "Phi-4"),
        ("Stability", "Stable Diffusion 3.5"),
    ]
    for i, (org, prod) in enumerate(products[:n_events]):
        base = f"{org} releases {prod}"
        items.append(make_item(f"src_a{i}", base, f"2026-08-11T{10 + i:02d}:00:00Z",
                               role="primary"))
        items.append(make_item(f"src_b{i}", f"{prod} launched by {org}",
                               f"2026-08-11T{10 + i:02d}:30:00Z"))
    return items


# Genuinely distinct events: each has a unique product + unique phrasing, so
# neither shared entities nor high title overlap can wrongly merge them.
_DISTINCT_EVENTS = [
    ("OpenAI", "GPT-5", "unveiled a major reasoning upgrade for its flagship model"),
    ("Google", "Gemini 2.0", "shipped the new model to select cloud partners"),
    ("Anthropic", "Claude 3.5", "debuted a more capable enterprise assistant"),
    ("Meta", "Llama 3.1", "open-sourced a 405B parameter checkpoint"),
    ("DeepSeek", "V3", "released a 671B mixture-of-experts model"),
    ("Mistral", "Large", "launched a multilingual API endpoint"),
    ("xAI", "Grok 3", "announced real-time web search integration"),
    ("Alibaba", "Qwen2.5", "published new 3B and 72B weight releases"),
    ("Microsoft", "Phi-4", "introduced a compact reasoning model"),
    ("Stability", "SD3.5", "shipped higher-resolution image synthesis"),
    ("Cohere", "Command R", "expanded its 128K token context window"),
    ("NVIDIA", "Nemotron", "detailed a new post-training recipe"),
    ("Hugging Face", "SmolLM", "released tiny on-device language models"),
    ("Perplexity", "Sonar", "added grounded citation support"),
    ("Runway", "Gen-3", "expanded access to video generation"),
    ("ElevenLabs", "v3", "shipped expressive speech synthesis"),
    ("Replicate", "R2", "launched a hosted inference service"),
    ("Pika", "1.5", "improved physics in generated video clips"),
    ("Character.AI", "Avatar", "rolled out voice-based personas"),
    ("Inflection", "Pi-3", "returned with a refreshed assistant"),
]


def stress_distinct_scenario(n: int = 20):
    """N unrelated events -> N stories (no false merges)."""
    items = []
    for i, (org, prod, detail) in enumerate(_DISTINCT_EVENTS[:n]):
        title = f"{org} {detail} ({prod})"
        items.append(make_item(f"src_{i}", title, f"2026-08-11T{i % 24:02d}:00:00Z"))
    return items
