from __future__ import annotations

from app.generation.context import ContextItem
from app.providers.generation import GenerationRequest, LocalGroundedGenerationProvider


def test_local_grounded_generation_is_deterministic():
    provider = LocalGroundedGenerationProvider(model_id="local-grounded-v1")
    request = GenerationRequest(
        question="What are provider boundaries?",
        prompt="Answer from context.",
        context="",
        context_items=[
            _item(
                1,
                "Provider boundaries keep Prisma from hardcoding one model service.",
            )
        ],
        max_answer_sentences=3,
    )

    first = provider.generate(request)
    second = provider.generate(request)

    assert first == second
    assert first.answer.endswith("[1]")
    assert first.cited_context_ids == [1]


def test_local_grounded_generation_cites_only_supplied_context_ids():
    provider = LocalGroundedGenerationProvider(model_id="local-grounded-v1")

    result = provider.generate(
        GenerationRequest(
            question="What protects tests?",
            prompt="Answer from context.",
            context="",
            context_items=[_item(7, "Provider boundaries also protect tests.")],
            max_answer_sentences=3,
        )
    )

    assert result.cited_context_ids == [7]
    assert "[7]" in result.answer
    assert "[1]" not in result.answer


def _item(citation_id: int, text: str) -> ContextItem:
    return ContextItem(
        citation_id=citation_id,
        chunk_id=f"chunk-{citation_id}",
        source_document="Provider Boundaries",
        source_path="datasets/sample_corpus/provider-boundaries.md",
        chunk_index=0,
        score=0.9,
        text=text,
        truncated=False,
    )
