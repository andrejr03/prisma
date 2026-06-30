"""Local Phase 4 evaluation runner.

Invoke with:

    python -m evals.runner
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, cast

from app.api.main import app
from app.config import PrismaSettings, load_settings
from app.retrieval.pipeline import run_indexing
from app.retrieval.search import index_is_ready
from fastapi.testclient import TestClient

from evals.metrics import METRIC_FUNCTIONS
from evals.models import CaseResult, GoldenCase, Scorecard
from evals.models import load_golden_cases as load_cases
from evals.reporting import build_scorecard, render_summary, write_scorecard

PostCase = Callable[[GoldenCase], Mapping[str, Any]]


def run_evaluation(
    *,
    settings: PrismaSettings | None = None,
    cases: list[GoldenCase] | None = None,
    post_case: PostCase | None = None,
    ensure_index: bool = True,
    write_scorecard_artifact: bool = True,
) -> Scorecard:
    """Run the Phase 4 evaluation harness and return a scorecard."""

    resolved_settings = settings or load_settings()
    golden_cases = cases if cases is not None else load_cases(resolved_settings.eval_golden_path)
    index_fingerprint = ensure_local_index(resolved_settings) if ensure_index else None

    if post_case is None:
        case_results = _evaluate_cases_with_test_client(golden_cases)
    else:
        case_results = [evaluate_case(case, post_case(case)) for case in golden_cases]

    scorecard = build_scorecard(
        case_results=case_results,
        metric_names=[name for name, _metric in METRIC_FUNCTIONS],
        index_fingerprint=index_fingerprint,
        minimum_pass_rate=resolved_settings.evals.minimum_pass_rate,
    )
    if write_scorecard_artifact:
        write_scorecard(resolved_settings.eval_scorecard_path, scorecard)
    return scorecard


def evaluate_case(case: GoldenCase, response: Mapping[str, Any]) -> CaseResult:
    """Evaluate every deterministic metric for one case/response pair."""

    metric_results = {name: metric(response, case) for name, metric in METRIC_FUNCTIONS}
    failure_reasons = [
        f"{name}: {result.reason or 'failed'}"
        for name, result in metric_results.items()
        if result.status == "fail"
    ]
    return CaseResult(
        id=case.id,
        passed=not failure_reasons,
        metrics=metric_results,
        failure_reasons=failure_reasons,
    )


def ensure_local_index(settings: PrismaSettings) -> str | None:
    """Verify or build the generated local index and return its fingerprint."""

    if not index_is_ready(settings):
        result = run_indexing(settings)
        return _display_fingerprint(result.fingerprint)
    return read_index_fingerprint(settings.manifest_path)


def read_index_fingerprint(manifest_path: Path) -> str | None:
    """Read the generated index fingerprint from the Phase 1 manifest, if present."""

    if not manifest_path.exists():
        return None
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        return None
    fingerprint = value.get("indexing_fingerprint")
    return _display_fingerprint(fingerprint) if isinstance(fingerprint, str) else None


def main() -> int:
    """CLI entry point for `python -m evals.runner`."""

    settings = load_settings()
    scorecard = run_evaluation(settings=settings)
    print(render_summary(scorecard, scorecard_path=settings.eval_scorecard_path))
    return 0


def _evaluate_cases_with_test_client(cases: list[GoldenCase]) -> list[CaseResult]:
    with TestClient(app) as client:
        return [evaluate_case(case, _post_query(client, case)) for case in cases]


def _post_query(client: TestClient, case: GoldenCase) -> Mapping[str, Any]:
    response = client.post("/query", json={"question": case.question})
    body = response.json()
    if not isinstance(body, Mapping):
        raise RuntimeError(f"Expected JSON object response for eval case {case.id}")
    return cast(Mapping[str, Any], body)


def _display_fingerprint(fingerprint: str) -> str:
    if fingerprint.startswith("sha256:"):
        return fingerprint
    return f"sha256:{fingerprint}"


if __name__ == "__main__":
    raise SystemExit(main())
