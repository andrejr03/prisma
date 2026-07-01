from __future__ import annotations

import json
from pathlib import Path

import pytest
from evals.regression import RegressionBaselineError, load_phase4_baseline
from evals.report_models import PromptSnapshot, RegressionReport


def test_prompt_snapshot_validates_expected_shape() -> None:
    snapshot = PromptSnapshot.model_validate(
        {
            "snapshot_id": "phase4-prompt-snapshot",
            "baseline_id": "phase4-baseline",
            "prompt_fingerprint": {
                "algorithm": "sha256",
                "digest": "sha256:abc123",
                "prompt_path": "prompts/baseline_rag.txt",
                "byte_count": 10,
                "line_count": 1,
                "captured_at": "2026-06-30T00:00:00Z",
                "semantic_version": None,
            },
        }
    )

    assert snapshot.baseline_id == "phase4-baseline"
    assert snapshot.prompt_fingerprint.algorithm == "sha256"


def test_regression_report_validates_minimal_report() -> None:
    report = RegressionReport.model_validate(_report_payload())

    assert report.baseline_id == "phase4-baseline"
    assert report.summary.baseline_unchanged is True
    assert report.unavailable_comparisons[0].status == "baseline_unavailable"


def test_malformed_baseline_raises_clear_error(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps({"baseline_id": "phase4-baseline"}), encoding="utf-8")

    with pytest.raises(RegressionBaselineError, match="Invalid regression input"):
        load_phase4_baseline(baseline_path)


def _report_payload() -> dict[str, object]:
    fingerprint = {
        "algorithm": "sha256",
        "digest": "sha256:abc123",
        "prompt_path": "prompts/baseline_rag.txt",
        "byte_count": 10,
        "line_count": 1,
        "captured_at": "2026-06-30T00:00:00Z",
        "semantic_version": None,
    }
    return {
        "run_id": "20260630T000000Z-abc123",
        "timestamp": "2026-06-30T00:00:00Z",
        "baseline_id": "phase4-baseline",
        "baseline_path": "evals/baselines/phase4-baseline.json",
        "scorecard_path": ".local/prisma/evals/scorecard.json",
        "old_prompt_fingerprint": fingerprint,
        "new_prompt_fingerprint": fingerprint,
        "case_count": 0,
        "case_deltas": [],
        "changed_cases": [],
        "metric_deltas": [],
        "improved_metrics": [],
        "regressed_metrics": [],
        "unchanged_metrics": [],
        "unavailable_comparisons": [
            {
                "comparison": "workflow",
                "status": "baseline_unavailable",
                "reason": "Phase 4 baseline summary does not contain historical detail.",
            }
        ],
        "overall_pass_rate_delta": 0.0,
        "summary": {
            "changed_case_count": 0,
            "improved_metric_count": 0,
            "regressed_metric_count": 0,
            "unchanged_metric_count": 0,
            "baseline_unchanged": True,
            "prompt_changed": False,
        },
    }
