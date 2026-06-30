from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from app.config import load_settings

from evals.models import GoldenCase
from evals.runner import evaluate_case, run_evaluation


def _case(case_id: str, *, expected_keywords: list[str] | None = None) -> GoldenCase:
    return GoldenCase(
        id=case_id,
        question="What does Prisma mean by provider boundaries?",
        expected_source_paths=["datasets/sample_corpus/provider-boundaries.md"],
        expected_keywords=expected_keywords or ["provider"],
        min_citations=1,
        expected_workflow_status="completed",
    )


def _response(answer: str = "Provider boundaries keep adapters isolated. [1]") -> dict[str, Any]:
    return {
        "answer": answer,
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


def test_evaluate_case_records_failure_reasons() -> None:
    result = evaluate_case(_case("keyword-miss", expected_keywords=["baseline"]), _response())

    assert result.passed is False
    assert result.failure_reasons
    assert result.failure_reasons[0].startswith("answer_contains_expected_terms:")


def test_runner_produces_scorecard_with_metric_counts() -> None:
    passing_case = _case("passing-case")
    failing_case = _case("failing-case", expected_keywords=["baseline"])

    scorecard = run_evaluation(
        settings=load_settings(),
        cases=[passing_case, failing_case],
        post_case=lambda case: _response(),
        ensure_index=False,
        write_scorecard_artifact=False,
    )

    assert scorecard.case_count == 2
    assert scorecard.aggregate.cases_passed == 1
    assert scorecard.aggregate.cases_failed == 1
    assert scorecard.aggregate.pass_rate == 0.5
    assert scorecard.metrics["answer_contains_expected_terms"].pass_count == 1
    assert scorecard.metrics["answer_contains_expected_terms"].fail == 1


def test_runner_writes_only_generated_scorecard_path(tmp_path: Path) -> None:
    settings = load_settings()
    baseline_before = settings.eval_baseline_path.read_text(encoding="utf-8")
    scorecard_path = tmp_path / ".local" / "prisma" / "evals" / "scorecard.json"
    test_settings = replace(
        settings,
        evals=replace(settings.evals, scorecard_path=str(scorecard_path)),
    )

    run_evaluation(
        settings=test_settings,
        cases=[_case("passing-case")],
        post_case=lambda case: _response(),
        ensure_index=False,
        write_scorecard_artifact=True,
    )

    assert scorecard_path.exists()
    assert json.loads(scorecard_path.read_text(encoding="utf-8"))["case_count"] == 1
    assert settings.eval_baseline_path.read_text(encoding="utf-8") == baseline_before
