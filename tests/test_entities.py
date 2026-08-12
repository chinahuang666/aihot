"""Phase 2 tests: entity extraction coverage."""
from __future__ import annotations

from pipeline.entities import extract_entities, strong_entities


def test_version_extracted():
    e = extract_entities("vLLM v0.27.0 released")
    assert "ver:0.27.0" in e
    assert "prod:vllm" in e


def test_product_dict_match():
    e = extract_entities("OpenAI launches GPT-5")
    assert "prod:gpt-5" in e
    assert "org:openai" in e


def test_company_is_not_strong_signal():
    e = extract_entities("OpenAI hires new researcher")
    assert "org:openai" in e
    # 'openai' must NOT be a strong (prod:/ver:) merge signal on its own
    assert strong_entities(e) == set()


def test_generic_acronyms_excluded():
    e = extract_entities("New AI model improves LLM reasoning via API")
    assert "prod:ai" not in e
    assert "prod:llm" not in e
    assert "prod:api" not in e


def test_pascal_case_captured():
    e = extract_entities("LangChain adds new agent features")
    assert "prod:langchain" in e


def test_no_false_strong_on_generic_headline():
    e = extract_entities("The future of AI and machine learning")
    assert strong_entities(e) == set()
