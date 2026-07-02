# Phase 6 Observability & Runtime Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task once approved.

**Goal:** Add local, deterministic runtime observability so that each Prisma `POST /query` request is inspectable through structured runtime events and a request-local runtime metrics summary, without introducing telemetry, tracing vendors, dashboards, or CI gates.

**Architecture:** Phase 6 adds a new `app/observability/` boundary that records request-local events and timings while the existing RAG service and workflow runner execute, aggregates them into a deterministic runtime metrics model, optionally exposes a compact `runtime` block on the `QueryResponse`, and writes generated JSON runtime artifacts under `.local/`. Observability is measurement-only: it never changes request behavior, retrieval, generation, citations, or evaluation pass/fail logic.

**Tech Stack:** Python 3.11, Pydantic, standard-library `time`/`uuid`/`json`, existing Phase 2 API models and Phase 3 workflow runner, pytest, ruff, mypy. No new runtime dependency is expected.

---

> Production LLM Engineering Platform  
> Planning document only. This document defines what Phase 6 should implement. It does not implement code, create directories, or modify application files.

**Status:** Draft v0.1  
**Date:** 2026-07-01  
**Document:** PRISMA_PHASE_6_OBSERVABILITY_RUNTIME_METRICS_PLAN_v0.1.md  
**Audience:** developers, AI engineers, ML engineers, technical reviewers, and maintainers  
**Companions:** [PRISMA_PROJECT_PLAN_v0.1.md](PRISMA_PROJECT_PLAN_v0.1.md), [PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md](PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md), [PRISMA_PHASE_2_BASELINE_RAG_API_PLAN_v0.1.md](PRISMA_PHASE_2_BASELINE_RAG_API_PLAN_v0.1.md), [PRISMA_PHASE_3_AGENT_WORKFLOW_PLAN_v0.1.md](PRISMA_PHASE_3_AGENT_WORKFLOW_PLAN_v0.1.md), [PRISMA_PHASE_4_EVALUATION_HARNESS_PLAN_v0.1.md](PRISMA_PHASE_4_EVALUATION_HARNESS_PLAN_v0.1.md), [PRISMA_PHASE_5_PROMPT_REGRESSION_PLAN_v0.1.md](PRISMA_PHASE_5_PROMPT_REGRESSION_PLAN_v0.1.md), [ADR-0001](adr/ADR-0001-code-data-separation.md), [ADR-0002](adr/ADR-0002-provider-adapter-boundary.md), [ADR-0003](adr/ADR-0003-secrets-via-environment.md), [ADR-0004](adr/ADR-0004-evaluation-first-development.md), [AGENTS.md](../AGENTS.md)

---

## 1. Purpose

Phase 6 exists to make each Prisma request inspectable through structured runtime metadata.

Through Phase 5, Prisma became measurable but not observable. Phases 2–3 produced a bounded RAG request with workflow metadata, Phase 4 produced a committed evaluation baseline, and Phase 5 produced deterministic prompt regression against that baseline. None of these phases explain *how a single request behaved at runtime*: how long retrieval took, how many retrieval attempts occurred, how much context was assembled, or which backend produced the answer.

Phase 6 answers request-level engineering questions such as:

- How long did this request take end to end?
- Where was the time spent — retrieval, context assembly, generation, or validation?
- How many retrieval attempts did the bounded workflow use?
- Which source paths were retrieved, and how many citations were produced?
- Which local generation backend and model id served the request?
- Did the request complete or fail, and with what error status?

This phase is an engineering-visibility control. It is **not** production telemetry, application performance monitoring, distributed tracing, or cost billing. It records what already happened during a local request and exposes it as a generated artifact.

**How it supports future CI/CD and dashboard work.** Phase 6 establishes a stable, provider-neutral runtime metrics shape written to local artifacts. A future **Phase 7 — CI/CD Evaluation Gate** can consume evaluation and regression outputs without needing to invent runtime measurement. Separately, once Phase 6 is validated, the runtime metrics shape becomes a data source that a later engineering dashboard prototype can visualize alongside scorecards and regression reports. Phase 6 deliberately produces the *data*, not the gate and not the dashboard.

## 2. Scope

### In Scope

- Structured, request-local runtime events captured during a single `POST /query` request.
- A deterministic runtime metrics model aggregated per request.
- Per-request latency timings for retrieval, context assembly, generation, and validation stages.
- An optional, additive `runtime` block on the existing `QueryResponse` (backward-compatible; see §8).
- A generated local runtime report written under `.local/`.
- A local inspection module invoked as `python -m app.observability.inspect`.
- Correctness tests for event capture, timing, metrics aggregation, artifact writing, inspection output, and API backward compatibility.
- Non-secret observability configuration in `configs/defaults.toml` and typed settings in `app/config.py`.
- README and `docs/DEVELOPMENT.md` updates documenting the local observability smoke path and generated-artifact policy.

### Explicit Non-Goals

- No OpenTelemetry.
- No LangSmith.
- No hosted observability.
- No production tracing.
- No dashboards.
- No cost billing integrations.
- No real token billing or provider usage/cost accounting.
- No CI gates.
- No persistent database traces or SQLite trace store.
- No user analytics.
- No telemetry upload.
- No external monitoring or external endpoints.
- No changes to retrieval, workflow, generation, citation, or evaluation *behavior*.
- No Phase 7+ capability.

## 3. Architectural Alignment

### Project Plan

The project plan defines Phase 6 as Observability & Runtime Metrics: make runtime behavior inspectable through structured metadata while preserving local-first execution. This plan implements that slice only. It deliberately excludes tracing vendors, hosted observability, cost budgets, dashboards, and CI gates, all of which belong to later work or to separate design efforts.

### Repository Architecture

Observability logic lives in a new `app/observability/` package because it instruments application request handling. It is code, not data. Generated runtime reports are runtime artifacts under `.local/` and are never committed, consistent with how Phase 4 scorecards and Phase 5 regression reports are treated. The planned flow is:

```text
POST /query
  -> RagService / RagWorkflowRunner (unchanged behavior)
  -> observability records events + stage timings
  -> runtime metrics aggregated per request
  -> optional additive `runtime` block on QueryResponse
  -> .local/prisma/runtime/latest-request.json
  -> .local/prisma/runtime/requests/<request_id>.json
```

### Phase 3 Workflow

The Phase 3 bounded workflow already exposes request-local `WorkflowMetadata` (`status`, `retrieval_attempts`, `max_retrieval_attempts`, `route`, `rewritten_query`, `context_sufficient`) on every `QueryResponse`. Phase 6 measures around that workflow; it reads workflow route and retrieval-attempt information rather than re-deriving it, and it must not change the bounded retry semantics (`max_retrieval_attempts == 2`).

### Phase 4 Evaluation Harness

Phase 4 metrics and scorecards remain the authority for pass/fail. Phase 6 runtime metrics are informational and must not feed evaluation pass/fail logic. Where useful, runtime metrics may be surfaced *alongside* scorecard entries as non-scoring context (see §10), but the set of Phase 4 metrics and their thresholds is unchanged.

### Phase 5 Prompt Regression

Phase 5 comparison logic and the committed Phase 4 baseline remain untouched. Runtime metrics may appear as informational fields in regression reporting output, but they must not participate in regression deltas or change the `baseline_unavailable` / comparison rules already defined in Phase 5.

### ADR-0001: Code / Data Separation

Observability code lives under `app/observability/`. Generated runtime artifacts are data under `.local/` and are never committed. Configuration remains declarative under `configs/`. No runtime artifact may contain executable logic, and no committed runtime state is introduced.

### ADR-0002: Provider Adapter Boundary

Runtime metrics are derived from provider-neutral values already available to application code (backend name, model id string, char/sentence counts, elapsed wall-clock time). Observability must not import provider SDKs, read provider-specific response objects, or record provider usage/cost fields. "Local generation backend metadata" means the neutral `backend` and `model_id` strings already carried by `ResponseMetadata`.

### ADR-0003: Secrets via Environment

Phase 6 requires no secrets. Request ids, timings, counts, backend names, model ids, and file paths are non-secret. No `.env`, `.env.example`, external endpoint, credential, or token is introduced.

### ADR-0004: Evaluation-First Development

Observability is measurement without judgment. It records what happened but does not decide correctness. Evaluation-first development is preserved because Phase 4/5 remain the authority on quality; Phase 6 only adds visibility.

### AGENTS.md

This plan respects AGENTS.md scope control (§5): no unapproved dashboards, registries, CI, Docker, hosted integrations, or provider comparisons; provider neutrality (§9); no secrets (§10); and local-first, deterministic, simplicity-first repository philosophy (§11). Public behavior documentation (`README.md`, `docs/DEVELOPMENT.md`) is updated in the same task per §7.

## 4. Observability Philosophy

- **Local-first.** All observability runs on the developer's machine against local artifacts. No network access is required.
- **No telemetry upload.** Nothing is transmitted to any external service, ever.
- **Deterministic where possible.** Counts, request structure, event ordering, stage names, and artifact schema are deterministic. Only wall-clock durations and timestamps are inherently non-deterministic; those are isolated so tests can assert everything else exactly.
- **Inspectable but minimal.** Capture the smallest set of events and metrics that answer real engineering questions. Do not build a general tracing framework.
- **Runtime metadata is a generated artifact.** Runtime reports are outputs, like scorecards and regression reports. They live under `.local/` and are never committed.
- **Measurement without changing behavior.** Instrumentation must not alter retrieval results, workflow routing, generation, citations, error handling, or response payload semantics for existing fields.
- **No vendor lock-in.** No OpenTelemetry, LangSmith, or any tracing/monitoring vendor. The model is plain Pydantic and standard-library timing so it can be swapped or extended later without migration.

## 5. Runtime Event Model

A runtime event is one structured record describing something that happened during a single request. Events are ordered and request-scoped.

Fields:

| Field | Type | Meaning |
|---|---|---|
| `request_id` | `str` | Stable id for the owning request (see §6/§7). Same across all events in a request. |
| `sequence` | `int` | Monotonic 0-based index establishing deterministic event order within the request. |
| `timestamp` | `str` | UTC ISO-8601 timestamp when the event was recorded. Metadata only; excluded from deterministic assertions. |
| `stage` | `str` | Stage name from a fixed, closed set (see below). |
| `status` | `str` | One of `started`, `completed`, `skipped`, `failed`. |
| `duration_ms` | `float \| None` | Elapsed milliseconds for a completed stage span; `None` for point/`started` events. |
| `details` | `dict[str, str \| int \| float \| bool]` | Small, non-secret, deterministic key/values (e.g. `retrieved_count`, `attempt`). No raw prompt text, no answer text, no question text. |
| `error_code` | `str \| None` | Stable error code when `status == "failed"` (e.g. `invalid_query`, `no_context`, `citation_invalid`); otherwise `None`. |

Captured events (fixed stage vocabulary, aligned to the existing request flow in `app/generation/service.py` and the Phase 3 workflow route):

- `request` — overall request span (`started` at entry, `completed`/`failed` at exit).
- `validate_query`
- `retrieve_context` — one event per retrieval attempt; `details.attempt` records the attempt number.
- `assemble_context`
- `generate_answer`
- `validate_citations`
- `finalize_response`

Clarifications:

- The event vocabulary is closed. Instrumentation must map to these stages rather than inventing free-form stage names per call site.
- Events never contain question text, prompt text, generated answer text, or full chunk text. Only counts, ids, paths, and small scalar details are allowed (see §16 leakage risk).
- Event order is deterministic; `sequence` (not `timestamp`) is the ordering key used in tests.

## 6. Runtime Metrics Model

The runtime metrics model is the per-request aggregate derived from the events and from values already computed during the request. All counts are deterministic proxies; there is **no real token billing**.

| Metric | Type | Definition |
|---|---|---|
| `request_id` | `str` | Owning request id. |
| `total_latency_ms` | `float` | Wall-clock duration of the `request` span. |
| `retrieval_latency_ms` | `float` | Sum of durations of all `retrieve_context` events. |
| `context_assembly_latency_ms` | `float` | Duration of the `assemble_context` stage. |
| `generation_latency_ms` | `float` | Duration of the `generate_answer` stage. |
| `validation_latency_ms` | `float` | Duration of the `validate_citations` stage. |
| `retrieval_attempts` | `int` | Number of retrieval attempts (equals workflow `retrieval_attempts`; `1` on the non-workflow path). |
| `retrieved_context_count` | `int` | Number of assembled context items used for generation. |
| `retrieved_source_paths` | `list[str]` | Distinct repository-relative source paths of retrieved context, in stable order. |
| `citation_count` | `int` | Number of citations in the final response. |
| `answer_char_count` | `int` | Character length of the generated answer. |
| `generated_answer_sentence_count` | `int` | Deterministic sentence count of the answer using the existing sentence-bounding convention. |
| `context_char_count` | `int` | Character length of the assembled context string. |
| `prompt_char_count` | `int` | Character length of the loaded prompt asset. |
| `workflow_route` | `list[str]` | Workflow route from `WorkflowMetadata.route`. |
| `generation_backend` | `str` | Neutral backend name from `ResponseMetadata.generation_backend`. |
| `generation_model_id` | `str` | Neutral model id from `ResponseMetadata.generation_model_id`. |
| `status` | `str` | `completed` or `failed`. |
| `error_code` | `str \| None` | Stable error code on failure; otherwise `None`. |

Rules:

- No real token counts, provider usage, or cost fields. `*_char_count` and `*_sentence_count` are deterministic local proxies only.
- Latency fields are the only non-deterministic values; every other field is deterministic given the same inputs, code, and index.
- Metrics are derived; they must not re-run retrieval or generation or otherwise change behavior.

## 7. Storage Strategy

Runtime artifacts are written under the existing local runtime state root (Phase 0 `paths.runtime_state`, i.e. `.local/prisma`), in a dedicated `runtime/` subtree:

```text
.local/prisma/runtime/latest-request.json
.local/prisma/runtime/requests/<request_id>.json
```

- `latest-request.json` always reflects the most recent request (overwritten each time).
- `requests/<request_id>.json` is one file per request, containing that request's events and metrics.
- `request_id` is a UUID4 hex string generated at request entry. It is used verbatim as the filename and validated to be filename-safe before any write.

Clarifications:

- Generated runtime artifacts are ignored, consistent with the existing `.local/` gitignore policy. Confirm `.local/` (or `.local/prisma/`) is git-ignored; if not already covered, extend `.gitignore` — no runtime file may be committed.
- **No committed runtime state.** The repository must contain zero request artifacts after a run.
- **No SQLite trace store yet.** A persistent trace database is explicitly out of scope and is not justified for local, single-request inspection. If persistence is ever needed it must be proposed in a future phase, not added here.
- **No production DB.** No database of any kind is introduced.
- Writes must be confined to the configured runtime directory; the writer must reject targets outside `.local/` (mirrors the Phase 5 report-path guard).

## 8. API Surface

The existing `POST /query` response (`QueryResponse` in [app/models/rag.py](../app/models/rag.py)) is extended with **one new optional, additive field** named `runtime`. All existing fields (`answer`, `citations`, `retrieved_context`, `metadata`, `workflow`) keep their exact names, types, and meaning.

The `runtime` block is a compact subset of the runtime metrics model — enough for inline inspection without duplicating the full artifact:

```json
"runtime": {
  "request_id": "…",
  "total_latency_ms": 42.0,
  "retrieval_latency_ms": 12.0,
  "context_assembly_latency_ms": 3.0,
  "generation_latency_ms": 8.0,
  "validation_latency_ms": 1.0,
  "retrieval_attempts": 1,
  "citation_count": 2
}
```

Rules:

- **Additive only.** No existing field is renamed, removed, retyped, or reordered. Existing response consumers continue to work unchanged.
- The `runtime` block is emitted when observability is enabled and is `null`/omitted when observability is disabled (`configs/defaults.toml` `[observability].enabled = false`), so the feature can be turned off without breaking the schema.
- Only latencies and a few deterministic counts appear inline. The full per-request metrics and event list live in the generated artifact (§7), not in the response.
- The `runtime` block never contains prompt, question, or answer text.

## 9. Local Inspection Command

A minimal inspection module reads the generated local artifacts and prints a concise, human-readable summary:

```bash
python -m app.observability.inspect
```

Behavior:

1. Load settings from `configs/defaults.toml`.
2. Resolve the runtime directory from `[observability].runtime_dir`.
3. Read `latest-request.json` by default, or a specific `requests/<request_id>.json` when a `--request-id <id>` argument is provided.
4. Print a concise summary: `request_id`, `status`, total and per-stage latencies, `retrieval_attempts`, `retrieved_context_count`, `citation_count`, `workflow_route`, and `generation_backend`/`generation_model_id`.
5. Exit `0` on success; exit non-zero with a clear message if no artifact exists yet (e.g. "no runtime artifact found; issue a request first").

Constraints:

- The command reads only; it never issues a request, mutates artifacts, or reaches the network.
- Implemented as a runnable module (`python -m app.observability.inspect`). **No `scripts/` directory** is created — a module command matches the existing `python -m evals.runner` / `python -m evals.regression` convention and is sufficient.

## 10. Evaluation and Regression Integration

Runtime metrics are **informational only** in Phase 6 and must not change evaluation or regression pass/fail logic.

- **Eval scorecards.** Phase 4 scorecard entries may optionally carry a non-scoring `runtime` block (or the eval runner may print a runtime summary line) so an engineer can see latency and counts next to case results. This is display/context only; the set of Phase 4 metrics and thresholds is unchanged, and pass/fail is computed exactly as before.
- **Prompt regression reports.** Phase 5 regression output may optionally surface runtime metrics as informational fields. Runtime values must not participate in regression deltas, must not affect `overall_pass_rate_delta`, and must not change the `baseline_unavailable` comparison rules.

If wiring runtime metrics into eval/regression output adds meaningful complexity or risk, prefer to keep Phase 6 self-contained (artifact + inline `runtime` block only) and defer eval/regression display to a later phase. The integration is optional; the runtime artifact and inspection command are the required deliverables.

## 11. Repository Changes

Phase 6 should create or modify only the paths listed here.

### Create Files

```text
app/observability/__init__.py
app/observability/models.py
app/observability/timing.py
app/observability/runtime.py
app/observability/inspect.py
tests/observability/__init__.py
tests/observability/test_runtime_metrics.py
tests/observability/test_inspect.py
tests/observability/test_api_runtime.py
```

### Modify Existing Files

```text
configs/defaults.toml
app/config.py
app/models/rag.py
app/generation/service.py
app/workflow/runner.py
.gitignore
README.md
docs/DEVELOPMENT.md
```

Required responsibilities:

- `app/observability/models.py`: Pydantic models for `RuntimeEvent`, `RuntimeMetrics`, and the compact `RuntimeSummary` block used on `QueryResponse`.
- `app/observability/timing.py`: deterministic-friendly stage timing helper (a context-manager/span recorder) built on `time.perf_counter`, isolating the only non-deterministic values.
- `app/observability/runtime.py`: a request-scoped `RuntimeRecorder` that collects events, aggregates the runtime metrics, builds the summary block, and writes the `latest-request.json` and `requests/<request_id>.json` artifacts.
- `app/observability/inspect.py`: the `python -m app.observability.inspect` reader/summary command (§9).
- `tests/observability/*`: correctness tests (§13).
- `configs/defaults.toml`: add `[observability]` (§12).
- `app/config.py`: add typed, non-secret `ObservabilitySettings` and wire it into `PrismaSettings` following the existing dataclass/`load_settings` pattern.
- `app/models/rag.py`: add the optional additive `runtime` field to `QueryResponse` (§8).
- `app/generation/service.py` and `app/workflow/runner.py`: thread a `RuntimeRecorder` through the existing request paths to record events/timings and populate the runtime metrics **without changing behavior**.
- `.gitignore`: ensure `.local/` runtime artifacts are ignored (only if not already covered).
- `README.md` and `docs/DEVELOPMENT.md`: document the observability smoke path, the `runtime` response block, and the generated-artifact policy.

Do not create `app/observability/observability/` or any package where a single module command suffices. Do not create `.github/`, `docker/`, `scripts/`, dashboard directories, a trace database, hosted-service configuration, or provider-specific observability assets.

## 12. Configuration

Phase 6 adds non-secret observability configuration:

```toml
[observability]
enabled = true
runtime_dir = ".local/prisma/runtime"
write_latest = true
write_per_request = true
```

Rules:

- All values are non-secret. No API keys, tokens, endpoints, or credentials.
- `runtime_dir` must resolve under `.local/` so routine runs produce no committed diffs; the writer rejects targets outside `.local/`.
- `enabled = false` disables event capture, artifact writing, and the inline `runtime` block, leaving all existing behavior and the existing response schema intact.
- `write_latest` / `write_per_request` independently toggle the two artifact writes (§7).
- No thresholds, budgets, or external endpoints are configured in Phase 6.

## 13. Testing Strategy

Tests are correctness tests for the observability harness. They assert deterministic structure, not wall-clock values.

- **Request id generation:** ids are unique per request, filename-safe, and stable across all events and artifacts of a single request.
- **Event ordering:** events are recorded with a monotonic `sequence` and appear in the fixed stage order for a normal request; `sequence` (not `timestamp`) is the assertion key.
- **Timing capture:** the timing helper records a non-negative `duration_ms` for each completed stage span and `None` for point events; durations are excluded from equality assertions (assert `>= 0` and presence only).
- **Metrics aggregation:** given a synthetic event stream, aggregated metrics (`retrieval_attempts`, `retrieved_context_count`, `citation_count`, `*_char_count`, `generated_answer_sentence_count`, per-stage latency sums) equal the expected deterministic values.
- **Artifact writing:** enabling observability writes `latest-request.json` and `requests/<request_id>.json` under a temp runtime dir; content round-trips through the Pydantic models; writes outside `.local/` are rejected.
- **Inspect command output:** `python -m app.observability.inspect` reads a fixture artifact and prints the expected summary fields; it exits cleanly with a clear message when no artifact exists.
- **API response backward compatibility:** existing `QueryResponse` fields are unchanged; the `runtime` block is present and additive when enabled and absent/`null` when `[observability].enabled = false`; existing Phase 2/3 API tests still pass unchanged.
- **Behavior invariance:** a request produces identical `answer`, `citations`, `retrieved_context`, `metadata`, and `workflow` values whether observability is enabled or disabled.
- **Eval/regression metrics inclusion (only if implemented):** when runtime display is wired into eval/regression output, assert it is informational and does not change pass/fail, `overall_pass_rate_delta`, or comparison rules.

Tests should use small synthetic event/metrics fixtures and temp directories. No test may require network access or provider credentials.

## 14. Validation Commands

After Phase 6 implementation, these commands must pass:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy app evals
python -m pytest
python -m app.retrieval.index
python -m evals.runner
python -m evals.regression
```

Observability smoke command (reads the generated runtime artifact after a request/eval run has produced one):

```bash
python -m app.observability.inspect
```

Additional repository checks:

```bash
git diff --check
git status --short
```

Confirm that routine runs write runtime artifacts only under `.local/prisma/runtime/`, that no runtime artifact is staged or committed, and that `evals/baselines/phase4-baseline.json`, `evals/baselines/phase4-prompt-snapshot.json`, and `evals/golden/cases.jsonl` remain unchanged.

## 15. Deliverables

Phase 6 deliverables:

- A request-local runtime event model with a fixed stage vocabulary.
- A deterministic per-request runtime metrics model (latencies + proxy counts, no token billing).
- Stage timing instrumentation threaded through the RAG service and Phase 3 workflow **without behavior change**.
- An optional additive `runtime` block on `QueryResponse`, backward-compatible with the existing schema.
- Generated runtime artifacts at `.local/prisma/runtime/latest-request.json` and `.local/prisma/runtime/requests/<request_id>.json`.
- A local inspection command `python -m app.observability.inspect`.
- Non-secret `[observability]` configuration and typed settings.
- Correctness tests under `tests/observability/`.
- README and development-guide updates documenting the observability smoke path and generated-artifact policy.

## 16. Risks

### Observability Becoming Production Telemetry

Risk: Instrumentation grows into an APM/telemetry pipeline.

Mitigation: Keep it local-first, artifact-based, and disable-able. No exporters, no background threads, no network. Fixed, closed stage vocabulary.

### Introducing External Vendors

Risk: OpenTelemetry, LangSmith, or another SDK is added "for convenience."

Mitigation: Plain Pydantic + standard library only. No new runtime dependency. Reviewer must reject any vendor import.

### Runtime Metrics Changing Behavior

Risk: Instrumentation alters retrieval, workflow routing, generation, citations, or error handling.

Mitigation: Recorder is passive; it only reads values already computed. A behavior-invariance test asserts identical response fields with observability enabled vs. disabled.

### Noisy Generated Artifacts

Risk: Per-request files accumulate or leak into commits.

Mitigation: Write only under `.local/`; ensure gitignore coverage; `git status --short` in validation. Keep `latest-request.json` overwritten; per-request files are opt-out via config.

### Overcomplicated Tracing Abstraction

Risk: A general tracing framework is built.

Mitigation: One `RuntimeRecorder`, one timing helper, a fixed stage set. YAGNI. Simplicity rule (AGENTS.md §6).

### Leaking Private Data

Risk: Prompt, question, answer, or full chunk text ends up in events/artifacts.

Mitigation: Events carry only counts, ids, paths, and small scalar details. Explicit rule and tests forbid text payloads. Counts are proxies, not content.

### Breaking API Schema

Risk: The `QueryResponse` change breaks existing consumers.

Mitigation: `runtime` is strictly additive and optional; existing fields are frozen; backward-compatibility test plus existing Phase 2/3 API tests must pass unchanged.

## 17. Success Criteria

Phase 6 is complete when:

- Runtime metrics are generated locally for each request, with no network access.
- The `POST /query` API remains backward-compatible; existing fields are unchanged and the `runtime` block is additive.
- A request-level report is created at `.local/prisma/runtime/requests/<request_id>.json`, and `latest-request.json` reflects the most recent request.
- `python -m app.observability.inspect` reads local artifacts and prints a concise, correct summary.
- All validation commands pass, including `ruff`, `mypy app evals`, and `pytest`.
- `python -m evals.runner` and `python -m evals.regression` still pass and remain informative-only with respect to runtime metrics (pass/fail logic unchanged).
- No external telemetry, no telemetry upload, and no external endpoints are introduced.
- No dashboards are introduced.
- No CI gates are introduced.
- No persistent trace database or production DB is introduced.
- No secrets are introduced.
- No Phase 7+ capability is introduced.

## 18. Recommended Next Natural Step

After Phase 6 is implemented and validated, the expected next phase is:

- **Phase 7 — CI/CD Evaluation Gate.**

Phase 7 should turn the existing local evaluation and regression outputs into an automated gate (e.g. a CI workflow that fails when the evaluation pass rate drops below the configured minimum), building on the deterministic artifacts produced in Phases 4–6. Runtime metrics from Phase 6 may inform, but must not by themselves define, that gate.

Separately — and **not** part of Phase 6 implementation — this is the right point to create a **visual design prototype** that visualizes:

- evaluation scorecards,
- prompt regression reports,
- runtime metrics,
- workflow routes,
- citations and retrieved context.

That prototype must remain visual/design-only and must not be folded into Phase 6 implementation. It consumes the generated artifacts from Phases 4–6; it does not add capability to them.
