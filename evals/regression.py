"""Local Phase 5 prompt-regression runner.

Invoke with:

    python -m evals.regression
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from app.config import PrismaSettings, load_settings
from pydantic import BaseModel, ValidationError

from evals.fingerprints import fingerprint_prompt
from evals.models import MetricCounts, Scorecard
from evals.report_models import (
    CaseDelta,
    CaseDeltaStatus,
    MetricDelta,
    MetricDeltaStatus,
    Phase4Baseline,
    PromptFingerprint,
    PromptSnapshot,
    RegressionReport,
    RegressionSummary,
    UnavailableComparison,
)
from evals.runner import run_evaluation

TModel = TypeVar("TModel", bound=BaseModel)

_UNAVAILABLE_REASON = "Phase 4 baseline summary does not contain historical detail."


class RegressionBaselineError(ValueError):
    """Raised when a committed regression input is malformed."""


def run_regression(settings: PrismaSettings | None = None) -> RegressionReport:
    """Run prompt regression and return the generated report."""

    resolved_settings = settings or load_settings()
    baseline = load_phase4_baseline(resolved_settings.prompt_regression_baseline_path)
    snapshot = load_prompt_snapshot(resolved_settings.prompt_regression_snapshot_path)
    current_fingerprint = fingerprint_prompt(
        prompt_path=resolved_settings.prompt_path,
        repo_root=resolved_settings.repo_root,
    )
    scorecard = run_evaluation(settings=resolved_settings)
    report = build_regression_report(
        baseline=baseline,
        baseline_path=resolved_settings.prompt_regression_baseline_path,
        snapshot=snapshot,
        current_fingerprint=current_fingerprint,
        scorecard=scorecard,
        scorecard_path=resolved_settings.eval_scorecard_path,
    )
    write_regression_report(
        path=resolved_settings.prompt_regression_report_path,
        report=report,
        repo_root=resolved_settings.repo_root,
    )
    return report


def build_regression_report(
    *,
    baseline: Phase4Baseline,
    baseline_path: Path,
    snapshot: PromptSnapshot,
    current_fingerprint: PromptFingerprint,
    scorecard: Scorecard,
    scorecard_path: Path,
    run_id: str | None = None,
    timestamp: str | None = None,
) -> RegressionReport:
    """Compare a current scorecard with the committed Phase 4 baseline."""

    if baseline.baseline_id != snapshot.baseline_id:
        raise RegressionBaselineError(
            "Prompt snapshot baseline_id does not match Phase 4 baseline baseline_id"
        )
    _validate_baseline_summary(baseline)

    case_deltas = compare_cases(baseline, scorecard)
    metric_deltas = compare_metrics(baseline, scorecard)
    changed_cases = [delta for delta in case_deltas if delta.status != "unchanged"]
    improved_metrics = [delta.metric for delta in metric_deltas if delta.status == "improved"]
    regressed_metrics = [delta.metric for delta in metric_deltas if delta.status == "regressed"]
    unchanged_metrics = [delta.metric for delta in metric_deltas if delta.status == "unchanged"]
    overall_pass_rate_delta = round(
        scorecard.aggregate.pass_rate - baseline.aggregate.pass_rate,
        12,
    )

    new_fingerprint = PromptFingerprint.model_validate(current_fingerprint)
    return RegressionReport(
        run_id=run_id or _run_id(),
        timestamp=timestamp or _utc_timestamp(),
        baseline_id=baseline.baseline_id,
        baseline_path=_display_path(baseline_path),
        scorecard_path=_display_path(scorecard_path),
        old_prompt_fingerprint=snapshot.prompt_fingerprint,
        new_prompt_fingerprint=new_fingerprint,
        case_count=scorecard.case_count,
        case_deltas=case_deltas,
        changed_cases=changed_cases,
        metric_deltas=metric_deltas,
        improved_metrics=improved_metrics,
        regressed_metrics=regressed_metrics,
        unchanged_metrics=unchanged_metrics,
        unavailable_comparisons=[
            UnavailableComparison(
                comparison="workflow",
                status="baseline_unavailable",
                reason=_UNAVAILABLE_REASON,
            ),
            UnavailableComparison(
                comparison="citation",
                status="baseline_unavailable",
                reason=_UNAVAILABLE_REASON,
            ),
            UnavailableComparison(
                comparison="retrieval_attempt",
                status="baseline_unavailable",
                reason=_UNAVAILABLE_REASON,
            ),
        ],
        overall_pass_rate_delta=overall_pass_rate_delta,
        summary=RegressionSummary(
            changed_case_count=len(changed_cases),
            improved_metric_count=len(improved_metrics),
            regressed_metric_count=len(regressed_metrics),
            unchanged_metric_count=len(unchanged_metrics),
            baseline_unchanged=True,
            prompt_changed=snapshot.prompt_fingerprint.digest != new_fingerprint.digest,
        ),
    )


def compare_cases(baseline: Phase4Baseline, scorecard: Scorecard) -> list[CaseDelta]:
    """Compare per-case pass/fail status."""

    baseline_cases = {case.id: case for case in baseline.cases}
    current_cases = {case.id: case for case in scorecard.cases}
    case_ids = sorted(set(baseline_cases) | set(current_cases))
    deltas: list[CaseDelta] = []
    for case_id in case_ids:
        baseline_case = baseline_cases.get(case_id)
        current_case = current_cases.get(case_id)
        baseline_passed = baseline_case.passed if baseline_case is not None else None
        current_passed = current_case.passed if current_case is not None else None
        deltas.append(
            CaseDelta(
                case_id=case_id,
                status=_case_status(baseline_passed, current_passed),
                baseline_passed=baseline_passed,
                current_passed=current_passed,
                workflow_delta="baseline_unavailable",
                citation_delta="baseline_unavailable",
                retrieval_attempt_delta="baseline_unavailable",
            )
        )
    return deltas


def compare_metrics(baseline: Phase4Baseline, scorecard: Scorecard) -> list[MetricDelta]:
    """Compare per-metric aggregate counts."""

    metric_names = sorted(set(baseline.metrics) | set(scorecard.metrics))
    return [
        _metric_delta(
            metric_name,
            baseline.metrics.get(metric_name),
            scorecard.metrics.get(metric_name),
        )
        for metric_name in metric_names
    ]


def load_phase4_baseline(path: Path) -> Phase4Baseline:
    """Load and validate the committed Phase 4 baseline."""

    return _load_json_model(path, Phase4Baseline)


def load_prompt_snapshot(path: Path) -> PromptSnapshot:
    """Load and validate the committed prompt snapshot."""

    return _load_json_model(path, PromptSnapshot)


def write_regression_report(*, path: Path, report: RegressionReport, repo_root: Path) -> None:
    """Write a generated regression report under the ignored local tree."""

    _ensure_generated_report_path(path=path, repo_root=repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = report.model_dump(mode="json", by_alias=True, exclude_none=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def render_summary(report: RegressionReport, *, report_path: Path) -> str:
    """Render a concise human-readable prompt-regression summary."""

    prompt_status = "changed" if report.summary.prompt_changed else "unchanged"
    lines = [
        "Prisma prompt regression complete",
        f"Prompt: {prompt_status}",
        f"Cases changed: {report.summary.changed_case_count}/{report.case_count}",
        f"Metrics regressed: {report.summary.regressed_metric_count}",
        f"Overall pass-rate delta: {report.overall_pass_rate_delta:+.3f}",
        f"Report: {report_path.as_posix()}",
    ]
    return "\n".join(lines)


def main() -> int:
    """CLI entry point for `python -m evals.regression`."""

    settings = load_settings()
    report = run_regression(settings=settings)
    print(render_summary(report, report_path=settings.prompt_regression_report_path))
    return 0


def _metric_delta(
    metric_name: str,
    baseline_counts: MetricCounts | None,
    current_counts: MetricCounts | None,
) -> MetricDelta:
    if baseline_counts is None:
        return MetricDelta(
            metric=metric_name,
            status="added",
            baseline_counts=None,
            current_counts=current_counts,
            pass_delta=None,
            fail_delta=None,
            not_applicable_delta=None,
        )
    if current_counts is None:
        return MetricDelta(
            metric=metric_name,
            status="missing",
            baseline_counts=baseline_counts,
            current_counts=None,
            pass_delta=None,
            fail_delta=None,
            not_applicable_delta=None,
        )

    pass_delta = current_counts.pass_count - baseline_counts.pass_count
    fail_delta = current_counts.fail - baseline_counts.fail
    not_applicable_delta = current_counts.not_applicable - baseline_counts.not_applicable
    baseline_score = baseline_counts.pass_count - baseline_counts.fail
    current_score = current_counts.pass_count - current_counts.fail
    status: MetricDeltaStatus
    if current_score > baseline_score:
        status = "improved"
    elif current_score < baseline_score:
        status = "regressed"
    else:
        status = "unchanged"

    return MetricDelta(
        metric=metric_name,
        status=status,
        baseline_counts=baseline_counts,
        current_counts=current_counts,
        pass_delta=pass_delta,
        fail_delta=fail_delta,
        not_applicable_delta=not_applicable_delta,
    )


def _case_status(
    baseline_passed: bool | None,
    current_passed: bool | None,
) -> CaseDeltaStatus:
    if baseline_passed is None:
        return "added"
    if current_passed is None:
        return "missing"
    if baseline_passed is False and current_passed is True:
        return "improved"
    if baseline_passed is True and current_passed is False:
        return "regressed"
    return "unchanged"


def _validate_baseline_summary(baseline: Phase4Baseline) -> None:
    if baseline.case_count != len(baseline.cases):
        raise RegressionBaselineError("Phase 4 baseline case_count does not match cases length")
    if not baseline.metrics:
        raise RegressionBaselineError("Phase 4 baseline contains no metric counts")


def _load_json_model(path: Path, model: type[TModel]) -> TModel:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RegressionBaselineError(f"Invalid JSON in {path}: {exc.msg}") from exc
    except OSError as exc:
        raise RegressionBaselineError(f"Unable to read {path}: {exc}") from exc

    try:
        return model.model_validate(raw)
    except ValidationError as exc:
        raise RegressionBaselineError(f"Invalid regression input {path}: {exc}") from exc


def _ensure_generated_report_path(*, path: Path, repo_root: Path) -> None:
    try:
        relative_path = path.resolve().relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError("Regression report path must be inside the repository") from exc

    if not relative_path.as_posix().startswith(".local/"):
        raise ValueError("Regression report path must be under .local/")


def _display_path(path: Path) -> str:
    return path.as_posix()


def _run_id() -> str:
    return f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:6]}"


def _utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
