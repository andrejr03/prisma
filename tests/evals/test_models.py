from __future__ import annotations

from pathlib import Path

import pytest
from app.config import load_settings

from evals.models import GoldenCaseFileError, load_golden_cases


def test_load_golden_cases_validates_jsonl(tmp_path: Path) -> None:
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text(
        "\n".join(
            [
                (
                    '{"id":"provider-boundaries-basic",'
                    '"question":"What does Prisma mean by provider boundaries?",'
                    '"expected_source_paths":["datasets/sample_corpus/provider-boundaries.md"],'
                    '"expected_keywords":["provider","adapter"],'
                    '"min_citations":1,'
                    '"expected_workflow_status":"completed"}'
                ),
                (
                    '{"id":"out-of-corpus-no-context",'
                    '"question":"What is outside the corpus?",'
                    '"expected_source_paths":[],'
                    '"expected_keywords":[],'
                    '"min_citations":0,'
                    '"expected_workflow_status":"no_context",'
                    '"expects_no_context":true}'
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    cases = load_golden_cases(cases_path)

    assert [case.id for case in cases] == [
        "provider-boundaries-basic",
        "out-of-corpus-no-context",
    ]
    assert cases[0].expected_source_paths == ["datasets/sample_corpus/provider-boundaries.md"]
    assert cases[1].expects_no_context is True


def test_load_golden_cases_rejects_malformed_case(tmp_path: Path) -> None:
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text(
        (
            '{"id":"bad-case",'
            '"expected_source_paths":["datasets/sample_corpus/provider-boundaries.md"],'
            '"expected_keywords":["provider"],'
            '"min_citations":1}\n'
        ),
        encoding="utf-8",
    )

    with pytest.raises(GoldenCaseFileError, match="Invalid golden case on line 1"):
        load_golden_cases(cases_path)


def test_load_golden_cases_rejects_duplicate_ids(tmp_path: Path) -> None:
    cases_path = tmp_path / "cases.jsonl"
    line = (
        '{"id":"duplicate-case",'
        '"question":"What does Prisma measure?",'
        '"expected_source_paths":["datasets/sample_corpus/evaluation-discipline.md"],'
        '"expected_keywords":["evaluation"],'
        '"min_citations":1}\n'
    )
    cases_path.write_text(line + line, encoding="utf-8")

    with pytest.raises(GoldenCaseFileError, match="Duplicate golden case id"):
        load_golden_cases(cases_path)


def test_default_scorecard_path_is_ignored_runtime_artifact(repo_root: Path) -> None:
    settings = load_settings()
    relative_scorecard_path = settings.eval_scorecard_path.relative_to(repo_root).as_posix()
    gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")

    assert relative_scorecard_path == ".local/prisma/evals/scorecard.json"
    assert ".local/" in gitignore
    assert settings.eval_baseline_path.relative_to(repo_root).as_posix() == (
        "evals/baselines/phase4-baseline.json"
    )
