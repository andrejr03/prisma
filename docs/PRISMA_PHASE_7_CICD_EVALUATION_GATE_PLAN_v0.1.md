# Prisma - Phase 7: CI/CD Evaluation Gate Plan v0.1

> Planning document only. This document defines *what* Phase 7 should build and *how* it should be shaped. It does not implement code, create `.github/`, define workflows, or modify existing files. Implementation is a separate, later step performed only against an approved plan.

**Status:** Draft v0.1
**Date:** 2026-07-02
**Document:** PRISMA_PHASE_7_CICD_EVALUATION_GATE_PLAN_v0.1.md
**Audience:** developers, AI engineers, ML engineers, technical reviewers, and maintainers
**Predecessors:** [v1 Engineering Milestone](PRISMA_V1_ENGINEERING_MILESTONE_v1.0.md), [v1 Engineering Readiness Review](PRISMA_V1_ENGINEERING_READINESS_REVIEW_v1.0.md)
**Companions:** [Project Plan](PRISMA_PROJECT_PLAN_v0.1.md), [Repository Architecture](PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md)

---

## 0. How to Read This Document

This is the phase plan for Prisma's first CI/CD gate. It follows the same discipline as Phases 0–6: it defines scope, aligns to the architecture, specifies exact commands, and states success criteria before any implementation begins. It is deliberately small. Phase 7 automates commands that already run locally; it does not invent a new execution path, a new runtime dependency, or new application behavior.

The load-bearing constraint to keep in mind throughout: **CI must call the existing local commands, in the existing local way, on a clean checkout.** If a gate cannot be expressed as "run a command the developer already runs and react to its result," it is out of scope for Phase 7.

---

## 1. Purpose

Phase 7 exists to convert Prisma's existing *local evidence* into an *automated, repository-level gate*.

Phases 0–6 built the substrate:

- **Phase 4 (Evaluation Harness)** produces a deterministic scorecard from committed golden cases through the public API boundary, with a configured `minimum_pass_rate` (currently `0.8` in `configs/defaults.toml`).
- **Phase 5 (Prompt Regression)** fingerprints the configured prompt and compares current behavior against the committed Phase 4 baseline, producing an informational regression report.
- **Phase 6 (Observability & Runtime Metrics)** records request-local runtime artifacts and provides a read-only inspection command.

Today these run only when a developer chooses to run them. The v1 Readiness Review recorded that Phase 5 and Phase 6 are correctly *informational* and identified the missing seam: nothing yet enforces these checks automatically on every change. Phase 7 closes exactly that seam. It makes formatting, linting, type checking, tests, index build, evaluation, prompt regression, and observability inspection run automatically in CI, so a change that breaks correctness or drops evaluation quality below threshold is caught at the repository level rather than discovered later.

Phase 7 is the transition from **Foundation Engineering** (the system exists and is measurable locally) to **Operational Engineering** (the system's quality is enforced automatically).

---

## 2. Scope

### 2.1 In scope

- **GitHub Actions workflow planning.** A single workflow that runs the existing validation sequence on a clean checkout.
- **CI command sequence.** The exact, ordered set of commands defined in Section 5, matching the commands `docs/DEVELOPMENT.md` already documents.
- **Cache strategy.** Dependency (pip) caching only, keyed on the dependency manifest. No caching of generated `.local/` state.
- **Artifact strategy.** Upload generated evaluation and runtime reports as *CI artifacts* for inspection, never committing them.
- **Evaluation pass-rate handling.** A CI-side gate that fails the build when the evaluation pass rate falls below the configured `minimum_pass_rate` (Section 6 defines how, given that the runner currently returns success regardless of pass rate).
- **Regression report handling.** Run regression, upload its report, and fail only on runner *crash* — regression remains informational, consistent with Phase 5.
- **Runtime artifact handling.** Ensure a runtime artifact exists before inspection runs, upload the latest artifact, and keep runtime metrics informational.
- **Failure behavior.** Explicit, deterministic rules for when the workflow fails (Section 6).

### 2.2 Explicitly out of scope

Phase 7 introduces **none** of the following:

- Deployment or release automation.
- Docker or any container build.
- Hosted services or external runtime dependencies beyond GitHub Actions itself.
- External model or embedding providers.
- Dashboards or any UI surface.
- Scheduled / cron jobs.
- Matrix builds across multiple Python versions or operating systems, unless a concrete need is justified (Section 4.2 — default is a single version, single OS).
- Any change to application behavior, the local execution path, or the default configuration.
- Committing any generated artifact (`.local/` remains ignored).

If implementation appears to require any of the above, that is a signal to stop and report, not to expand Phase 7.

---

## 3. Architectural Alignment

Phase 7 is consistent with every governing document, and its home is a directory the architecture already reserved for it.

- **Project Plan.** Phase 7 (CI/CD Evaluation Gate) is the planned successor to the evaluation and regression phases. It automates what those phases made measurable.
- **Repository Architecture.** `.github/` is a declared top-level directory whose stated responsibility is "CI/CD workflows and repository automation that run quality, evaluation, and regression gates," with the explicit rule that it "orchestrates; it does not implement." Section 14 of the architecture lists `.github/` as the directory introduced "when evals, regression, and budgets become automated gates (plan Phase 7)." Phase 7 is precisely that moment. The workflow must contain **no business logic** — only invocations of existing `app/` and `evals/` commands.
- **AGENTS.md.** The workflow honors scope control (implement only the approved phase; create no unapproved services), simplicity (choose the simplest expression of the gate), documentation rules (update `README.md` and `docs/DEVELOPMENT.md` if public behavior changes), and the validation rules (run every required check). Notably, `AGENTS.md` currently lists "CI" among capabilities not to introduce before their phase — Phase 7 is the approved phase that lifts that restriction for CI specifically, and only for CI.
- **ADRs.** ADR-0001 (code/data separation) — the workflow is orchestration, not code or data. ADR-0002 (provider-adapter boundary) — CI uses the default local backends and names no provider. ADR-0003 (secrets via environment) — the gate needs no secrets; none are introduced. ADR-0004 (evaluation-first development) — Phase 7 elevates the evaluation harness to an enforced gate, the natural fulfillment of this ADR.
- **v1 Engineering Milestone.** The milestone names Phase 7 as the shift "from a local engineering foundation to operational automation" that should "turn the existing local checks, evaluation harness, prompt regression, and runtime evidence into automated repository-level quality gates without weakening the local-first default path." This plan is scoped to do exactly that and nothing more.
- **v1 Readiness Review.** The review returned **PASS WITH OBSERVATIONS** with **YES** for readiness, and recommended (a) confirming the local check suite is green before Phase 7 and (b) small pre-Phase-7 cleanups. Phase 7 assumes those are addressed or knowingly accepted; it does not itself perform code refactors.

**Alignment guardrail:** the workflow file is the *only* new artifact Phase 7 requires. If Phase 7 seems to need changes inside `app/` or `evals/`, that is a separate, explicitly-argued decision (see Section 6.3 on the pass-rate exit contract), not an implicit part of wiring CI.

---

## 4. CI Workflow Design

A single workflow file, planned as `.github/workflows/prisma-ci.yml` (created only at implementation time).

### 4.1 Trigger events

- `push` to the default branch.
- `pull_request` targeting the default branch.

Rationale: gate the mainline and every proposed change to it. No scheduled triggers (out of scope). No triggers on tags (no release automation).

### 4.2 Runtime environment

- **Runner:** `ubuntu-latest` (GitHub-hosted). Single OS.
- **Python version:** a single version consistent with the project's `requires-python = ">=3.11"`. Plan for `3.11` as the pinned CI version (the floor the project supports), so the gate exercises the minimum supported interpreter. A version **matrix is intentionally omitted**: the project targets `>=3.11` and there is no current evidence of version-specific behavior to justify the added cost. Revisit only if a concrete cross-version issue appears.

### 4.3 Install steps

1. `actions/checkout` — clean checkout.
2. `actions/setup-python` pinned to the CI Python version, with pip caching enabled (Section 4.5).
3. `python -m pip install -U pip`.
4. `python -m pip install -e ".[dev]"` — installs the app plus the `dev` extras (`ruff`, `mypy`, `pytest`) declared in `pyproject.toml`. No `requirements.txt` is introduced (forbidden by `DEVELOPMENT.md`); dependencies stay declared in `pyproject.toml`.

### 4.4 Validation steps

The exact command sequence in Section 5, run in order, on the clean checkout. Each command is a discrete CI step so failures are attributable to a specific check.

### 4.5 Cache strategy

- **Cache:** pip's download cache only, keyed on `pyproject.toml` (the dependency manifest). Use `actions/setup-python`'s built-in `cache: pip`.
- **Do not cache** any generated state: the qdrant-local index, scorecards, regression reports, and runtime artifacts are all rebuilt from committed inputs on every run. Caching them would undermine reproducibility and risk stale evidence.

### 4.6 Artifact upload behavior

After the validation steps, upload the generated reports (Section 7) using `actions/upload-artifact`, with `if: always()` semantics on the upload step so artifacts are captured even when an earlier gate fails (aiding diagnosis). Uploaded artifacts are ephemeral CI outputs; they are never committed.

### 4.7 Failure rules

Failure is governed by process exit codes plus one CI-side assertion for the pass-rate gate. See Section 6 for the full policy. In summary: any non-zero exit from formatting, linting, type checking, tests, index build, the evaluation runner, the regression runner, or the inspection command fails the build; and the pass-rate assertion fails the build when evaluation quality drops below the configured minimum.

---

## 5. Command Sequence

CI runs exactly these commands, in this order, matching what `docs/DEVELOPMENT.md` already documents for local use:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy app evals
python -m pytest
python -m app.retrieval.index
python -m evals.runner
python -m evals.regression
python -m app.observability.inspect
```

**Ordering rationale (grounded in current behavior):**

1. `ruff check` / `ruff format --check` / `mypy` / `pytest` — fast static and correctness gates first; fail early and cheaply.
2. `app.retrieval.index` — build the local qdrant index from the committed corpus before anything queries it. (The evaluation runner also verifies/builds the index if needed, but building it explicitly first keeps the step attributable.)
3. `evals.runner` — exercises `POST /query` through `TestClient`, writes `.local/prisma/evals/scorecard.json`, and — because observability is enabled by default — produces runtime artifacts under `.local/prisma/runtime/` as a side effect.
4. `evals.regression` — fingerprints the prompt and compares against the committed Phase 4 baseline; writes `.local/prisma/evals/regression.json`.
5. `app.observability.inspect` — **must run after** `evals.runner`/`evals.regression`, because inspection reads `.local/prisma/runtime/latest-request.json` and exits non-zero with `RuntimeArtifactError("no runtime artifact found; issue a request first")` if none exists. Running it last guarantees the artifact is present.

**Important current-behavior note for the pass-rate gate:** `evals.runner.main()` and `evals.regression.main()` currently `print` a summary and `return 0` unconditionally — they exit non-zero only if they *crash*. Neither today fails the process when the evaluation pass rate is below `minimum_pass_rate`, and regression does not fail on regressed metrics (it is informational). Section 6 defines how CI enforces the pass-rate gate on top of this without changing default application behavior.

---

## 6. Evaluation Gate Policy

The gate is deterministic. CI fails when, and only when, one of the following holds.

### 6.1 Fail conditions

- **Formatting / lint / type / test failure** — any non-zero exit from `ruff check`, `ruff format --check`, `mypy app evals`, or `pytest`.
- **Index build failure** — non-zero exit from `app.retrieval.index`.
- **Evaluation runner crash** — non-zero exit from `evals.runner` (e.g., malformed response, missing golden data, harness error).
- **Evaluation pass rate below minimum** — the computed pass rate in the generated scorecard is below the configured `minimum_pass_rate` (`configs/defaults.toml`, currently `0.8`). See 6.3 for how this is enforced.
- **Regression runner crash** — non-zero exit from `evals.regression` (e.g., missing/invalid baseline, comparison error).
- **Inspection failure** — non-zero exit from `app.observability.inspect` (e.g., missing or malformed runtime artifact).

### 6.2 Explicitly non-failing (informational)

- **Runtime metrics values** — latencies, counts, and other runtime measurements are informational and never fail the build. Only a *crash* of the inspection command fails CI, not the metric values it reports.
- **Regressed metrics in the regression report** — consistent with Phase 5, a detected regression is recorded and surfaced, not build-breaking. Promoting regression to a hard gate is a **future** decision requiring its own approval; it is out of scope for Phase 7.

### 6.3 Enforcing the pass-rate gate without changing application behavior

Because `evals.runner.main()` returns `0` regardless of pass rate today, a pure "run the command" step would catch only crashes, not sub-threshold quality. Phase 7 must therefore make a deliberate choice. Two options, with a recommendation:

- **Option A (recommended) — CI-side assertion, no application change.** After `evals.runner` writes the scorecard, add a small CI step that reads `.local/prisma/evals/scorecard.json` and fails the build if the recorded pass rate is below `minimum_pass_rate`. This keeps application behavior and the local execution path unchanged, treats the scorecard as read-only evidence (the same philosophy as the inspection command), and keeps enforcement policy in CI where it belongs. It adds no new application code path.
- **Option B (alternative, requires explicit approval) — change the runner exit contract.** Modify `evals.runner.main()` to return non-zero when the pass rate is below the minimum. This is cleaner conceptually but **changes application behavior** (the runner's exit contract), which this plan's constraints forbid without a separate, explicit decision. It would also alter the local developer experience (the command would start failing locally too).

**Recommendation:** adopt **Option A** for Phase 7 to honor "do not modify application behavior" and "CI automates existing commands." Record Option B as a candidate for a future, separately-approved refinement if the team later wants the local command to enforce the threshold too.

---

## 7. Artifacts

CI uploads the following generated reports as **CI artifacts** (ephemeral, downloadable from the workflow run). None of these are committed to the repository; all remain under `.local/` and ignored by git.

| Artifact | Generated path | Purpose in CI |
|---|---|---|
| Evaluation scorecard | `.local/prisma/evals/scorecard.json` | Evidence for the pass-rate gate; per-metric results. |
| Prompt regression report | `.local/prisma/evals/regression.json` | Informational drift record vs. the committed baseline. |
| Runtime latest-request artifact | `.local/prisma/runtime/latest-request.json` | Informational runtime metrics from the eval run; input the inspection command reads. |

Clarifications:

- These are **CI artifacts, not committed files.** The workflow uploads them for inspection; it must never `git add`/commit them. `.gitignore` already excludes `.local/`, and Phase 7 must not weaken that.
- Committed evaluation assets (`evals/baselines/phase4-baseline.json`, `evals/baselines/phase4-prompt-snapshot.json`, `evals/golden/cases.jsonl`) are inputs, not outputs; CI reads them and must not overwrite or promote them. Baseline promotion remains an explicit, reviewed human change, per `DEVELOPMENT.md`.
- Per-request runtime artifacts under `.local/prisma/runtime/requests/` may optionally be included, but the latest-request artifact is sufficient and is the minimal, clearest upload.

---

## 8. Repository Changes

Phase 7 is deliberately minimal in its footprint.

**Expected new file (created only at implementation time):**

```text
.github/workflows/prisma-ci.yml
```

**This planning document (created now, in this task):**

```text
docs/PRISMA_PHASE_7_CICD_EVALUATION_GATE_PLAN_v0.1.md
```

**Documentation updates expected at implementation time (not now):**

- `README.md` — add a short note that CI runs the validation sequence and enforces the evaluation gate (roadmap row for Phase 7 moves to "Complete").
- `docs/DEVELOPMENT.md` — note that the same local commands are what CI runs, and that CI enforces the pass-rate gate via the scorecard.

**Explicitly not created now:** the workflow file, any `.github/` directory or contents, and any change to application or evaluation code. This task creates only the planning document above.

---

## 9. Testing Strategy

The workflow should be validated as much as possible *locally*, before and during implementation, to minimize the classic "debug CI by pushing commits" loop.

1. **Run the exact sequence locally on a clean tree.** From a fresh virtualenv on Python 3.11, run the eight commands in Section 5 in order and confirm each succeeds and produces its expected artifact. This is the primary rehearsal of what CI will do. (`docs/DEVELOPMENT.md` already documents these commands and smoke checks.)
2. **Rehearse from a clean checkout.** Verify the sequence works with no pre-existing `.local/` state (e.g., in a fresh clone or after removing `.local/`), since CI always starts clean. This specifically exercises the index-build-before-query and artifact-before-inspect ordering.
3. **Validate the pass-rate assertion (Option A).** Test the scorecard-reading assertion against a known-good scorecard (passes) and, in a throwaway local experiment, against a synthetic scorecard below threshold (fails) — without committing either. Confirms the gate actually gates.
4. **Confirm no artifact leakage.** After a full local run, `git status` must show no new tracked files under `.local/`. This mirrors the CI invariant that generated artifacts are never committed.
5. **Static workflow validation at implementation time.** Lint the YAML (e.g., `actions/checkout` and `setup-python` versions pinned; steps well-formed) and, optionally, dry-run with a local Actions runner if available. Keep this lightweight; the substance of the gate is the command sequence, which item 1 already proves.

The dividing line stays intact: `tests/` proves code correctness, `evals/` measures output quality. Phase 7 adds no test logic and no eval logic — it orchestrates both.

---

## 10. Risks

| Risk | Description | Mitigation |
|---|---|---|
| **CI flakiness** | Non-determinism (timing, ordering, network) causing intermittent failures. | The default path is fully local and deterministic (hashing embeddings, qdrant-local, deterministic generation, deterministic metrics). Runtime *timing* is variable but is informational and never gated (Section 6.2). No network calls in the default path. |
| **Dependency install time** | `pip install -e ".[dev]"` (FastAPI, qdrant-client, uvicorn, tooling) slowing every run. | Enable pip caching keyed on `pyproject.toml` (Section 4.5). Dependency set is small; single Python version avoids matrix multiplication of install cost. |
| **Generated artifact leakage** | A workflow accidentally committing `.local/` outputs or promoting a baseline. | CI only *uploads* artifacts (read-only), never commits. `.gitignore` already excludes `.local/`. Testing-strategy item 4 asserts a clean `git status`. Baseline promotion stays a manual reviewed change. |
| **Evaluation brittleness** | Golden set is small (7 cases); a minor change could swing the pass rate across the `0.8` threshold. | Keep the threshold as configured; treat threshold breaches as real signals to investigate. Growing the golden set is future evaluation work, not Phase 7 scope. Regression report (uploaded) helps diagnose which metric moved. |
| **Prompt regression false alarms** | Legitimate prompt edits flagged as regressions. | Regression stays **informational** in Phase 7 (never build-breaking), exactly as Phase 5 intended. A regression surfaces in the uploaded report and prompts a human to re-review/promote the baseline; it does not block CI. |
| **Observability command requires an artifact** | `app.observability.inspect` exits non-zero if no runtime artifact exists. | Order inspection **after** `evals.runner`/`evals.regression`, which generate `latest-request.json` as a side effect of exercising `POST /query` with observability enabled (Section 5). Clean-checkout rehearsal (Testing item 2) verifies this ordering holds. |
| **Pass-rate gate is a no-op if mis-wired** | Relying on `evals.runner` exit code alone would miss sub-threshold pass rates, since the runner returns 0 regardless. | Implement the explicit CI-side scorecard assertion (Option A, Section 6.3); validate it fails on a below-threshold scorecard (Testing item 3). |
| **Action version drift / supply chain** | Unpinned marketplace actions changing behavior. | Pin `actions/checkout`, `actions/setup-python`, and `actions/upload-artifact` to fixed major versions; no third-party actions beyond these first-party ones. No secrets are exposed to any action. |

---

## 11. Success Criteria

Phase 7 is complete when **all** of the following hold:

- A GitHub Actions workflow exists at `.github/workflows/prisma-ci.yml`.
- CI runs the full validation sequence from Section 5, in order, on a clean checkout.
- The evaluation gate is enforced: CI fails on test failure, on evaluation/regression runner crash, and when the evaluation pass rate is below the configured `minimum_pass_rate`.
- Generated reports (scorecard, regression report, latest runtime artifact) are uploaded as CI artifacts.
- No generated artifacts are committed to the repository; `.local/` remains ignored and untracked.
- Runtime metrics and detected prompt regressions remain informational (never build-breaking) in Phase 7.
- The local developer path is unchanged: the same commands behave the same locally as before, and no application behavior or default configuration is modified.
- `README.md` and `docs/DEVELOPMENT.md` note that CI runs the sequence and enforces the gate.

---

## 12. Recommended Next Natural Step

**Implement the Phase 7 CI/CD Evaluation Gate** against this approved plan:

1. Add `.github/workflows/prisma-ci.yml` triggering on push and pull_request to the default branch, on `ubuntu-latest` with Python 3.11 and pip caching.
2. Install via `pip install -e ".[dev]"`; run the eight commands in Section 5 as discrete, ordered steps.
3. Add the Option A scorecard pass-rate assertion after `evals.runner`.
4. Upload the three reports in Section 7 as CI artifacts with `if: always()`; commit nothing generated.
5. Update `README.md` and `docs/DEVELOPMENT.md` to reflect the enforced gate.
6. Rehearse the full sequence locally on a clean checkout first (Section 9) before relying on CI.

Keep the implementation small: a single workflow that orchestrates existing commands, adds one read-only assertion, and uploads evidence — nothing more.

---

## Constraints (restated for the implementer)

- Keep Phase 7 small.
- Do **not** introduce Docker.
- Do **not** introduce deployment or release automation.
- Do **not** introduce hosted model providers or external providers.
- Do **not** introduce external monitoring.
- Do **not** introduce dashboards.
- Do **not** modify application behavior or the default configuration (see Section 6.3 — prefer the CI-side assertion over changing the runner's exit contract).
- CI must automate the existing local commands, not create a new execution path.

---

## Validation of This Plan

- **All completed foundation phases referenced.** Phases 0–6 are named, and Phases 4–6 (evaluation, regression, observability) are described as the substrate Phase 7 builds on — Sections 1, 3.
- **Phase 7 remains CI-only.** Scope is a single GitHub Actions workflow orchestrating existing commands plus one read-only assertion — Sections 2, 4, 8.
- **No deployment scope introduced.** Deployment, Docker, hosted services, dashboards, release automation, and scheduled jobs are explicitly excluded — Section 2.2.
- **Local-first default path preserved.** No application behavior or default configuration changes; the same commands behave the same locally — Sections 2.2, 6.3, 11.
- **Generated artifacts remain uncommitted.** Reports are CI artifacts only; `.local/` stays ignored — Sections 7, 10, 11.
- **GitHub Actions planned but not implemented.** The workflow file is described but explicitly not created in this task; only this planning document is created — Sections 4, 8.

---

## Final Report

**File created**

- `docs/PRISMA_PHASE_7_CICD_EVALUATION_GATE_PLAN_v0.1.md` — this planning document. No other files created or modified; no code written; no `.github/` or workflow created.

**Key CI decisions**

- Single workflow (`.github/workflows/prisma-ci.yml`), triggered on push and pull_request to the default branch, on `ubuntu-latest`, Python 3.11, with pip caching keyed on `pyproject.toml`.
- Install via `pip install -e ".[dev]"`; run the eight documented commands (Section 5) as discrete, ordered steps.
- Ordering is load-bearing: build the index before evaluation, and run `observability.inspect` last so a runtime artifact exists (it exits non-zero otherwise).
- The evaluation pass-rate gate is enforced **CI-side** by asserting on the generated scorecard (Option A), because `evals.runner.main()` currently returns 0 regardless of pass rate — chosen to avoid modifying application behavior.
- Regression and runtime metrics stay **informational** (fail only on crash), consistent with Phases 5 and 6.
- Generated scorecard, regression report, and latest runtime artifact are uploaded as **CI artifacts**, never committed.

**Risks**

- CI flakiness (mitigated by the deterministic local path; timing never gated).
- Dependency install time (mitigated by pip caching, single Python version).
- Generated-artifact leakage (mitigated by upload-only, `.gitignore`, clean-status check).
- Evaluation brittleness on a 7-case golden set near the `0.8` threshold (treat breaches as real signals; growing the set is future work).
- Prompt-regression false alarms (kept informational, not build-breaking).
- Observability command requiring a pre-existing artifact (mitigated by command ordering).
- Pass-rate gate becoming a no-op if wired to the runner exit code alone (mitigated by the explicit scorecard assertion).

**Recommended next natural step**

Implement the Phase 7 CI/CD Evaluation Gate against this approved plan — a single GitHub Actions workflow that runs the existing validation sequence, enforces the evaluation pass-rate gate via a read-only scorecard assertion, and uploads generated reports as CI artifacts, while committing nothing generated and leaving the local-first default path unchanged.
