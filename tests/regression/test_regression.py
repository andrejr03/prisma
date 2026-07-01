from __future__ import annotations

import json
from pathlib import Path

from evals.models import AggregateResult, CaseResult, MetricCounts, MetricResult, Scorecard
from evals.regression import build_regression_report, write_regression_report
from evals.report_models import Phase4Baseline, PromptFingerprint, PromptSnapshot


def test_regression_comparison_records_case_metric_and_unavailable_deltas(tmp_path: Path) -> None:
    report = build_regression_report(
        baseline=_baseline(),
        baseline_path=Path("evals/baselines/phase4-baseline.json"),
        snapshot=_snapshot(),
        current_fingerprint=_fingerprint("sha256:new"),
        scorecard=_scorecard(),
        scorecard_path=Path(".local/prisma/evals/scorecard.json"),
        run_id="20260630T000000Z-abc123",
        timestamp="2026-06-30T00:00:00Z",
    )

    changed_by_id = {case.case_id: case for case in report.changed_cases}
    assert changed_by_id["regressed-case"].status == "regressed"
    assert changed_by_id["improved-case"].status == "improved"
    assert report.improved_metrics == ["metric_improved"]
    assert report.regressed_metrics == ["metric_regressed"]
    assert report.unchanged_metrics == ["metric_unchanged"]
    assert {item.comparison for item in report.unavailable_comparisons} == {
        "workflow",
        "citation",
        "retrieval_attempt",
    }
    assert all(
        case.workflow_delta == "baseline_unavailable"
        and case.citation_delta == "baseline_unavailable"
        and case.retrieval_attempt_delta == "baseline_unavailable"
        for case in report.case_deltas
    )


def test_report_generation_writes_generated_local_artifact(tmp_path: Path) -> None:
    report_path = tmp_path / ".local" / "prisma" / "evals" / "regression.json"
    report = _report()

    write_regression_report(path=report_path, report=report, repo_root=tmp_path)

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["baseline_id"] == "phase4-baseline"
    assert payload["summary"]["baseline_unchanged"] is True


def test_report_output_is_deterministic_with_fixed_run_metadata() -> None:
    first = _report()
    second = _report()

    assert first.model_dump(mode="json", by_alias=True) == second.model_dump(
        mode="json",
        by_alias=True,
    )


def test_regression_report_generation_does_not_mutate_committed_baselines(
    repo_root: Path,
    tmp_path: Path,
) -> None:
    baseline_path = repo_root / "evals" / "baselines" / "phase4-baseline.json"
    snapshot_path = repo_root / "evals" / "baselines" / "phase4-prompt-snapshot.json"
    baseline_before = baseline_path.read_text(encoding="utf-8")
    snapshot_before = snapshot_path.read_text(encoding="utf-8")

    write_regression_report(
        path=tmp_path / ".local" / "prisma" / "evals" / "regression.json",
        report=_report(),
        repo_root=tmp_path,
    )

    assert baseline_path.read_text(encoding="utf-8") == baseline_before
    assert snapshot_path.read_text(encoding="utf-8") == snapshot_before


def _report():
    return build_regression_report(
        baseline=_baseline(),
        baseline_path=Path("evals/baselines/phase4-baseline.json"),
        snapshot=_snapshot(),
        current_fingerprint=_fingerprint("sha256:old"),
        scorecard=_scorecard(),
        scorecard_path=Path(".local/prisma/evals/scorecard.json"),
        run_id="20260630T000000Z-abc123",
        timestamp="2026-06-30T00:00:00Z",
    )


def _baseline() -> Phase4Baseline:
    return Phase4Baseline(
        baseline_id="phase4-baseline",
        golden_path="evals/golden/cases.jsonl",
        case_count=3,
        index_fingerprint="sha256:index",
        metrics={
            "metric_improved": _counts(passed=1, failed=1),
            "metric_regressed": _counts(passed=2, failed=0),
            "metric_unchanged": _counts(passed=1, failed=0),
        },
        cases=[
            {"id": "stable-case", "passed": True},
            {"id": "regressed-case", "passed": True},
            {"id": "improved-case", "passed": False},
        ],
        aggregate=AggregateResult(
            cases_passed=2,
            cases_failed=1,
            pass_rate=2 / 3,
            minimum_pass_rate=0.8,
            meets_minimum=False,
        ),
        policy={
            "routine_scorecard_path": ".local/prisma/evals/scorecard.json",
            "routine_scorecards_committed": False,
            "baseline_comparison_enforced": False,
        },
    )


def _scorecard() -> Scorecard:
    return Scorecard(
        run_id="20260630T000000Z-current",
        timestamp="2026-06-30T00:00:00Z",
        index_fingerprint="sha256:index",
        case_count=3,
        metrics={
            "metric_improved": _counts(passed=2, failed=0),
            "metric_regressed": _counts(passed=1, failed=1),
            "metric_unchanged": _counts(passed=1, failed=0),
        },
        cases=[
            _case("stable-case", passed=True),
            _case("regressed-case", passed=False),
            _case("improved-case", passed=True),
        ],
        aggregate=AggregateResult(
            cases_passed=2,
            cases_failed=1,
            pass_rate=2 / 3,
            minimum_pass_rate=0.8,
            meets_minimum=False,
        ),
    )


def _snapshot() -> PromptSnapshot:
    return PromptSnapshot(
        snapshot_id="phase4-prompt-snapshot",
        baseline_id="phase4-baseline",
        prompt_fingerprint=_fingerprint("sha256:old"),
    )


def _fingerprint(digest: str) -> PromptFingerprint:
    return PromptFingerprint(
        algorithm="sha256",
        digest=digest,
        prompt_path="prompts/baseline_rag.txt",
        byte_count=230,
        line_count=5,
        captured_at="2026-06-30T00:00:00Z",
        semantic_version=None,
    )


def _case(case_id: str, *, passed: bool) -> CaseResult:
    return CaseResult(
        id=case_id,
        passed=passed,
        metrics={"metric": MetricResult(status="pass" if passed else "fail")},
        failure_reasons=[] if passed else ["metric: failed"],
    )


def _counts(*, passed: int, failed: int, not_applicable: int = 0) -> MetricCounts:
    return MetricCounts.model_validate(
        {"pass": passed, "fail": failed, "not_applicable": not_applicable}
    )
