from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from evals.metrics import (
    answer_contains_expected_terms,
    citation_source_hit,
    citation_validity,
    no_unsupported_citations,
    retrieval_source_hit,
    structured_response_validity,
    workflow_completed,
    workflow_retry_bounded,
)
from evals.models import GoldenCase


def _answer_case() -> GoldenCase:
    return GoldenCase(
        id="provider-boundaries-basic",
        question="What does Prisma mean by provider boundaries?",
        expected_source_paths=["datasets/sample_corpus/provider-boundaries.md"],
        expected_keywords=["provider", "adapter"],
        min_citations=1,
        expected_workflow_status="completed",
    )


def _no_context_case() -> GoldenCase:
    return GoldenCase(
        id="out-of-corpus-no-context",
        question="What is outside the corpus?",
        expected_source_paths=[],
        expected_keywords=[],
        min_citations=0,
        expected_workflow_status="no_context",
        expects_no_context=True,
    )


def _response() -> dict[str, Any]:
    return {
        "answer": "Provider boundaries keep adapters isolated. [1]",
        "citations": [
            {
                "citation_id": 1,
                "source_document": "Provider Boundaries",
                "source_path": "datasets/sample_corpus/provider-boundaries.md",
                "chunk_id": "chunk-1",
                "chunk_index": 0,
                "score": 0.99,
            }
        ],
        "retrieved_context": [
            {
                "citation_id": 1,
                "chunk_id": "chunk-1",
                "source_document": "Provider Boundaries",
                "source_path": "datasets/sample_corpus/provider-boundaries.md",
                "chunk_index": 0,
                "score": 0.99,
                "text": "Provider boundaries keep adapters isolated.",
                "truncated": False,
            }
        ],
        "metadata": {
            "retrieval_top_k": 4,
            "context_item_count": 1,
            "generation_backend": "local-grounded",
            "generation_model_id": "local-grounded-v1",
        },
        "workflow": {
            "status": "completed",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 2,
            "route": ["validate_query", "finalize_response"],
            "rewritten_query": None,
            "context_sufficient": True,
        },
    }


def _no_context_response() -> dict[str, Any]:
    return {
        "error": {
            "code": "no_context",
            "message": "No sufficient context was retrieved for the question.",
            "details": {},
        }
    }


def test_source_keyword_and_citation_metrics_pass() -> None:
    case = _answer_case()
    response = _response()

    assert retrieval_source_hit(response, case).status == "pass"
    assert citation_source_hit(response, case).status == "pass"
    assert citation_validity(response, case).status == "pass"
    assert answer_contains_expected_terms(response, case).status == "pass"
    assert no_unsupported_citations(response, case).status == "pass"


def test_source_keyword_and_citation_metrics_fail_with_reasons() -> None:
    case = _answer_case()

    missing_retrieval = _response()
    missing_retrieval["retrieved_context"] = []
    assert retrieval_source_hit(missing_retrieval, case).status == "fail"

    missing_citation_source = _response()
    missing_citation_source["citations"] = [
        {
            **missing_citation_source["citations"][0],
            "source_path": "datasets/sample_corpus/retrieval-pipeline.md",
        }
    ]
    assert citation_source_hit(missing_citation_source, case).status == "fail"

    invalid_citation = _response()
    invalid_citation["citations"] = [
        {
            **invalid_citation["citations"][0],
            "citation_id": 2,
        }
    ]
    assert citation_validity(invalid_citation, case).status == "fail"

    missing_keyword = _response()
    missing_keyword["answer"] = "Provider boundaries keep modules isolated. [1]"
    assert answer_contains_expected_terms(missing_keyword, case).status == "fail"

    unsupported_marker = _response()
    unsupported_marker["answer"] = "Provider boundaries keep adapters isolated. [2]"
    assert no_unsupported_citations(unsupported_marker, case).status == "fail"


def test_no_context_makes_source_citation_keyword_metrics_not_applicable() -> None:
    case = _no_context_case()
    response = _no_context_response()
    metrics = [
        retrieval_source_hit,
        citation_source_hit,
        citation_validity,
        answer_contains_expected_terms,
        no_unsupported_citations,
        workflow_retry_bounded,
    ]

    for metric in metrics:
        assert metric(response, case).status == "not_applicable"


def test_workflow_completed_passes_for_answer_and_no_context() -> None:
    assert workflow_completed(_response(), _answer_case()).status == "pass"
    assert workflow_completed(_no_context_response(), _no_context_case()).status == "pass"


def test_workflow_completed_fails_on_wrong_status() -> None:
    response = _response()
    workflow = _copy_mapping(response["workflow"])
    workflow["status"] = "no_context"
    response["workflow"] = workflow

    result = workflow_completed(response, _answer_case())

    assert result.status == "fail"
    assert "expected workflow status" in (result.reason or "")


def test_workflow_retry_bounded_passes_and_fails() -> None:
    assert workflow_retry_bounded(_response(), _answer_case()).status == "pass"

    response = _response()
    workflow = _copy_mapping(response["workflow"])
    workflow["retrieval_attempts"] = 3
    response["workflow"] = workflow

    assert workflow_retry_bounded(response, _answer_case()).status == "fail"


def test_structured_response_validity_passes_for_success_and_no_context() -> None:
    assert structured_response_validity(_response(), _answer_case()).status == "pass"
    assert structured_response_validity(_no_context_response(), _no_context_case()).status == "pass"


def test_structured_response_validity_fails_for_too_few_citations() -> None:
    response = _response()
    response["citations"] = []

    result = structured_response_validity(response, _answer_case())

    assert result.status == "fail"
    assert "expected at least 1 citation" in (result.reason or "")


def _copy_mapping(value: object) -> dict[str, Any]:
    assert isinstance(value, Mapping)
    return dict(value)
