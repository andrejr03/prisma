# Phase 4 Evaluation Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task once approved.

**Goal:** Add a local, deterministic evaluation harness under `evals/` that exercises the existing `POST /query` behavior against a committed golden question set and produces a structured, reproducible scorecard.

**Architecture:** Phase 4 introduces `evals/` as a first-class top-level directory, parallel to `app/` and `tests/`. The harness loads golden cases, drives the existing API/service boundary case-by-case, applies deterministic metric functions to each response, and writes a scorecard artifact plus an aggregate pass rate. It adds no LLM-as-judge, no hosted services, no CI, and no dashboards.

**Tech Stack:** Python 3.11, Pydantic, FastAPI `TestClient` (in-process API boundary), pytest, ruff, mypy. No new runtime dependency is expected.

---

> Production LLM Engineering Platform
> Planning document only. This document defines what Phase 4 should implement. It does not implement code, create directories, or modify application files.

**Status:** Draft v0.1
**Date:** 2026-06-30
**Document:** PRISMA_PHASE_4_EVALUATION_HARNESS_PLAN_v0.1.md
**Audience:** developers, AI engineers, ML engineers, technical reviewers, and maintainers
**Companions:** [PRISMA_PROJECT_PLAN_v0.1.md](PRISMA_PROJECT_PLAN_v0.1.md), [PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md](PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md), [PRISMA_PHASE_1_INGESTION_INDEXING_PLAN_v0.1.md](PRISMA_PHASE_1_INGESTION_INDEXING_PLAN_v0.1.md), [PRISMA_PHASE_2_BASELINE_RAG_API_PLAN_v0.1.md](PRISMA_PHASE_2_BASELINE_RAG_API_PLAN_v0.1.md), [PRISMA_PHASE_3_AGENT_WORKFLOW_PLAN_v0.1.md](PRISMA_PHASE_3_AGENT_WORKFLOW_PLAN_v0.1.md), [ADR-0001](adr/ADR-0001-code-data-separation.md), [ADR-0002](adr/ADR-0002-provider-adapter-boundary.md), [ADR-0003](adr/ADR-0003-secrets-via-environment.md), [ADR-0004](adr/ADR-0004-evaluation-first-development.md)

---

## 1. Purpose

Phase 4 exists to give Prisma its first formal **evaluation harness**: a reproducible way to measure the behavior of the system through its public boundary instead of by inspection.

Phases 1 through 3 proved that Prisma can ingest and index a local corpus, retrieve relevant chunks, assemble bounded context, generate a deterministic grounded answer, validate citations, and orchestrate all of that through a bounded workflow. Those phases are verified by correctness tests, which prove the *code* does what it is written to do. They do not yet answer the operational question the project plan cares about most: *is the system's end-to-end behavior good, and did a change make it better or worse?*

This is the phase where Prisma stops being only a working RAG/workflow system and starts becoming a **measured** production LLM engineering platform. It is the project differentiator. The project plan states plainly that retrieval and generation are only part of the system and that the differentiator is the operational layer around them — evaluations first among them. ADR-0004 makes evaluation a first-class engineering concern and requires that every significant capability have a measurement story before it is considered complete. Phase 4 is where that measurement story becomes executable.

The goal is **not** a perfect benchmark, a leaderboard, or a research-grade metric suite. The goal is a small, reproducible, extensible evaluation foundation that later phases — Phase 5 prompt regression and Phase 7 CI gates — can build on without redesigning it.

## 2. Scope

### In Scope

- `evals/` as a first-class top-level directory, parallel to `app/` and `tests/`.
- A committed **golden question set** describing expected behavior for a small number of cases.
- Expected source/citation targets per case, pointing at real `datasets/sample_corpus/` paths.
- An **evaluation runner** that drives the existing `POST /query` behavior case-by-case.
- **Deterministic metrics** computed purely from the structured API response and the golden case.
- A generated **scorecard** output (JSON) summarizing per-case and aggregate results.
- A committed **baseline record** capturing the Phase 4 reference result.
- **Local execution** only, with no network access and no hosted services.
- **API-level evaluation** against existing behavior, through the public boundary, without importing workflow or retrieval internals unnecessarily.
- Correctness tests for the evaluation harness code itself, under `tests/evals/`.
- Non-secret evaluation configuration in `configs/defaults.toml`.
- README and `docs/DEVELOPMENT.md` updates for the eval smoke path.

### Explicit Non-Goals

- No LLM-as-judge or any model-graded metric.
- No RAGAS.
- No PromptFoo.
- No CI gate, no `.github/` workflows, no blocking automation.
- No prompt regression, prompt registry, or prompt versioning system.
- No online/production evaluation or feedback capture.
- No hosted services or external eval platforms.
- No dashboards or visualization UI.
- No model-provider comparison or multi-provider matrix.
- No cost regression or cost budgets.
- No production observability, persisted traces, or run database.
- No human annotation workflow.
- No large benchmark corpus or large case set.
- No dependency on internet access.
- No secrets, no `.env`, no `.env.example`.
- No `requirements.txt`, no Docker, no `scripts/` directory.

## 3. Architectural Alignment

### Project Plan

The project plan defines Phase 4 as the Evaluation Harness: golden question/answer dataset, metric definitions, eval runner, scorecard, and a recorded baseline. It also names the evaluation harness as the cheapest feature that delivers the project's core thesis — that LLM applications should be measured and gated like production software — and includes it in the MVP line (Phases 0 through 4 plus a thin Phase 7 slice). This plan implements exactly that slice and nothing beyond it. It deliberately omits Phase 5 prompt regression, Phase 6 observability/budgets, and Phase 7 CI automation.

### Repository Architecture

The repository architecture treats evaluation as a cross-cutting concern with clear separation between retrieval, reasoning, serving, and evaluation. Phase 4 honors that separation by placing all evaluation assets and code under a dedicated top-level `evals/` directory rather than inside `app/`. Evaluation is application-adjacent measurement, not application business logic, so it must not live in `app/`. The planned control flow is:

```text
evals.runner -> golden cases -> API boundary (POST /query) -> structured response -> deterministic metrics -> scorecard
```

### Phase 1

Phase 4 evaluates behavior that depends on the Phase 1 local Qdrant index, deterministic chunk identifiers, deterministic local embeddings, and the committed sample corpus. The runner assumes the index has been built (`python -m app.retrieval.index`) and reads only through the public query path. It does not change ingestion, chunking, indexing, or vector persistence, and it records a corpus/index fingerprint where available so a scorecard can be traced to the data it measured.

### Phase 2

Phase 4 treats the Phase 2 `POST /query` request and response contract as the measurement surface. Metrics read only documented response fields — `answer`, `citations`, `retrieved_context`, `metadata`, and `workflow` — and must not depend on private internals. The endpoint, request schema, and response schema remain unchanged by Phase 4.

### Phase 3

Phase 4 measures the Phase 3 bounded workflow through the same boundary. The `workflow` metadata object (`status`, `retrieval_attempts`, `max_retrieval_attempts`, `route`, `rewritten_query`, `context_sufficient`) makes workflow behavior observable and therefore measurable. Phase 4 reads this metadata for workflow metrics but does not modify `app/workflow/` or change any transition, bound, or routing rule.

### ADR-0001: Code / Data Separation

Evaluation logic (runner, metrics, models, reporting) is code and lives under `evals/`. Golden cases and committed baselines are declarative data and live under `evals/golden/` and `evals/baselines/`. Configuration stays declarative in `configs/defaults.toml`. No metric thresholds or case data are hard-coded into application logic, and no evaluation logic is placed into datasets, prompts, or configuration.

### ADR-0002: Provider Adapter Boundary

The harness never imports a provider SDK and never assumes provider-specific response objects. It evaluates the system through the provider-neutral public API, so the same harness would work against any provider configured behind the existing adapter boundary. Phase 4 introduces no provider comparison.

### ADR-0003: Secrets via Environment

Phase 4 requires no secrets. All evaluation configuration is non-secret: golden path, scorecard path, baseline path, and a minimum pass rate. No `.env` or `.env.example` is introduced, and golden cases must contain no personal or private data.

### ADR-0004: Evaluation-First Development

Phase 4 is the direct realization of ADR-0004. It measures the system through its public boundary, keeps evaluation assets as part of the durable engineering record, and ensures evaluation does not become hidden business logic by keeping it out of `app/`. The committed baseline establishes the reference point against which future regression (Phase 5) and gating (Phase 7) will be judged.

## 4. Evaluation Philosophy

The harness is governed by these principles:

- **Deterministic first.** Every Phase 4 metric is computable from the structured response and the golden case with no randomness and no model judgment. Re-running the harness on the same index and code yields the same per-case results.
- **Local-first.** The harness runs entirely on a laptop with no hosted services and no network access. It depends only on the local index and the in-process API.
- **Reproducible.** Same inputs (corpus, index, code, golden set) produce the same scorecard content, modulo the run id and timestamp. A corpus/index fingerprint ties a scorecard to the data it measured.
- **API-boundary evaluation.** Evaluation drives the system through `POST /query`, the same surface a real client uses. It does not reach into retrieval, workflow, or generation internals to manufacture a result.
- **No hidden state.** The harness reads committed golden cases and config; it does not depend on uncommitted local files to produce a meaningful run, and it never silently mutates committed baselines.
- **Evals measure behavior; tests verify code.** `tests/` proves the code is correct. `evals/` measures whether the end-to-end behavior is good. The two are kept distinct: eval metrics never live in `tests/`, and correctness assertions never masquerade as evaluation scores.
- **Scorecards are generated artifacts unless explicitly committed as baselines.** A routine run writes a scorecard to an ignored local path. Only a deliberately promoted baseline is committed to the repository.

## 5. Evaluation Dataset Strategy

The golden dataset is a small, hand-authored set of cases describing expected behavior over the committed sample corpus.

- **Number of cases:** start with **6 to 10** cases. This is intentionally small — enough to cover the corpus and the main behaviors (good retrieval, multi-source answers, and at least one expected `no_context` case), but small enough to author and review carefully. It is not a benchmark.
- **Storage and format:** committed under `evals/golden/` as a single JSON Lines file, `evals/golden/cases.jsonl`, one case object per line. JSONL keeps cases diff-friendly and append-friendly.
- **No personal or private data.** Questions and expected values reference only the public sample corpus already committed under `datasets/sample_corpus/`.

### Case Schema

Each line is one case object:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | Stable, unique case identifier (e.g. `provider-boundaries-basic`). |
| `question` | string | yes | The question sent to `POST /query`. |
| `expected_source_paths` | string[] | yes | Source paths that should appear in retrieval/citations, e.g. `datasets/sample_corpus/provider-boundaries.md`. |
| `expected_keywords` | string[] | yes | Lowercased terms/claims expected to appear in the answer text. |
| `min_citations` | int | yes | Minimum number of citations a valid answer must include. For a `no_context` case this is `0`. |
| `expected_workflow_status` | string \| null | no | Optional expected `workflow.status` (e.g. `completed` or `no_context`). `null`/absent means unconstrained. |
| `expects_no_context` | bool | no | Optional. When `true`, the case asserts a structured `no_context` outcome rather than an answer. |
| `notes` | string | no | Optional human note explaining the case's intent. |

### Example Cases

```jsonl
{"id": "provider-boundaries-basic", "question": "What does Prisma mean by provider boundaries?", "expected_source_paths": ["datasets/sample_corpus/provider-boundaries.md"], "expected_keywords": ["provider", "adapter"], "min_citations": 1, "expected_workflow_status": "completed"}
{"id": "evaluation-discipline-grounded", "question": "How does Prisma approach evaluation discipline?", "expected_source_paths": ["datasets/sample_corpus/evaluation-discipline.md"], "expected_keywords": ["evaluation", "baseline"], "min_citations": 1, "expected_workflow_status": "completed"}
{"id": "local-first-setup", "question": "Why is Prisma local-first?", "expected_source_paths": ["datasets/sample_corpus/local-first-development.md"], "expected_keywords": ["local", "reproducible"], "min_citations": 1, "expected_workflow_status": "completed"}
{"id": "out-of-corpus-no-context", "question": "What is the airspeed velocity of an unladen swallow?", "expected_source_paths": [], "expected_keywords": [], "min_citations": 0, "expects_no_context": true, "expected_workflow_status": "no_context"}
```

### Minimum Citation Requirements

- A case expecting an answer must set `min_citations >= 1`, and every citation in the response must reference an item that exists in `retrieved_context` (an unsupported-citation check, see §6).
- A case expecting `no_context` must set `min_citations: 0` and `expects_no_context: true`, and is satisfied by a structured `no_context` error rather than an answer.

## 6. Metrics

All Phase 4 metrics are **deterministic** and computed from the structured `POST /query` response (or structured error) plus the golden case. **No LLM-based grading is introduced.** Each metric is a pure function returning a pass/fail boolean plus optional counts and a failure reason.

| Metric | Definition | Pass condition |
|---|---|---|
| `retrieval_source_hit` | Did retrieval surface the expected source(s)? | Every path in `expected_source_paths` appears in at least one `retrieved_context[].source_path`. |
| `citation_source_hit` | Did the cited sources include the expected source(s)? | Every path in `expected_source_paths` appears in at least one `citations[].source_path`. |
| `citation_validity` | Are all citations well-formed and grounded? | Every `citations[].citation_id` maps to a `retrieved_context[]` item with the same `citation_id`, and required citation fields are present. |
| `answer_contains_expected_terms` | Does the answer contain the expected terms? | Every term in `expected_keywords` appears (case-insensitive substring) in `answer`. |
| `no_unsupported_citations` | Does the answer avoid citing anything not retrieved? | No `citations[].citation_id` is absent from `retrieved_context[]`, and no in-answer citation marker references an id not present in `citations`. |
| `workflow_completed` | Did the workflow reach the expected terminal status? | `workflow.status` equals `expected_workflow_status` when specified; for answer cases it must be `completed`. |
| `workflow_retry_bounded` | Did the workflow stay within its retrieval bound? | `1 <= workflow.retrieval_attempts <= workflow.max_retrieval_attempts` and `workflow.max_retrieval_attempts == 2`. |
| `structured_response_validity` | Is the response shape contract-valid? | The response validates against the documented `QueryResponse` (or `ErrorResponse`) schema, including `min_citations`. |

Notes:

- For `expects_no_context` cases, the response is a structured `no_context` error. Source/citation/keyword metrics are reported as **not-applicable** (recorded, not counted as failures), while `workflow_completed` (expecting `no_context`) and `structured_response_validity` (against `ErrorResponse`) still apply.
- Metrics are independent. One failing metric does not short-circuit the others; the case records every metric result so failure reasons are complete.
- Metrics must read only documented response fields. They must not import `app.workflow`, `app.retrieval`, or `app.generation` internals to recompute behavior.

## 7. Scorecard

A run produces one scorecard object, written as JSON.

### Format

```json
{
  "run_id": "20260630T214500Z-ab12cd",
  "timestamp": "2026-06-30T21:45:00Z",
  "index_fingerprint": "sha256:<manifest-or-index-hash-or-null>",
  "case_count": 8,
  "metrics": {
    "retrieval_source_hit": {"pass": 7, "fail": 1, "not_applicable": 0},
    "citation_source_hit": {"pass": 7, "fail": 0, "not_applicable": 1},
    "citation_validity": {"pass": 8, "fail": 0, "not_applicable": 0},
    "answer_contains_expected_terms": {"pass": 6, "fail": 1, "not_applicable": 1},
    "no_unsupported_citations": {"pass": 8, "fail": 0, "not_applicable": 0},
    "workflow_completed": {"pass": 8, "fail": 0, "not_applicable": 0},
    "workflow_retry_bounded": {"pass": 8, "fail": 0, "not_applicable": 0},
    "structured_response_validity": {"pass": 8, "fail": 0, "not_applicable": 0}
  },
  "cases": [
    {
      "id": "provider-boundaries-basic",
      "passed": true,
      "metrics": {
        "retrieval_source_hit": {"status": "pass"},
        "answer_contains_expected_terms": {"status": "pass"}
      },
      "failure_reasons": [],
      "latency_ms": 42
    },
    {
      "id": "evaluation-discipline-grounded",
      "passed": false,
      "metrics": {
        "answer_contains_expected_terms": {"status": "fail"}
      },
      "failure_reasons": ["answer_contains_expected_terms: missing expected term 'baseline'"]
    }
  ],
  "aggregate": {
    "cases_passed": 7,
    "cases_failed": 1,
    "pass_rate": 0.875,
    "minimum_pass_rate": 0.8,
    "meets_minimum": true
  }
}
```

### Fields

- `run_id`: unique per run (timestamp plus short random/hash suffix).
- `timestamp`: UTC ISO-8601 run start.
- `index_fingerprint`: corpus/index fingerprint if available (e.g. a hash of the Phase 1 manifest), else `null`.
- `case_count`: number of golden cases evaluated.
- `metrics`: per-metric pass/fail/not-applicable counts.
- `cases`: per-case results — `id`, overall `passed`, per-metric statuses, `failure_reasons`, and optional `latency_ms` runtime metadata where practical.
- `aggregate`: `cases_passed`, `cases_failed`, `pass_rate`, configured `minimum_pass_rate`, and `meets_minimum`.

### What Is Committed vs Generated

- **Generated (not committed):** routine scorecards, written to the ignored local path `.local/prisma/evals/scorecard.json`. The existing `.gitignore` already ignores `.local/` and `scorecards/`, so routine runs produce no noisy diffs.
- **Committed (only when promoted):** the baseline summary under `evals/baselines/` (see §8). A scorecard becomes part of the durable record only by deliberate promotion, never automatically.

## 8. Baseline Policy

**Recommended policy:** commit **golden cases plus an initial committed baseline summary**, and keep routine scorecards generated and locally ignored.

Rationale:

- Committing **golden cases only** would satisfy the dataset requirement but leave ADR-0004's "recorded baseline" unfulfilled and give Phase 5/Phase 7 no reference point.
- Committing **generated scorecards on every run** would create constant noisy diffs and risk the scorecard drifting into hidden state — directly against §4.
- Committing **golden cases plus one promoted baseline** records the reference result for review, satisfies the project plan's "recorded baseline" deliverable, and keeps day-to-day runs diff-free.

Concretely:

- `evals/golden/cases.jsonl` is committed.
- `evals/baselines/phase4-baseline.json` is committed once, holding the aggregate summary and per-metric counts for the agreed reference run. It is a deliberately promoted artifact, regenerated and re-committed only when the team consciously moves the baseline.
- All other scorecards are written to `.local/prisma/evals/scorecard.json` and are git-ignored.
- The baseline file should exclude volatile fields (or hold them informationally only): `run_id` and `timestamp` are not used for comparison logic in Phase 4. Phase 4 does **not** implement automated baseline comparison or gating — that is Phase 5/Phase 7. Phase 4 only *records* the baseline.

## 9. Evaluation Runner

The runner is a module invoked as:

```bash
python -m evals.runner
```

Behavior:

1. Load evaluation configuration from `configs/defaults.toml` (`[evals]`).
2. Load and validate golden cases from `evals/golden/cases.jsonl`.
3. For each case, send the question to the existing API through an in-process FastAPI `TestClient` bound to `app.api.main:app` — the same public boundary a real client uses.
4. Apply each deterministic metric to the structured response and the golden case.
5. Assemble per-case results, per-metric counts, and the aggregate pass rate.
6. Write the scorecard to the configured (ignored) scorecard path and print a concise human summary.
7. Exit `0` on a successful run. Phase 4's runner does **not** fail the process on a low pass rate — gating is out of scope; `minimum_pass_rate` is recorded and surfaced, not enforced as an exit code.

Why the runner belongs in `evals/`, not `app/` or `tests/`:

- It is measurement, not application business logic, so it must not live in `app/` (ADR-0001, ADR-0004: evaluation must not become hidden business logic).
- It is a generated-artifact-producing driver, not a pass/fail unit test of code; keeping it out of `tests/` preserves the §4 distinction "evals measure behavior, tests verify code." (`tests/evals/` tests the harness code itself — see §11 — but the *runner* that drives the system lives in `evals/`.)

How it calls the boundary without importing internals:

- It depends on `app.api.main:app` (the assembled FastAPI app) via `TestClient` and reads only the documented response JSON.
- It imports `app` Pydantic response models (e.g. `QueryResponse`, `ErrorResponse`) **only** for `structured_response_validity` schema validation — a read of the public contract, not of workflow/retrieval/generation internals.
- It does not import `app.workflow`, `app.retrieval`, or `app.generation` to recompute or shortcut behavior.

## 10. Repository Changes

Phase 4 should create or modify only the paths listed here.

### Create Directories

```text
evals/
evals/golden/
evals/baselines/
tests/evals/
```

Do not create `.github/`, `docker/`, `scripts/`, UI directories, dashboard directories, or prompt-regression directories.

### Create Files

```text
evals/__init__.py
evals/models.py
evals/metrics.py
evals/runner.py
evals/reporting.py
evals/golden/cases.jsonl
evals/baselines/phase4-baseline.json
tests/evals/__init__.py
tests/evals/test_models.py
tests/evals/test_metrics.py
tests/evals/test_runner.py
```

Responsibilities:

- `evals/models.py`: Pydantic models for a golden case, a per-case result, per-metric results, and the scorecard. Includes loading/validation of `cases.jsonl` and rejection of malformed cases.
- `evals/metrics.py`: the deterministic metric functions from §6. Pure functions over `(response, case)`; no model calls, no I/O.
- `evals/runner.py`: orchestration described in §9 — load config, load cases, drive the API boundary, apply metrics, build and write the scorecard, print the summary, expose `python -m evals.runner`.
- `evals/reporting.py`: scorecard assembly, JSON serialization to the configured path, and the human-readable console summary.
- `evals/golden/cases.jsonl`: the committed golden case set (§5).
- `evals/baselines/phase4-baseline.json`: the committed baseline summary (§8).
- `tests/evals/*`: correctness tests for the harness code (§11).

### Modify Existing Files

```text
configs/defaults.toml
app/config.py
README.md
docs/DEVELOPMENT.md
```

Required modifications:

- `configs/defaults.toml`: add the `[evals]` section (§12).
- `app/config.py`: add typed, non-secret evals settings with validation (paths as strings, `0.0 <= minimum_pass_rate <= 1.0`).
- `README.md` and `docs/DEVELOPMENT.md`: document the eval smoke path and the baseline policy.

### Do Not Create or Modify

```text
.github/
docker/
scripts/
.env
.env.example
requirements.txt
app/workflow/
app/retrieval/
app/generation/
app/api/
```

No new runtime dependency is expected for Phase 4. Do not add RAGAS, PromptFoo, an LLM-judge client, or any hosted-eval dependency.

## 11. Testing Strategy

These are correctness tests for the **evaluation harness code itself**. They verify that the harness behaves correctly; they are **not** a substitute for running the harness, and they must not assert end-to-end answer quality (that is what an eval *run* measures).

Required tests:

- **Golden cases load:** a well-formed `cases.jsonl` loads into typed case models with expected field values.
- **Malformed cases are rejected:** a case missing a required field, or with a wrong-typed field, raises a clear validation error rather than silently passing.
- **Metric functions behave correctly:** each metric in §6 has unit tests over hand-built `(response, case)` fixtures covering a passing case, a failing case, and (where relevant) a not-applicable case — using synthetic response dicts, no live index required.
- **Runner produces a scorecard:** the runner, driven over a small in-memory or fixture case set, returns a scorecard object with per-case results, per-metric counts, and an aggregate pass rate.
- **Failure reasons are recorded:** a deliberately failing case yields a non-empty `failure_reasons` entry naming the failing metric.
- **Generated artifacts are ignored:** the default scorecard path resolves under the git-ignored `.local/` tree, and the test confirms the runner does not write into committed `evals/` paths.

Recommended test files:

```text
tests/evals/test_models.py
tests/evals/test_metrics.py
tests/evals/test_runner.py
```

Tests that need a live response should use fixture response dictionaries or a minimal `TestClient` call against the in-process app with a temporary index, consistent with the Phase 1–3 test setup that builds an index via `run_indexing()`. Pure metric and model tests must not require Qdrant.

## 12. Configuration

Phase 4 adds a non-secret `[evals]` section to `configs/defaults.toml`:

```toml
[evals]
golden_path = "evals/golden/cases.jsonl"
scorecard_path = ".local/prisma/evals/scorecard.json"
baseline_path = "evals/baselines/phase4-baseline.json"
minimum_pass_rate = 0.8
```

Configuration rules:

- All values are non-secret. No secrets, no `.env`, no `.env.example`.
- `golden_path` and `baseline_path` point at committed repository paths.
- `scorecard_path` points under the git-ignored `.local/` tree so routine runs produce no diffs.
- `minimum_pass_rate` is in `[0.0, 1.0]` and is **recorded and surfaced** in Phase 4, not enforced as a gate. Enforcement is deferred to Phase 7.

## 13. Validation Commands

After Phase 4 implementation, these commands must pass:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy app evals
python -m pytest
python -m app.retrieval.index
python -m evals.runner
```

Eval smoke expectation: `python -m evals.runner` builds/uses the local index path, evaluates the committed golden cases, prints an aggregate summary, and writes a scorecard to `.local/prisma/evals/scorecard.json` without error.

Forbidden path checks (Phase 4 must not introduce CI/Docker/hosted/secret infrastructure):

```bash
test ! -d .github
test ! -d docker
test ! -d scripts
test ! -f .env
test ! -f .env.example
test ! -f requirements.txt
```

Additional repository checks:

```bash
git diff --check
git status --short
```

Confirm that routine runs leave `evals/golden/` and `evals/baselines/` unchanged and write only to the ignored scorecard path.

## 14. Deliverables

Phase 4 deliverables:

- `evals/` as a first-class top-level directory with `golden/` and `baselines/` subdirectories.
- A committed golden question set (`evals/golden/cases.jsonl`) of 6–10 deterministic cases referencing the real sample corpus.
- Deterministic metric functions (`evals/metrics.py`) implementing the §6 metric set, with no LLM grading.
- Typed evaluation models and case loading/validation (`evals/models.py`).
- An evaluation runner (`evals/runner.py`) invoked via `python -m evals.runner`, driving `POST /query` through the in-process API boundary.
- Scorecard assembly and reporting (`evals/reporting.py`) writing JSON to the ignored local path plus a console summary.
- A committed baseline summary (`evals/baselines/phase4-baseline.json`) recording the Phase 4 reference run.
- Non-secret `[evals]` configuration and typed settings.
- Correctness tests for the harness under `tests/evals/`.
- README and development-guide updates documenting the eval smoke path and baseline policy.

## 15. Risks

### Evals Becoming Brittle

Risk: Substring keyword matching and exact source-path matching can break on benign wording or path changes.

Mitigation: Keep the golden set small and reviewable, use a few robust expected keywords per case rather than long phrases, and treat metrics as behavioral guardrails, not exact-string contracts. Author at least one `no_context` case so the set covers more than the happy path.

### Testing Confused with Evaluation

Risk: `tests/evals/` could drift into asserting answer quality, or eval metrics could migrate into `tests/`.

Mitigation: Enforce the §4 split — `tests/` verifies harness code over fixtures; `evals/` measures behavior over the live boundary. Keep metric logic out of `tests/` and keep quality assertions out of `tests/evals/`.

### Overfitting to the Sample Corpus

Risk: Golden cases tuned to the current sample corpus may make metrics look good without measuring anything general.

Mitigation: Document that the Phase 4 set is a foundation, not a benchmark; keep cases tied to durable corpus claims; and design the schema so cases extend cleanly when the corpus grows.

### Meaningless Metrics

Risk: Metrics that almost always pass (or always fail) provide no signal.

Mitigation: Include at least one case expected to stress retrieval/grounding (e.g. the `no_context` case), and review the baseline to confirm metrics discriminate between good and bad behavior.

### Committing Noisy Scorecards

Risk: Generated scorecards committed on every run create churn and risk hidden state.

Mitigation: Write routine scorecards to the git-ignored `.local/` path; commit only the deliberately promoted baseline (§8). The existing `.gitignore` already ignores `.local/` and `scorecards/`.

### Hidden Dependency on Local Generated State

Risk: The harness could come to depend on uncommitted local files to produce a meaningful run.

Mitigation: Drive everything from committed golden cases and config; treat the scorecard as output only; never read a prior scorecard to influence a new run in Phase 4.

### Evaluation Scope Creep

Risk: Pressure to add LLM-judge, RAGAS, PromptFoo, CI gating, dashboards, or provider comparison during Phase 4.

Mitigation: Hold the §2 non-goals firm. Each of those belongs to a later phase or a future extension and must not be smuggled into the Phase 4 foundation.

## 16. Success Criteria

Phase 4 is complete when:

- The eval runner works locally via `python -m evals.runner` with no network access.
- Golden cases are committed under `evals/golden/cases.jsonl`.
- A deterministic scorecard is generated to the ignored local path and re-running on the same index/code yields the same per-case results.
- The metric set is documented and implemented as deterministic functions (§6).
- The baseline policy is implemented: golden cases committed, one baseline summary committed, routine scorecards ignored.
- Harness correctness tests pass under `tests/evals/`, and the full `pytest`/`ruff`/`mypy` suite passes.
- No LLM judge is introduced.
- No CI gate is introduced.
- No prompt regression is introduced.
- The existing `POST /query` API, request schema, and response schema remain unchanged.
- No Phase 5+ capability (prompt regression, observability/budgets, CI, Docker, hosted services, provider comparison, dashboards, human annotation) is introduced.

## 17. Recommended Next Natural Step

Review this Phase 4 plan against the approved project plan, repository architecture, and ADRs. After approval, implement Phase 4 Evaluation Harness as one focused development slice.

Expected next phase after implementation:

- **Phase 5 — Prompt Regression.** With a committed baseline and deterministic scorecard in place, Phase 5 can version prompt artifacts and compare runs against the recorded baseline to make prompt changes safe and reviewable.

Additional note: after Phase 4 is implemented and validated, it may be the right time to ask Claude Design for an engineering **dashboard prototype** that visualizes scorecards and per-metric trends. This would remain a separate, optional, non-MVP exploration and must not be folded into the Phase 4 scope.
