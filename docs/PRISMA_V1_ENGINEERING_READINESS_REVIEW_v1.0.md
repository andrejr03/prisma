# Prisma v1 Engineering Readiness Review

> Engineering review only. This document assessed whether Prisma was technically ready to move from Foundation Engineering into Operational Engineering (Phase 7). It records findings; it does not implement fixes, redesign architecture, or introduce scope.

**Status:** v1.0 readiness review
**Date:** 2026-07-01
**Document:** PRISMA_V1_ENGINEERING_READINESS_REVIEW_v1.0.md
**Reviewed at commit:** `64b43d8` (docs: record prisma v1 engineering foundation milestone)
**Audience:** developers, AI engineers, ML engineers, technical reviewers, and maintainers
**Reviewed scope:** the repository at the reviewed commit (Phases 0–6 complete, README showcase polish applied)

---

## 0. Method and Evidence

This review is a static engineering assessment of the repository at the commit above. It reads the architecture, project plan, phase plans, ADRs, README, DEVELOPMENT guide, `AGENTS.md`, milestone record, and the implementation under `app/`, `evals/`, `tests/`, `configs/`, `prompts/`, and `datasets/`.

**Evidence base:**

- Application code: 32 tracked files under `app/` (~3,242 lines of Python).
- Test surface: 29 files under `tests/`, 72 `test_` functions across API, retrieval, workflow, generation, persistence, observability, evals, and regression suites.
- Evaluation assets: 7 committed golden cases (`evals/golden/cases.jsonl`), a committed Phase 4 baseline, and a committed prompt fingerprint snapshot.
- Repository hygiene: `.gitignore` excludes `.local/`, caches, virtualenvs, secrets, and macOS cruft; `git ls-files` confirms no generated artifacts, `.egg-info`, `__pycache__`, `.DS_Store`, or secrets are tracked.
- Structural check: no unapproved deferred top-level directories existed ahead of their phase at the reviewed commit.

**Validation note.** Live validation was not part of this historical static review. Findings below were drawn from source reading of a complete, coherent, and well-tested source tree; the validation-command set was internally consistent and the test surface was substantial. This limitation is recorded as a Low risk rather than treated as a defect.

---

## 1. Executive Summary

**Overall assessment:** Prisma has reached a coherent, disciplined, local-first LLM engineering foundation. The repository matches its own architecture blueprint closely: boundaries hold, provider neutrality is enforced at a single adapter, the default path is local and deterministic, evaluation is first-class, and generated state is kept out of version control. Documentation is unusually complete for a project of this size and reflects genuine engineering intent rather than decoration.

The review found **no blocking defects** and **no future-phase scope leakage**. It did surface a small number of maintainability observations — most notably a cross-module private-symbol import and a duplicated request/response path retained behind a configuration flag — that were worth resolving as Phase 7 automated gates were introduced, but none of which prevented that transition.

**Overall readiness:** **PASS WITH OBSERVATIONS**

**Justification.** Every completed phase achieved its stated objective, the architecture was intact, the repository was clean, and the evaluation foundation (golden cases, baseline, prompt fingerprint, deterministic metrics, informational regression) was exactly the substrate Phase 7 needed. The result was not an unqualified PASS because two real coupling/duplication observations and minor documentation drift existed; it was well above a CONDITIONAL PASS because none of these were gating and none required architectural change. The correct characterization was a healthy foundation with a short list of small, non-blocking cleanups.

---

## 2. Architecture Review

**Reference documents:** `docs/PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md`, `docs/PRISMA_PROJECT_PLAN_v0.1.md`, `docs/adr/ADR-0001..0004`.

### 2.1 Integrity against the blueprint

The implemented structure is a faithful realization of the documented architecture:

- **Boundary-first layout holds.** `app/` contains all executable logic, organized by seam (`api`, `workflow`, `retrieval`, `generation`, `providers`, `persistence`, `observability`, `models`). `evals/` measures across the public API boundary. `prompts/`, `configs/`, and `datasets/` are pure data. `docs/` describes and decides only. This is precisely the dependency gravity the architecture prescribes.
- **Provider neutrality is real, not aspirational.** Every provider entry point is funneled through `app/providers/`. `create_generation_provider` rejects any backend other than `local-grounded` (`app/providers/generation.py:114`), and no application module names or imports a vendor SDK. Embeddings are a deterministic hashing backend (`configs/defaults.toml`), so the default path has no external provider dependency at all — consistent with ADR-0002.
- **Layer flow is downward.** Control moves API → workflow → retrieval/generation → providers/persistence, with observability injected as a cross-cutting recorder rather than a business layer. The API never reasons about retrieval internals; the provider adapter has no knowledge of the workflow.
- **ADRs are consistent with the code.** Code/data separation (ADR-0001), the provider-adapter boundary (ADR-0002), secrets-via-environment (ADR-0003 — no secrets in `configs/`, `prompts/`, or code; `.env*` ignored), and evaluation-first development (ADR-0004 — `evals/` observes through `POST /query`) are all observable in the tree. No ADR contradicts the implementation, and no ADR appears to have been edited after the fact to justify code.

### 2.2 Architecture drift

Minimal. The intended boundaries are intact. Two mild internal-coupling signals are worth recording (neither is a boundary violation):

1. **Cross-module private imports.** `app/workflow/runner.py:12-20` imports seven symbols from `app/generation/service.py`, four of which are private (`_citations_for`, `_load_prompt`, `_retrieved_context_items`, `_validate_citations`) alongside three exception classes. Reaching across a module boundary for underscore-prefixed helpers means those helpers are, in practice, a shared internal API that has not been promoted to one. This is hidden coupling: a change to a "private" helper in `service.py` silently affects `runner.py`.
2. **A phase constant embedded in the generic loader.** `load_settings` hard-codes `max_retrieval_attempts must be exactly 2` as a Phase-3 invariant inside the general configuration loader (`app/config.py:204`). The guard is reasonable, but locating a phase-specific rule in the neutral loader couples configuration parsing to a particular phase's policy.

### 2.3 Duplicated responsibilities

One meaningful duplication. Two parallel implementations of the full RAG pipeline exist:

- The bounded workflow in `app/workflow/runner.py` (the default path; `workflow.enabled = true`).
- A pre-workflow path, `RagService._answer_without_workflow` in `app/generation/service.py:89`, reachable only when `workflow.enabled = false`.

Both assemble context, generate, validate citations, build the route, and shape `QueryResponse`; and request validation is duplicated almost verbatim between `RagService._validate_request` (`service.py:191`) and the module-level `_validate_request` (`runner.py:385`). The non-workflow path is effectively a retained Phase 2 baseline behind a flag that the default configuration never sets. It is coherent and tested, but it is a second, parallel behavior surface that must be kept in step by hand.

### 2.4 Unnecessary coupling and hidden complexity

Beyond the two items above, coupling is well-controlled. The runtime recorder is optional and injected (`RuntimeRecorder | None`), so observability adds no hard dependency to the workflow. `RagService` imports the workflow runner lazily inside the method (`service.py:65`) to avoid an import cycle — a small, deliberate seam rather than accidental complexity. No god-objects, no circular hard imports, no reach-through into persistence internals.

**Section verdict:** Architecture integrity is strong. Findings are maintainability-level, not structural.

---

## 3. Repository Structure Review

- **Directory layout.** Matches the architecture's declared top-level set. `app/` seams are clean and single-purpose; `evals/` holds the harness, metrics, golden data, baselines, and reporting; `configs/`, `prompts/`, `datasets/` are data-only.
- **Naming consistency.** Module and file names are descriptive and uniform (`retrieval/pipeline.py`, `workflow/routing.py`, `observability/runtime.py`). Documentation files follow a consistent `PRISMA_*_v*.md` convention. ADRs are numbered and titled consistently.
- **Boundaries.** No unapproved deferred directory existed ahead of schedule at the reviewed commit. The later `.github/` workflow belongs to the completed Phase 7 gate.
- **Generated artifacts.** All runtime state is confined to `.local/` and ignored. `git ls-files` shows zero tracked generated files, caches, or `.egg-info`. Runtime writes are additionally guarded to stay under `.local/` (`app/observability/runtime.py:267-282`).
- **Cleanliness.** No secrets, no `.env`, no committed `.DS_Store`. Tracked file distribution is proportionate (app 32, tests 29, docs 17, evals 11, assets 10, datasets 8).

**Minor cleanliness observation (Low).** `assets/prisma-prototype-v2.zip` (~18 KB) is a committed binary archive. It is intentional design-showcase material and clearly labeled design-only, but a binary blob in git does not diff and will accrete history weight if re-versioned. Worth a conscious decision (keep as-is, or track the prototype source elsewhere) rather than a fix.

**Section verdict:** Repository is clean and disciplined.

---

## 4. Phase Consistency Review

Each phase completed at the reviewed commit was reviewed for objective achievement, absence of future-phase leakage, and continued coherence.

| Phase | Objective | Evidence in repo | Future-phase leakage | Verdict |
|---|---|---|---|---|
| 0 — Repository Skeleton | Boundary-first skeleton, tooling, ADRs | `pyproject.toml`, `configs/`, `docs/adr/`, seam directories | None | Achieved |
| 1 — Ingestion & Indexing | Local corpus load, chunk, embed, index | `app/retrieval/*`, `datasets/sample_corpus/`, qdrant-local index build | None | Achieved |
| 2 — Baseline RAG API | Typed `POST /query`, cited answers, structured errors | `app/api/*`, `app/generation/service.py`, `app/models/rag.py` | None | Achieved |
| 3 — Bounded Agent Workflow | Validate → retrieve → assess → rewrite-once → generate → validate citations | `app/workflow/*`; `max_retrieval_attempts` bounded to 2 | None (rewrite strictly bounded to one retry) | Achieved |
| 4 — Evaluation Harness | Golden cases, deterministic metrics, scorecard | `evals/runner.py`, `evals/metrics.py`, committed baseline | None | Achieved |
| 5 — Prompt Regression | Prompt fingerprint, baseline comparison, report | `evals/fingerprints.py`, `evals/regression.py`, prompt snapshot | Regression was informational, not a gate — correctly deferred until Phase 7 | Achieved |
| 6 — Observability & Runtime Metrics | Runtime block, per-request artifacts, inspect command | `app/observability/*`; privacy-preserving metrics | No CI gate at the reviewed commit, no telemetry upload — correctly deferred | Achieved |

**Consistency observations:**

- **No future-phase capability was present at the reviewed commit.** There was no unapproved CI, Docker, hosted integration, provider comparison, LLM-as-judge metric, prompt registry, chat memory, or autonomous multi-agent behavior. The later Phase 7 CI workflow was added by its approved phase rather than ahead of schedule.
- **Bounded autonomy is genuinely bounded.** The workflow permits exactly one query rewrite and caps retrieval attempts at 2, enforced both in code and by the config loader guard. This matches the Phase 3 objective precisely.
- **Phase 5/6 restraint was correct.** Regression and runtime metrics were informational, not build-breaking. This was the right posture for a foundation and the seam Phase 7 later automated.

**Section verdict:** All phases coherent; no leakage.

---

## 5. Documentation Review

**Reviewed:** README, DEVELOPMENT, ADRs (0001–0004), `AGENTS.md`, all phase plans, project plan, architecture, and the v1 milestone.

**Strengths:**

- README functions as a genuine front door: what Prisma is, why it exists, feature/command tables, quick start, evaluation and observability sections, explicit boundaries/non-goals. Claims are measured ("design-only prototype", "no claim that Prisma is used in production").
- `AGENTS.md` is a strong operating contract (git rules, plan-first, architecture authority order, scope control, provider neutrality, secrets, reporting). It is consistent with the architecture and ADRs.
- The milestone record accurately described the foundation state at the time and has since been updated for completed Phase 7 automation.
- Architecture and ADRs are internally consistent and match the code.

**Contradictions / stale information (minor):**

1. **`docs/DEVELOPMENT.md` phase framing lagged the milestone at the reviewed commit (Low).** It opened with "This repository is in Phase 6" and described regression as "informational only in Phase 5" and runtime metrics as not gating "in Phase 6." That drift has since been resolved; DEVELOPMENT now describes Phases 0–7 as complete.
2. **README roadmap wording lagged the milestone at the reviewed commit (Low).** The roadmap table carried a "Current polish — README Showcase Polish — Current" row, while the milestone declared the foundation complete and Phase 7 the next step. That drift has since been resolved; README now marks Phase 7 complete.

**Duplicated explanations:** Setup/run instructions and the evaluation/observability descriptions appear in both README and DEVELOPMENT. This is acceptable (different audiences) but is a place where the two files can drift, as observation (1) shows.

**Missing documentation:** None material for a foundation. At the reviewed commit there was no `CONTRIBUTING.md` or root `LICENSE`; the root license has since been added for public release.

**Section verdict:** Documentation is a genuine strength with two low-severity drift items.

---

## 6. Codebase Readiness

- **Modularity.** High. Seams are small and single-purpose; providers, retrieval, workflow, generation, and observability are independently comprehensible. Dependency injection (optional recorder, optional retriever/provider) keeps modules testable in isolation.
- **Maintainability.** Good overall, with the two Section 2 items as the main drag: the cross-module private imports and the duplicated dual RAG path each create a hand-synchronization burden that matters more now that Phase 7 asserts behavior automatically.
- **Clarity.** Strong. Typed dataclasses/protocols, explicit exception taxonomy (`InvalidQueryError`, `NoContextError`, `CitationValidationError`, `UnsupportedGenerationBackendError`), and a clean error→code mapping (`_runtime_error_code`) make control flow legible.
- **Provider neutrality.** Enforced at exactly one boundary; the rest of the system speaks in neutral terms. Backend selection is configuration, not code.
- **Local-first execution.** The default path requires no hosted service and no network: hashing embeddings, qdrant-local persistence, deterministic local generation, and local artifact writes only.
- **Deterministic behavior.** Determinism is pursued where the system controls it: frozen config with strict typed validation, deterministic generation (context-only sentence selection), deterministic metrics, and privacy-preserving runtime capture (char counts, not text). Runtime timing is inherently variable but is isolated to the observability layer and not part of answer behavior.

**Section verdict:** The codebase is ready as a foundation; the two maintainability items are the natural pre-Phase-7 tidy-up.

---

## 7. Evaluation Readiness

- **Golden cases.** 7 committed cases covering the corpus's main topics plus a deliberate negative case (`out-of-corpus-no-context`) that exercises the no-context path. Small but purposeful and representative of the committed corpus.
- **Baselines.** A committed Phase 4 baseline records per-metric pass/fail/not-applicable counts and an index fingerprint, giving regression a fixed reference. `DEVELOPMENT.md` correctly instructs that baselines are promoted only as explicit reviewed changes, never overwritten by routine runs.
- **Prompt regression.** A committed prompt fingerprint snapshot (sha256 digest, byte/line counts, path) lets prompt drift be detected deterministically. The regression runner fingerprints the prompt, re-runs the harness through the public API, and diffs against the baseline — reproducible and provider-neutral.
- **Runtime observability.** Request-local metrics (stage latencies, counts, source paths, workflow route, neutral backend/model IDs) with explicit privacy guarantees (no question, prompt, or answer text; no secrets; no telemetry export) and a read-only inspection command.

**Did Phase 7 have a reliable foundation?** Yes. Phase 7's job — turning local checks, the eval harness, prompt regression, and runtime evidence into automated repository gates — could be built directly on committed, reproducible artifacts rather than on quality controls invented after the fact. The one caveat is that evaluation observes behavior through a single path (the default workflow). If future gating expands to the `workflow.enabled = false` path too, the duplicated pipeline (Section 2.3) should be consolidated or explicitly declared out of scope for gating.

**Section verdict:** Evaluation foundation is reliable and Phase-7-ready.

---

## 8. Portfolio Readiness

Judged purely as a repository, from the perspective of an experienced AI engineer reading it cold:

- **Engineering quality.** The project demonstrates the operational layer around RAG — retrieval boundaries, bounded workflow, golden-case evaluation, prompt regression, runtime observability — integrated in one place rather than as disconnected demos. That integration is the credible part; most reference RAG repositories stop at retrieval and a prompt.
- **Clarity.** A reader can locate any responsibility quickly, understand the boundaries from the architecture document, and trace a request from `POST /query` through the workflow to a cited answer and a runtime artifact.
- **Professionalism.** Scope discipline is visible everywhere: explicit non-goals, an agent operating contract, ADRs capturing the load-bearing decisions, and a refusal to over-claim (no production, benchmark, or commercial claims). Deferred directories are genuinely deferred.
- **Technical credibility.** Determinism, provider neutrality, local-first defaults, and privacy-preserving observability are implemented, not merely asserted. The test surface (72 tests across every seam) backs the claims.

The two maintainability observations are the kind a careful reader would notice and would read as honest, addressable debt rather than as red flags — particularly because the repository itself documents its boundaries so plainly.

**Section verdict:** High repository quality and technical credibility.

---

## 9. Risks

Only real engineering risks are listed.

### High
- **None identified.** No blocking defect, no boundary violation, no future-phase leakage, no secret exposure.

### Medium
- **M1 — Cross-module private-symbol coupling.** `app/workflow/runner.py` depends on four private helpers in `app/generation/service.py`. A refactor of those "private" helpers can silently break the workflow. Risk rises when automated gates assert behavior continuously. (`runner.py:12-20`)
- **M2 — Duplicated RAG path and validation.** Two parallel pipelines (workflow vs. `_answer_without_workflow`) and two copies of request validation must be kept in step by hand. If future gates cover both paths, divergence could produce inconsistent gate results or maintenance surprises. (`service.py:89`, `service.py:191`, `runner.py:385`)

### Low
- **L1 — Documentation drift.** `DEVELOPMENT.md` and README roadmap wording lagged the milestone at the reviewed commit (Section 5). This has since been resolved.
- **L2 — Phase constant in the generic loader.** `load_settings` bakes `max_retrieval_attempts == 2` into the neutral configuration parser (`config.py:204`).
- **L3 — Committed binary asset.** `assets/prisma-prototype-v2.zip` is a non-diffable blob in version control (Section 3).
- **L4 — Live validation not re-run here.** The documented check suite was not executed as part of this historical static review. Confidence rested on static review plus a substantial existing test surface; Phase 7 now supplies automated repository validation.

---

## 10. Recommended Improvements

Small, non-speculative follow-ups. None introduce architecture.

1. **Promote shared generation helpers out of "private."** Move `_load_prompt`, `_validate_citations`, `_citations_for`, `_retrieved_context_items`, and the shared exception classes into a public shared location (public names in `app/generation/`, or a small `app/generation/pipeline.py`) so `runner.py` imports supported symbols rather than underscore-prefixed ones. Behavior-preserving. (Addresses M1)
2. **Consolidate or explicitly annotate the duplicated path.** Either factor the shared request-validation and response-shaping into one function used by both paths, or add a short note (code comment + `DEVELOPMENT.md` line) declaring `_answer_without_workflow` a retained legacy baseline and clarifying whether future gates apply to it. (Addresses M2)
3. **Keep public status wording aligned** across README, DEVELOPMENT, and milestone records after phase transitions. (Addresses L1)
4. **Optionally relocate the phase invariant.** Consider moving the `max_retrieval_attempts == 2` guard from the generic loader into the workflow's own validation so the loader stays phase-neutral. (Addresses L2 — optional)
5. **Keep the local check suite green** (`ruff`, `mypy`, `pytest`, `runner`, `regression`, `inspect`) alongside the Phase 7 gate. (Addresses L4)

---

## 11. Historical Readiness Decision

**Is Prisma ready to begin Operational Engineering (Phase 7)?**

**YES.**

**Why.** The foundation the milestone claimed was genuinely present and internally consistent: the architecture held, every completed phase met its objective without leaking future scope, the repository was clean, and the evaluation substrate (golden cases, committed baseline, prompt fingerprint, deterministic metrics, informational regression, runtime evidence) was exactly what a CI/CD evaluation gate is built on. The observations raised were maintainability-level — a private-import coupling, a duplicated fallback path, and minor documentation drift — none of which blocked Phase 7 or required architectural change. The readiness was real; the cleanups were the responsible next tidy-up, not a precondition.

---

## 12. Final Statement

Prisma was a mature, disciplined local-first LLM engineering foundation at the reviewed commit. It demonstrated the operational layer around RAG and bounded agent workflows — grounded retrieval, bounded autonomy, golden-case evaluation, prompt regression, and privacy-preserving runtime observability — integrated in a single reproducible repository with boundaries that were documented, enforced, and tested. Its maturity showed most in its restraint: it built only the approved phases, deferred what belonged to later, and stated its limits plainly. The repository was ready to move from Foundation Engineering into Operational Engineering, carrying a short and well-understood list of small improvements rather than any structural debt.

---

## Validation Checklist

- [x] All completed phases (0–6) reviewed for objectives, leakage, and coherence — Section 4.
- [x] README reviewed — Sections 5, 8.
- [x] Architecture reviewed (architecture doc, project plan, ADRs) — Section 2.
- [x] Documentation reviewed (README, DEVELOPMENT, ADRs, phase plans, milestone) — Section 5.
- [x] `AGENTS.md` reviewed — Sections 4, 5.
- [x] Milestone reviewed — Sections 1, 4, 5.
- [x] Repository structure and cleanliness reviewed — Section 3.
- [x] Evaluation foundation reviewed — Section 7.
- [x] Constraints honored: no code, documentation, or asset modified; no new architecture proposed; no product features, redesign, history rewrite, or SaaS ideas introduced.

---

```text
Overall Result:

PASS WITH OBSERVATIONS
```

**Rationale for the result.** The engineering foundation was complete, coherent, clean, and Phase-7-ready at the reviewed commit: architecture integrity held, all phases met their objectives with no future-phase leakage, the repository was disciplined, and the evaluation substrate was reliable. The result was qualified with "OBSERVATIONS" — rather than an unqualified PASS — because of two real, non-blocking maintainability findings (cross-module private-symbol coupling in the workflow runner; a duplicated request/response path and validation retained behind a config flag) and minor documentation drift in `DEVELOPMENT.md` and the README roadmap. None of these gated the transition to Operational Engineering, and none required architectural change.
