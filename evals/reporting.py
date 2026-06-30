"""Scorecard assembly and reporting for Prisma evals."""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from evals.models import AggregateResult, CaseResult, MetricCounts, Scorecard


def build_scorecard(
    *,
    case_results: list[CaseResult],
    metric_names: Iterable[str],
    index_fingerprint: str | None,
    minimum_pass_rate: float,
) -> Scorecard:
    """Build a structured scorecard from per-case results."""

    timestamp = datetime.now(UTC).replace(microsecond=0)
    metric_counts = _metric_counts(case_results, metric_names)
    cases_passed = sum(1 for result in case_results if result.passed)
    cases_failed = len(case_results) - cases_passed
    pass_rate = cases_passed / len(case_results) if case_results else 0.0

    return Scorecard(
        run_id=_run_id(timestamp),
        timestamp=timestamp.isoformat().replace("+00:00", "Z"),
        index_fingerprint=index_fingerprint,
        case_count=len(case_results),
        metrics=metric_counts,
        cases=case_results,
        aggregate=AggregateResult(
            cases_passed=cases_passed,
            cases_failed=cases_failed,
            pass_rate=pass_rate,
            minimum_pass_rate=minimum_pass_rate,
            meets_minimum=pass_rate >= minimum_pass_rate,
        ),
    )


def write_scorecard(path: Path, scorecard: Scorecard) -> None:
    """Write a scorecard JSON artifact to the configured generated path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = scorecard.model_dump(mode="json", by_alias=True, exclude_none=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def render_summary(scorecard: Scorecard, *, scorecard_path: Path) -> str:
    """Render a concise human-readable console summary."""

    aggregate = scorecard.aggregate
    lines = [
        "Prisma evaluation complete",
        (
            f"Cases: {aggregate.cases_passed}/{scorecard.case_count} passed "
            f"({aggregate.pass_rate:.1%})"
        ),
        (
            f"Minimum pass rate: {aggregate.minimum_pass_rate:.1%} "
            f"({'met' if aggregate.meets_minimum else 'not met'})"
        ),
        f"Scorecard: {scorecard_path.as_posix()}",
    ]

    failed_cases = [case for case in scorecard.cases if not case.passed]
    if failed_cases:
        lines.append("Failures:")
        lines.extend(f"- {case.id}: {'; '.join(case.failure_reasons)}" for case in failed_cases)

    return "\n".join(lines)


def _metric_counts(
    case_results: list[CaseResult],
    metric_names: Iterable[str],
) -> dict[str, MetricCounts]:
    counts: dict[str, MetricCounts] = {}
    for metric_name in metric_names:
        passed = 0
        failed = 0
        not_applicable = 0
        for case_result in case_results:
            metric = case_result.metrics[metric_name]
            if metric.status == "pass":
                passed += 1
            elif metric.status == "fail":
                failed += 1
            else:
                not_applicable += 1
        counts[metric_name] = MetricCounts.model_validate(
            {
                "pass": passed,
                "fail": failed,
                "not_applicable": not_applicable,
            }
        )
    return counts


def _run_id(timestamp: datetime) -> str:
    return f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:6]}"
