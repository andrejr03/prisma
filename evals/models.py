"""Typed models and loaders for Prisma evaluation assets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

MetricStatus = Literal["pass", "fail", "not_applicable"]


class GoldenCaseFileError(ValueError):
    """Raised when a golden case file cannot be loaded or validated."""


class GoldenCase(BaseModel):
    """One committed golden evaluation case."""

    model_config = ConfigDict(extra="forbid")

    id: str
    question: str
    expected_source_paths: list[str]
    expected_keywords: list[str]
    min_citations: int = Field(ge=0)
    expected_workflow_status: str | None = None
    expects_no_context: bool = False
    notes: str | None = None

    @field_validator("id", "question")
    @classmethod
    def require_non_empty_string(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must be a non-empty string")
        return cleaned

    @field_validator("expected_source_paths")
    @classmethod
    def validate_source_paths(cls, value: list[str]) -> list[str]:
        for path in value:
            if not path or not path.strip():
                raise ValueError("expected source paths must be non-empty strings")
            if Path(path).is_absolute():
                raise ValueError("expected source paths must be repository-relative")
        return value

    @field_validator("expected_keywords")
    @classmethod
    def validate_keywords(cls, value: list[str]) -> list[str]:
        for keyword in value:
            if not keyword or not keyword.strip():
                raise ValueError("expected keywords must be non-empty strings")
            if keyword != keyword.lower():
                raise ValueError("expected keywords must be lowercased")
        return value

    @model_validator(mode="after")
    def validate_case_contract(self) -> GoldenCase:
        if self.expects_no_context:
            if self.min_citations != 0:
                raise ValueError("no-context cases must set min_citations to 0")
            if self.expected_source_paths:
                raise ValueError("no-context cases must not set expected source paths")
            if self.expected_keywords:
                raise ValueError("no-context cases must not set expected keywords")
            return self

        if not self.expected_source_paths:
            raise ValueError("answer cases must set at least one expected source path")
        if self.min_citations < 1:
            raise ValueError("answer cases must require at least one citation")
        return self


class MetricResult(BaseModel):
    """Pass/fail/not-applicable result for a deterministic metric."""

    model_config = ConfigDict(extra="forbid")

    status: MetricStatus
    reason: str | None = None
    details: dict[str, int | float | str | bool | list[str]] = Field(default_factory=dict)


class MetricCounts(BaseModel):
    """Aggregate status counts for one metric."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    pass_count: int = Field(alias="pass", ge=0)
    fail: int = Field(ge=0)
    not_applicable: int = Field(ge=0)


class CaseResult(BaseModel):
    """Evaluation result for one golden case."""

    model_config = ConfigDict(extra="forbid")

    id: str
    passed: bool
    metrics: dict[str, MetricResult]
    failure_reasons: list[str]
    latency_ms: int | None = Field(default=None, ge=0)


class AggregateResult(BaseModel):
    """Aggregate pass-rate summary for a scorecard."""

    model_config = ConfigDict(extra="forbid")

    cases_passed: int = Field(ge=0)
    cases_failed: int = Field(ge=0)
    pass_rate: float = Field(ge=0.0, le=1.0)
    minimum_pass_rate: float = Field(ge=0.0, le=1.0)
    meets_minimum: bool


class Scorecard(BaseModel):
    """Structured Phase 4 evaluation scorecard."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    timestamp: str
    index_fingerprint: str | None
    case_count: int = Field(ge=0)
    metrics: dict[str, MetricCounts]
    cases: list[CaseResult]
    aggregate: AggregateResult


def load_golden_cases(path: Path) -> list[GoldenCase]:
    """Load and validate a JSON Lines golden case file."""

    cases: list[GoldenCase] = []
    seen_ids: set[str] = set()

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GoldenCaseFileError(f"Invalid JSON on line {line_number}: {exc.msg}") from exc

        try:
            case = GoldenCase.model_validate(raw)
        except ValidationError as exc:
            raise GoldenCaseFileError(f"Invalid golden case on line {line_number}: {exc}") from exc

        if case.id in seen_ids:
            raise GoldenCaseFileError(f"Duplicate golden case id on line {line_number}: {case.id}")
        seen_ids.add(case.id)
        cases.append(case)

    if not cases:
        raise GoldenCaseFileError(f"Golden case file contains no cases: {path}")

    return cases
