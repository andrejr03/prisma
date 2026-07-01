"""Typed report models for Phase 5 prompt regression."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from evals.models import AggregateResult, MetricCounts

CaseDeltaStatus = Literal["unchanged", "improved", "regressed", "added", "missing"]
MetricDeltaStatus = Literal["unchanged", "improved", "regressed", "added", "missing"]
FieldDeltaStatus = Literal["unchanged", "changed", "baseline_unavailable", "current_unavailable"]


class PromptFingerprint(BaseModel):
    """Stable prompt digest plus non-digest metadata."""

    model_config = ConfigDict(extra="forbid")

    algorithm: Literal["sha256"]
    digest: str
    prompt_path: str
    byte_count: int = Field(ge=0)
    line_count: int = Field(ge=0)
    captured_at: str
    semantic_version: str | None = None


class PromptSnapshot(BaseModel):
    """Committed prompt fingerprint associated with a baseline."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    baseline_id: str
    prompt_fingerprint: PromptFingerprint


class BaselineCase(BaseModel):
    """Case status recorded in a committed baseline summary."""

    model_config = ConfigDict(extra="forbid")

    id: str
    passed: bool


class Phase4Baseline(BaseModel):
    """Committed Phase 4 baseline summary used for regression comparison."""

    model_config = ConfigDict(extra="forbid")

    baseline_id: str
    golden_path: str
    case_count: int = Field(ge=0)
    index_fingerprint: str | None
    metrics: dict[str, MetricCounts]
    cases: list[BaselineCase]
    aggregate: AggregateResult
    policy: dict[str, str | int | float | bool]


class MetricDelta(BaseModel):
    """Delta between baseline and current counts for one metric."""

    model_config = ConfigDict(extra="forbid")

    metric: str
    status: MetricDeltaStatus
    baseline_counts: MetricCounts | None
    current_counts: MetricCounts | None
    pass_delta: int | None
    fail_delta: int | None
    not_applicable_delta: int | None


class CaseDelta(BaseModel):
    """Delta between baseline and current status for one case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    status: CaseDeltaStatus
    baseline_passed: bool | None
    current_passed: bool | None
    workflow_delta: FieldDeltaStatus
    citation_delta: FieldDeltaStatus
    retrieval_attempt_delta: FieldDeltaStatus


class UnavailableComparison(BaseModel):
    """Comparison that could not be computed from available baseline fields."""

    model_config = ConfigDict(extra="forbid")

    comparison: Literal["workflow", "citation", "retrieval_attempt"]
    status: Literal["baseline_unavailable"]
    reason: str


class RegressionSummary(BaseModel):
    """Compact regression summary for console and report consumers."""

    model_config = ConfigDict(extra="forbid")

    changed_case_count: int = Field(ge=0)
    improved_metric_count: int = Field(ge=0)
    regressed_metric_count: int = Field(ge=0)
    unchanged_metric_count: int = Field(ge=0)
    baseline_unchanged: bool
    prompt_changed: bool


class RegressionReport(BaseModel):
    """Generated prompt-regression report."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    timestamp: str
    baseline_id: str
    baseline_path: str
    scorecard_path: str
    old_prompt_fingerprint: PromptFingerprint
    new_prompt_fingerprint: PromptFingerprint
    case_count: int = Field(ge=0)
    case_deltas: list[CaseDelta]
    changed_cases: list[CaseDelta]
    metric_deltas: list[MetricDelta]
    improved_metrics: list[str]
    regressed_metrics: list[str]
    unchanged_metrics: list[str]
    unavailable_comparisons: list[UnavailableComparison]
    overall_pass_rate_delta: float
    summary: RegressionSummary
