"""Deterministic entity extraction for event clustering (task book §8).

Clustering across outlets is hard because headlines are phrased differently.
This module extracts lightweight, model-free *strong signals* so that two
articles about the same product/release/version merge even when their titles
barely overlap:

    "OpenAI launches GPT-5"   vs   "GPT-5 is here, says OpenAI"
    "vLLM v0.27.0 released"   vs   "vLLM 0.27.0 is now available"

Entity format: "<kind>:<value>" where kind is one of:
    ver  : version string, e.g. "0.27.0"  (very specific -> strong merge signal)
    prod : specific AI product / model / library token, e.g. "gpt-5", "vllm"
    org  : company name (informational only, NOT a strong merge signal by itself)

Only `ver:` and `prod:` entities are treated as *strong* by the clusterer;
`org:` is kept for display/evidence but never drives a merge on its own, which
prevents the "everything about OpenAI collapses into one story" failure mode.
"""
from __future__ import annotations

import re

# Curated dictionary of specific AI products / models / libraries.
# Company names alone are intentionally excluded here (kept in ORGS below).
PRODUCTS = {
    # OpenAI
    "gpt-5", "gpt-4", "gpt-4o", "gpt-4.5", "gpt-3.5", "gpt", "chatgpt",
    "dall-e", "dall·e", "sora", "whisper", "o1", "o3", "o4",
    # Anthropic
    "claude", "claude-3", "claude-3.5", "claude-opus", "claude-sonnet",
    "claude-haiku",
    # Google
    "gemini", "gemini-1.5", "gemini-2.0", "gemini-2.5", "gemma", "palm",
    "project astra", "veo", "imagen",
    # Meta
    "llama", "llama-2", "llama-3", "llama-3.1", "llama-3.2", "llama-3.3",
    "segment anything", "sam",
    # DeepSeek
    "deepseek", "deepseek-v3", "deepseek-v2", "deepseek-r1",
    # Alibaba
    "qwen", "qwen2", "qwen2.5", "qwen3",
    # Mistral
    "mistral", "mixtral", "codestral", "magistral",
    # xAI
    "grok", "grok-3", "grok-2",
    # Microsoft
    "copilot", "phi-3", "phi-3.5", "phi-4", "phi",
    # Others / open models & libs
    "vllm", "ollama", "llamacpp", "llama.cpp", "llamaindex", "transformers",
    "langchain", "langgraph", "autogen", "crewai", "stable-diffusion", "sd3",
    "sd3.5", "flux", "midjourney", "nemotron", "command-r", "command-r-plus",
    "embedding", "reranker", "rerank", "bert", "t5", "llama3", "qwen2.5",
    "deepseek-r1", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
}

# Company names. Informational only (org:); never a standalone merge signal.
ORGS = {
    "openai", "anthropic", "google", "meta", "microsoft", "nvidia", "xai",
    "deepmind", "mistral ai", "cohere", "hugging face", "stability ai",
    "baidu", "alibaba", "tencent", "apple", "amazon", "databricks",
    "salesforce", "ibm", "intel", "amd", "github", "gitlab",
}

# Generic acronyms that appear in nearly every AI headline. Treating them as
# strong merge signals would collapse unrelated stories, so they are ignored.
GENERIC_ACRONYMS = {
    "AI", "ML", "DL", "API", "UI", "UX", "OS", "IT", "AGI", "GPU", "CPU",
    "TPU", "NLP", "CV", "RL", "SQL", "SDK", "CLI", "URL", "HTTP", "JSON",
    "XML", "ID", "OK", "VS", "IO", "LLM", "RAG", "EM", "ANN", "HN",
    "QA", "DB", "JS", "TS", "PY", "GO", "C", "CI", "CD", "PR",
}

# version like 0.27.0 / v1.2 / 2.0.1 (optionally leading v)
VERSION_RE = re.compile(r"\b(v?\d+\.\d+(?:\.\d+)?)\b", re.I)

# NOTE: We deliberately do NOT infer products from arbitrary capitalized words
# (PascalCase / acronyms). Doing so created false "strong" merge signals and
# collapsed unrelated stories. The curated PRODUCTS dictionary + VERSION regex
# below is the precise, safe signal set for the MVP.


def _normalize_version(v: str) -> str:
    return v.lower().lstrip("v")


def extract_entities(title: str, excerpt: str = "") -> list:
    """Return a sorted list of "<kind>:<value>" entity strings."""
    text = f"{title or ''} {excerpt or ''}"
    low = text.lower()
    found: dict = {}

    # 1) version strings -> ver:
    for m in VERSION_RE.findall(text):
        found[f"ver:{_normalize_version(m)}"] = True

    # 2) curated products -> prod: (substring match, case-insensitive).
    #    Normalize hyphens to spaces so "stable-diffusion" matches the spaced
    #    "stable diffusion" that appears in real headlines.
    norm = low.replace("-", " ")
    for p in PRODUCTS:
        if p.replace("-", " ") in norm:
            found[f"prod:{p}"] = True

    # 3) companies / platforms -> org: (informational only; not a merge signal)
    for o in ORGS:
        if o in low:
            found[f"org:{o}"] = True

    return sorted(found.keys())


def strong_entities(entity_list) -> set:
    """Return only the merge-driving entities (ver: and prod:)."""
    return {e for e in (entity_list or []) if e.startswith(("ver:", "prod:"))}
