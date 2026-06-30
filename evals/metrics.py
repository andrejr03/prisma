"""Deterministic Phase 4 evaluation metrics."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Any, cast

from app.models.rag import ErrorResponse, QueryResponse
from pydantic import ValidationError

from evals.models import GoldenCase, MetricResult

MetricFunction = Callable[[Mapping[str, Any], GoldenCase], MetricResult]

_CITATION_MARKER_RE = re.compile(r"\[(\d+)]")


def retrieval_source_hit(response: Mapping[str, Any], case: GoldenCase) -> MetricResult:
    """Check whether retrieved context includes every expected source path."""

    if case.expects_no_context:
        return _not_applicable("no-context cases do not require retrieved sources")

    retrieved_context = _object_list(response, "retrieved_context")
    if retrieved_context is None:
        return _fail("retrieved_context is missing or malformed")

    actual_paths = _source_paths(retrieved_context)
    missing = sorted(path for path in case.expected_source_paths if path not in actual_paths)
    if missing:
        return _fail(
            f"missing expected retrieved source path(s): {', '.join(missing)}",
            missing_paths=missing,
        )
    return _pass()


def citation_source_hit(response: Mapping[str, Any], case: GoldenCase) -> MetricResult:
    """Check whether citations include every expected source path."""

    if case.expects_no_context:
        return _not_applicable("no-context cases do not require cited sources")

    citations = _object_list(response, "citations")
    if citations is None:
        return _fail("citations is missing or malformed")

    actual_paths = _source_paths(citations)
    missing = sorted(path for path in case.expected_source_paths if path not in actual_paths)
    if missing:
        return _fail(
            f"missing expected cited source path(s): {', '.join(missing)}",
            missing_paths=missing,
        )
    return _pass()


def citation_validity(response: Mapping[str, Any], case: GoldenCase) -> MetricResult:
    """Check that citations are well formed and grounded in retrieved context."""

    if case.expects_no_context:
        return _not_applicable("no-context cases do not require citations")

    citations = _object_list(response, "citations")
    retrieved_context = _object_list(response, "retrieved_context")
    if citations is None:
        return _fail("citations is missing or malformed")
    if retrieved_context is None:
        return _fail("retrieved_context is missing or malformed")
    if not citations:
        return _fail("response contains no citations")

    retrieved_ids = _citation_ids(retrieved_context)
    for citation in citations:
        missing_fields = [
            field
            for field in (
                "citation_id",
                "source_document",
                "source_path",
                "chunk_id",
                "chunk_index",
                "score",
            )
            if field not in citation or citation[field] is None
        ]
        if missing_fields:
            return _fail(
                f"citation is missing required field(s): {', '.join(missing_fields)}",
                missing_fields=missing_fields,
            )

        citation_id = citation.get("citation_id")
        if type(citation_id) is not int:
            return _fail("citation_id must be an integer")
        if citation_id not in retrieved_ids:
            return _fail(f"citation_id {citation_id} is not present in retrieved_context")

    return _pass()


def answer_contains_expected_terms(response: Mapping[str, Any], case: GoldenCase) -> MetricResult:
    """Check whether the answer contains every expected keyword."""

    if case.expects_no_context:
        return _not_applicable("no-context cases do not require answer keywords")

    answer = response.get("answer")
    if not isinstance(answer, str):
        return _fail("answer is missing or not a string")

    normalized_answer = answer.lower()
    missing = sorted(
        keyword for keyword in case.expected_keywords if keyword not in normalized_answer
    )
    if missing:
        return _fail(
            f"missing expected answer term(s): {', '.join(missing)}",
            missing_terms=missing,
        )
    return _pass()


def no_unsupported_citations(response: Mapping[str, Any], case: GoldenCase) -> MetricResult:
    """Check that citations and answer markers reference retrieved context only."""

    if case.expects_no_context:
        return _not_applicable("no-context cases do not require citation markers")

    citations = _object_list(response, "citations")
    retrieved_context = _object_list(response, "retrieved_context")
    if citations is None:
        return _fail("citations is missing or malformed")
    if retrieved_context is None:
        return _fail("retrieved_context is missing or malformed")

    citation_ids = _citation_ids(citations)
    retrieved_ids = _citation_ids(retrieved_context)
    unsupported_citations = sorted(str(citation_id) for citation_id in citation_ids - retrieved_ids)
    if unsupported_citations:
        return _fail(
            "citation_id(s) are absent from retrieved_context: " + ", ".join(unsupported_citations),
            unsupported_citations=unsupported_citations,
        )

    answer = response.get("answer")
    if not isinstance(answer, str):
        return _fail("answer is missing or not a string")

    marker_ids = {int(value) for value in _CITATION_MARKER_RE.findall(answer)}
    unsupported_markers = sorted(str(marker_id) for marker_id in marker_ids - citation_ids)
    if unsupported_markers:
        return _fail(
            "answer citation marker(s) are absent from citations: "
            + ", ".join(unsupported_markers),
            unsupported_markers=unsupported_markers,
        )

    return _pass()


def workflow_completed(response: Mapping[str, Any], case: GoldenCase) -> MetricResult:
    """Check whether the workflow reached the expected terminal status."""

    expected_status = case.expected_workflow_status
    if case.expects_no_context:
        expected_status = expected_status or "no_context"
        actual_error = _error_code(response)
        if actual_error == expected_status:
            return _pass()
        return _fail(f"expected no-context error code '{expected_status}', got '{actual_error}'")

    expected_status = expected_status or "completed"
    workflow = _mapping_value(response, "workflow")
    if workflow is None:
        return _fail("workflow is missing or malformed")

    actual_status = workflow.get("status")
    if actual_status == expected_status:
        return _pass()
    return _fail(f"expected workflow status '{expected_status}', got '{actual_status}'")


def workflow_retry_bounded(response: Mapping[str, Any], case: GoldenCase) -> MetricResult:
    """Check that retrieval attempts stayed within the Phase 3 bound."""

    if case.expects_no_context:
        return _not_applicable("no-context error responses do not expose workflow retry metadata")

    workflow = _mapping_value(response, "workflow")
    if workflow is None:
        return _fail("workflow is missing or malformed")

    retrieval_attempts = workflow.get("retrieval_attempts")
    max_retrieval_attempts = workflow.get("max_retrieval_attempts")
    if type(retrieval_attempts) is not int or type(max_retrieval_attempts) is not int:
        return _fail("workflow retry fields must be integers")
    if max_retrieval_attempts != 2:
        return _fail(f"expected max_retrieval_attempts to equal 2, got {max_retrieval_attempts}")
    if not 1 <= retrieval_attempts <= max_retrieval_attempts:
        return _fail(
            "retrieval_attempts must be between 1 and max_retrieval_attempts, "
            f"got {retrieval_attempts}"
        )
    return _pass()


def structured_response_validity(response: Mapping[str, Any], case: GoldenCase) -> MetricResult:
    """Validate the response against the public API response schema."""

    if case.expects_no_context:
        try:
            error_response = ErrorResponse.model_validate(response)
        except ValidationError as exc:
            return _fail(f"response does not validate as ErrorResponse: {exc.errors()[0]['msg']}")
        if error_response.error.code != "no_context":
            return _fail(f"expected error code 'no_context', got '{error_response.error.code}'")
        return _pass()

    if _error_code(response) is not None:
        return _fail(f"expected QueryResponse but received error code '{_error_code(response)}'")

    try:
        query_response = QueryResponse.model_validate(response)
    except ValidationError as exc:
        return _fail(f"response does not validate as QueryResponse: {exc.errors()[0]['msg']}")

    citation_count = len(query_response.citations)
    if citation_count < case.min_citations:
        return _fail(
            f"expected at least {case.min_citations} citation(s), got {citation_count}",
            citation_count=citation_count,
        )
    return _pass()


METRIC_FUNCTIONS: tuple[tuple[str, MetricFunction], ...] = (
    ("retrieval_source_hit", retrieval_source_hit),
    ("citation_source_hit", citation_source_hit),
    ("citation_validity", citation_validity),
    ("answer_contains_expected_terms", answer_contains_expected_terms),
    ("no_unsupported_citations", no_unsupported_citations),
    ("workflow_completed", workflow_completed),
    ("workflow_retry_bounded", workflow_retry_bounded),
    ("structured_response_validity", structured_response_validity),
)


def _pass() -> MetricResult:
    return MetricResult(status="pass")


def _fail(
    reason: str,
    **details: int | float | str | bool | list[str],
) -> MetricResult:
    return MetricResult(status="fail", reason=reason, details=details)


def _not_applicable(reason: str) -> MetricResult:
    return MetricResult(status="not_applicable", reason=reason)


def _object_list(response: Mapping[str, Any], key: str) -> list[Mapping[str, Any]] | None:
    value = response.get(key)
    if not isinstance(value, list):
        return None
    if not all(isinstance(item, Mapping) for item in value):
        return None
    return [cast(Mapping[str, Any], item) for item in value]


def _mapping_value(response: Mapping[str, Any], key: str) -> Mapping[str, Any] | None:
    value = response.get(key)
    if not isinstance(value, Mapping):
        return None
    return cast(Mapping[str, Any], value)


def _source_paths(items: list[Mapping[str, Any]]) -> set[str]:
    paths: set[str] = set()
    for item in items:
        source_path = item.get("source_path")
        if isinstance(source_path, str):
            paths.add(source_path)
    return paths


def _citation_ids(items: list[Mapping[str, Any]]) -> set[int]:
    ids: set[int] = set()
    for item in items:
        citation_id = item.get("citation_id")
        if type(citation_id) is int:
            ids.add(citation_id)
    return ids


def _error_code(response: Mapping[str, Any]) -> str | None:
    error = _mapping_value(response, "error")
    if error is None:
        return None
    code = error.get("code")
    return code if isinstance(code, str) else None
