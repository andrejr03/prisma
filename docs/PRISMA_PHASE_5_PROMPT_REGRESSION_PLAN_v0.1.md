# Phase 5 Prompt Regression Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task once approved.

**Goal:** Add a deterministic local prompt-regression workflow that fingerprints prompt assets, runs the Phase 4 evaluation harness, compares the result with the committed Phase 4 baseline, and emits an informational regression report.

**Architecture:** Phase 5 extends the existing `evals/` boundary without changing application behavior. The regression runner reads the current prompt asset, computes a stable fingerprint, runs the Phase 4 eval harness through the public API boundary, compares the generated scorecard with the committed baseline, and writes a generated report under `.local/`. The Phase 4 baseline remains immutable.

**Tech Stack:** Python 3.11, Pydantic, standard-library `hashlib`/`json`, existing Phase 4 eval models and runner, pytest, ruff, mypy. No new runtime dependency is expected.

---

> Production LLM Engineering Platform  
> Planning document only. This document defines what Phase 5 should implement. It does not implement code, create directories, or modify application files.

**Status:** Draft v0.1  
**Date:** 2026-06-30  
**Document:** PRISMA_PHASE_5_PROMPT_REGRESSION_PLAN_v0.1.md  
**Audience:** developers, AI engineers, ML engineers, technical reviewers, and maintainers  
**Companions:** [PRISMA_PROJECT_PLAN_v0.1.md](PRISMA_PROJECT_PLAN_v0.1.md), [PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md](PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md), [PRISMA_PHASE_2_BASELINE_RAG_API_PLAN_v0.1.md](PRISMA_PHASE_2_BASELINE_RAG_API_PLAN_v0.1.md), [PRISMA_PHASE_4_EVALUATION_HARNESS_PLAN_v0.1.md](PRISMA_PHASE_4_EVALUATION_HARNESS_PLAN_v0.1.md), [ADR-0001](adr/ADR-0001-code-data-separation.md), [ADR-0002](adr/ADR-0002-provider-adapter-boundary.md), [ADR-0003](adr/ADR-0003-secrets-via-environment.md), [ADR-0004](adr/ADR-0004-evaluation-first-development.md)

---

## 1. Purpose

Phase 5 exists to make prompt changes measurable, reviewable, and reproducible.

Phase 4 made Prisma measurable through a committed golden dataset, deterministic metrics, a generated scorecard, and a committed baseline. Phase 5 builds directly on that foundation by comparing the current prompt-driven behavior against the Phase 4 baseline. It should answer:

- Did a prompt change alter behavior?
- Which evaluation cases changed?
- Which metrics improved?
- Which metrics regressed?

This phase is an engineering control for prompt changes. It is not prompt engineering, prompt optimization, prompt tuning, prompt generation, or a CI gate.

## 2. Scope

### In Scope

- Prompt snapshots as committed metadata records for the baseline prompt state.
- Prompt fingerprinting for the configured prompt asset.
- Prompt metadata in generated regression reports.
- A local regression runner invoked as `python -m evals.regression`.
- Deterministic baseline comparison against `evals/baselines/phase4-baseline.json`.
- Generated regression report written under `.local/prisma/evals/regression.json`.
- Per-case and per-metric comparison of the current scorecard against the committed baseline.
- Informational reporting of changed workflow status, citations, and retrieval attempts where available.
- Correctness tests for fingerprinting, comparison, report generation, and baseline immutability.
- Non-secret prompt-regression configuration in `configs/defaults.toml`.
- README and `docs/DEVELOPMENT.md` updates documenting the local regression smoke path.

### Explicit Non-Goals

- No CI gates.
- No GitHub Actions.
- No PromptFoo.
- No online evaluation.
- No LLM-as-judge.
- No semantic grading.
- No prompt optimization.
- No automatic prompt rewriting.
- No prompt generation.
- No prompt registry.
- No hosted services.
- No dashboards.
- No human review workflow.
- No automatic approval or rejection of prompt changes.
- No provider comparison.
- No Phase 6 observability, traces, cost budgets, or runtime metrics.

## 3. Architectural Alignment

### Project Plan

The project plan defines Phase 5 as Prompt Regression: versioned prompt artifacts, regression runs on prompt changes, baseline comparison, and change reports. This plan implements that slice only. It deliberately excludes CI gates, observability budgets, dashboards, hosted services, and model benchmarking.

### Repository Architecture

Prompt assets remain under `prompts/` as data. Regression logic lives under `evals/` because it measures behavior against committed evaluation assets. Generated reports are runtime artifacts under `.local/` and are not committed. The planned flow is:

```text
evals.regression -> current prompt -> prompt fingerprint
                 -> evals.runner -> generated scorecard
                 -> phase4 baseline -> deterministic comparison
                 -> .local/prisma/evals/regression.json
```

### Phase 2 Prompt Asset

Phase 2 introduced one minimal prompt asset: `prompts/baseline_rag.txt`. Phase 5 measures changes to that configured prompt. It does not convert the prompt into a registry or prompt management system.

### Phase 4 Evaluation Harness

Phase 5 reuses the Phase 4 golden cases, metrics, scorecard model, and runner. It does not add new eval metrics and does not mutate the committed baseline. Regression is a comparison layer over existing evaluation output.

### ADR-0001: Code / Data Separation

Prompt text and prompt snapshots are data. Regression logic is code under `evals/`. Configuration remains declarative under `configs/`. No prompt metadata file may contain executable logic.

### ADR-0002: Provider Adapter Boundary

Prompt regression compares provider-neutral API responses and scorecards. It must not import provider SDKs, assume provider response objects, or introduce provider-specific comparison logic.

### ADR-0003: Secrets via Environment

Phase 5 requires no secrets. Prompt metadata, fingerprints, baseline paths, and report paths are non-secret. No `.env` or `.env.example` is introduced.

### ADR-0004: Evaluation-First Development

Phase 5 is an explicit evaluation-first control for prompt changes. It measures regressions before a prompt change is treated as complete, but remains informational in this phase.

## 4. Prompt Regression Philosophy

- Prompts are versioned assets.
- Prompts are data, never executable logic.
- Prompt changes require measurement against committed evaluation expectations.
- Comparisons must be deterministic and local.
- The committed Phase 4 baseline remains immutable during routine regression runs.
- Regression is informational in Phase 5.
- Phase 5 does not automatically approve, reject, gate, rewrite, or optimize prompts.
- A regression report is evidence for human review, not a policy engine.

## 5. Prompt Fingerprinting

The prompt fingerprint is a deterministic SHA256 digest over the exact UTF-8 bytes of the configured prompt file.

Fingerprint records should include:

- `algorithm`: `"sha256"`
- `digest`: full lowercase hex digest, displayed as `sha256:<digest>` in reports.
- `prompt_path`: repository-relative prompt path, e.g. `prompts/baseline_rag.txt`.
- `byte_count`: number of UTF-8 bytes read.
- `line_count`: number of text lines.
- `captured_at`: UTC timestamp for generated reports or committed snapshot metadata.
- `semantic_version`: optional human-maintained prompt version string, initially nullable.

The digest must not include timestamps, absolute paths, machine-specific paths, or generated report metadata. Those fields may appear beside the digest as metadata, but they must not affect the fingerprint.

## 6. Regression Dataset

Phase 5 uses only existing Phase 4 evaluation inputs:

- Golden cases: `evals/golden/cases.jsonl`
- Committed evaluation baseline: `evals/baselines/phase4-baseline.json`
- Current configured prompt: `prompts/baseline_rag.txt` via `generation.prompt_path`

No new golden datasets are introduced. No online examples, human annotations, or production feedback are introduced.

## 7. Regression Metrics

Regression compares the current generated scorecard with the committed baseline using deterministic structural deltas:

| Comparison | Definition |
|---|---|
| `overall_pass_rate_delta` | Current pass rate minus baseline pass rate. |
| `per_case_delta` | Case-level status changes: unchanged, improved, regressed, added, or missing. |
| `per_metric_delta` | Metric count changes for pass/fail/not-applicable. |
| `changed_workflow_behavior` | Case-level workflow status, route, or retry-bound metadata changed when both baseline and current records expose those fields. |
| `changed_citations` | Case-level cited source path or citation count changed when both baseline and current records expose those fields. |
| `changed_retrieval_attempts` | Case-level retrieval attempt count changed when both baseline and current records expose those fields. |

The existing Phase 4 baseline is intentionally a compact summary. If a baseline field is unavailable, Phase 5 must report the comparison as `baseline_unavailable` rather than mutating the baseline or fabricating historical detail.

Phase 5 must not add semantic similarity, LLM-as-judge, prompt scoring, RAGAS, PromptFoo, model benchmarking, or provider comparison.

## 8. Regression Report

The regression runner writes a generated JSON report to:

```text
.local/prisma/evals/regression.json
```

The report should include:

- `run_id`
- `timestamp`
- `baseline_id`
- `baseline_path`
- `scorecard_path`
- `old_prompt_fingerprint`
- `new_prompt_fingerprint`
- `case_count`
- `changed_cases`
- `improved_metrics`
- `regressed_metrics`
- `unchanged_metrics`
- `unavailable_comparisons`
- `overall_pass_rate_delta`
- `summary`

Example shape:

```json
{
  "baseline_id": "phase4-baseline",
  "old_prompt_fingerprint": {
    "prompt_path": "prompts/baseline_rag.txt",
    "digest": "sha256:<baseline-prompt-digest>"
  },
  "new_prompt_fingerprint": {
    "prompt_path": "prompts/baseline_rag.txt",
    "digest": "sha256:<current-prompt-digest>"
  },
  "changed_cases": [],
  "improved_metrics": [],
  "regressed_metrics": [],
  "unchanged_metrics": [
    "retrieval_source_hit",
    "citation_source_hit",
    "citation_validity",
    "answer_contains_expected_terms",
    "no_unsupported_citations",
    "workflow_completed",
    "workflow_retry_bounded",
    "structured_response_validity"
  ],
  "overall_pass_rate_delta": 0.0,
  "summary": {
    "changed_case_count": 0,
    "improved_metric_count": 0,
    "regressed_metric_count": 0,
    "baseline_unchanged": true
  }
}
```

Routine regression reports are generated artifacts and must not be committed.

## 9. Repository Changes

Phase 5 should create or modify only the paths listed here.

### Create Files

```text
evals/fingerprints.py
evals/report_models.py
evals/regression.py
evals/baselines/phase4-prompt-snapshot.json
tests/regression/__init__.py
tests/regression/test_fingerprints.py
tests/regression/test_regression.py
tests/regression/test_report_models.py
```

### Modify Existing Files

```text
configs/defaults.toml
app/config.py
README.md
docs/DEVELOPMENT.md
```

Required responsibilities:

- `evals/fingerprints.py`: prompt fingerprint calculation and repository-relative prompt metadata.
- `evals/report_models.py`: Pydantic models for prompt fingerprints, baseline summaries, metric deltas, case deltas, and regression reports.
- `evals/regression.py`: runner invoked with `python -m evals.regression`.
- `evals/baselines/phase4-prompt-snapshot.json`: committed prompt snapshot metadata for the prompt state associated with the Phase 4 baseline. It records fingerprint metadata only; it does not duplicate prompt text.
- `tests/regression/*`: correctness tests for Phase 5 regression code.
- `configs/defaults.toml`: add `[prompt_regression]`.
- `app/config.py`: add typed, non-secret prompt-regression settings.
- `README.md` and `docs/DEVELOPMENT.md`: document the prompt-regression smoke path and generated report policy.

Do not create `evals/regression/` if `evals/regression.py` is used as the command module. Do not create `.github/`, `docker/`, `scripts/`, dashboard directories, hosted-service configuration, prompt-registry directories, or provider-comparison assets.

## 10. Runner

The runner is invoked as:

```bash
python -m evals.regression
```

Behavior:

1. Load settings from `configs/defaults.toml`.
2. Resolve the configured prompt path from `generation.prompt_path`.
3. Load and fingerprint the current prompt.
4. Load the committed baseline prompt snapshot.
5. Load the committed Phase 4 baseline summary.
6. Run the Phase 4 evaluation harness using `evals.runner.run_evaluation`.
7. Compare the generated scorecard with the committed baseline.
8. Write the regression report to `.local/prisma/evals/regression.json`.
9. Print a concise console summary.
10. Exit `0` on successful report generation, regardless of informational regressions.

The runner must never:

- Modify `prompts/`.
- Modify golden cases.
- Modify `evals/baselines/phase4-baseline.json`.
- Modify `evals/baselines/phase4-prompt-snapshot.json`.
- Require internet access.
- Require provider credentials.
- Fail as a gate because a metric regressed.

## 11. Testing Strategy

Tests are correctness tests for the prompt-regression harness. They do not assert prompt quality.

Required tests:

- **Fingerprint stability:** identical prompt bytes produce identical SHA256 fingerprints across runs.
- **Fingerprint sensitivity:** changed prompt bytes produce a different fingerprint.
- **Repository-relative metadata:** prompt paths in reports are repository-relative and never absolute.
- **Regression comparison:** synthetic baseline/current scorecards produce expected case and metric deltas.
- **No baseline mutation:** running regression code does not write to committed baseline or prompt snapshot paths.
- **Report generation:** regression report serializes to the configured generated path.
- **Deterministic output:** excluding run id and timestamp, repeated comparisons over the same inputs produce the same report content.
- **Malformed baseline handling:** malformed or missing baseline fields raise clear validation errors.

Tests should use small synthetic scorecard and baseline fixtures where possible. Tests that invoke the live runner may use the existing local Phase 4 harness pattern, but must not require network access.

## 12. Configuration

Phase 5 adds non-secret prompt-regression configuration:

```toml
[prompt_regression]
baseline_path = "evals/baselines/phase4-baseline.json"
baseline_prompt_snapshot_path = "evals/baselines/phase4-prompt-snapshot.json"
report_path = ".local/prisma/evals/regression.json"
```

Rules:

- All values are non-secret.
- Baseline paths point at committed repository files.
- `report_path` points under `.local/` so routine runs produce no diffs.
- No thresholds are enforced in Phase 5.
- No environment secrets are required.

## 13. Validation Commands

After Phase 5 implementation, these commands must pass:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy app evals
python -m pytest
python -m evals.runner
python -m evals.regression
```

Additional repository checks:

```bash
git diff --check
git status --short
```

Confirm that routine runs write `.local/prisma/evals/regression.json` and leave `evals/baselines/phase4-baseline.json`, `evals/baselines/phase4-prompt-snapshot.json`, and `evals/golden/cases.jsonl` unchanged.

## 14. Deliverables

Phase 5 deliverables:

- Stable prompt fingerprinting for the configured prompt asset.
- Committed Phase 4 prompt snapshot metadata.
- Prompt-regression report models.
- Regression comparison logic for baseline/current scorecards.
- Local regression runner invoked with `python -m evals.regression`.
- Generated regression report at `.local/prisma/evals/regression.json`.
- Non-secret `[prompt_regression]` configuration and typed settings.
- Correctness tests under `tests/regression/`.
- README and development-guide updates documenting the regression smoke path and baseline immutability policy.

## 15. Risks

### Baseline Drift

Risk: Routine regression runs mutate or replace the committed Phase 4 baseline.

Mitigation: Treat committed baselines as read-only inputs. Write reports only under `.local/`. Add tests that compare baseline file contents before and after report generation.

### Prompt Fingerprint Instability

Risk: Fingerprints include timestamps, absolute paths, or platform-specific metadata.

Mitigation: Hash only exact UTF-8 prompt bytes. Keep timestamps and paths as metadata outside the digest.

### Noisy Regressions

Risk: Small deterministic output changes create distracting reports.

Mitigation: Keep Phase 5 informational. Report exact structural deltas without failing the run.

### Accidental Baseline Overwrite

Risk: The regression runner writes generated output to a committed baseline path.

Mitigation: Validate configured report paths are under `.local/` and add tests that reject committed `evals/baselines/` report targets.

### Comparison Against Wrong Baseline

Risk: A report compares current output against an unrelated baseline.

Mitigation: Require `baseline_id`, `case_count`, metric names, and golden path compatibility checks before comparison.

### Hidden Prompt Changes

Risk: Prompt text changes without a visible fingerprint change in the report.

Mitigation: Include old and new prompt fingerprints in every report and make prompt fingerprint changes explicit in the console summary.

## 16. Success Criteria

Phase 5 is complete when:

- `python -m evals.regression` runs locally without internet access.
- A prompt fingerprint is generated for the configured prompt.
- The committed prompt snapshot records the baseline prompt fingerprint.
- A regression report is generated under `.local/prisma/evals/regression.json`.
- The Phase 4 baseline remains unchanged after routine regression runs.
- Repeated runs over the same prompt, baseline, code, and index produce deterministic comparison content, excluding run id and timestamp.
- The report identifies changed cases, improved metrics, regressed metrics, and unchanged metrics.
- The runner is informational and does not implement an approval/rejection gate.
- No CI gate is introduced.
- No GitHub Actions are introduced.
- No PromptFoo is introduced.
- No LLM judge is introduced.
- No hosted service is introduced.
- No Phase 6+ capability is introduced.

## 17. Recommended Next Natural Step

After Phase 5 is implemented and validated, the expected next phase is:

- **Phase 6 — Observability & Runtime Metrics.**

Phase 6 should make runtime behavior inspectable through structured logs, traces, latency, and cost-related metadata while preserving local-first execution. After Phase 6, Prisma will likely be mature enough to benefit from an engineering dashboard prototype that visualizes scorecards, regression reports, and runtime metrics. That dashboard should remain separate from Phase 5 and must not be folded into prompt regression.
