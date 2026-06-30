# Prisma - Project Plan v0.1

> Production LLM Engineering Platform
> Planning document only. No application code, source layout, infrastructure files, tests, or package metadata are defined here as final implementation.

**Status:** Draft v0.1
**Date:** 2026-06-30
**Document:** PRISMA_PROJECT_PLAN_v0.1.md
**Audience:** developers, AI engineers, ML engineers, technical reviewers, and maintainers

---

## 0. How to Read This Document

This is the planning source for what Prisma is, why it exists, and the order in which it should be built. It deliberately stops short of implementation. Later design docs, ADRs, and pull requests should be traceable back to decisions recorded here.

The guiding instinct throughout: one focused, reproducible engineering system is more valuable than a broad set of unfinished demos. When a choice is between more features and more discipline around what already exists, this plan chooses discipline.

---

## 1. Vision

Prisma is a **local-first, reproducible platform for production-grade LLM systems**. It answers questions over a document corpus using retrieval and bounded agent workflows, and it treats the LLM application like production software: answers are traceable, prompt changes are regression-tested, and deployment gates are backed by evaluation results.

The repository should read like an engineering system, not an AI demo. A reader cloning the repo should be able to:

1. Run the MVP locally with no hosted database.
2. Ask a question and receive a cited, traceable answer.
3. Run the evaluation suite and inspect quality signals.
4. Understand the architecture quickly from the documentation.

Prisma is not another "chat with your PDF" wrapper. Retrieval and generation are only part of the system. The differentiator is the operational layer around them: evaluations, prompt regression, observability, cost and latency budgets, and CI/CD gates.

**One-sentence vision:** Prisma is what a careful engineering team builds when it treats an LLM feature like production software, with tests, gates, traces, and reproducibility.

---

## 2. Project Objectives

Prisma exists to establish a credible, maintainable reference for production LLM engineering. The project should make key engineering decisions explicit, keep the MVP runnable on a local machine, and demonstrate how quality controls fit into the development workflow for RAG and agent systems.

Primary objectives:

- **Production-readiness.** Model calls, retrieval, prompts, traces, and evaluations are treated as operational surfaces, not incidental details.
- **Reproducibility.** The MVP should run locally from a clean checkout without Supabase or other hosted infrastructure.
- **Evaluation discipline.** Changes to prompts, retrieval behavior, and agent workflow should be measurable against golden data and recorded baselines.
- **Maintainability.** Retrieval, reasoning, serving, evaluation, and observability should have clear boundaries so the system can evolve without becoming brittle.
- **Technical credibility.** The repository should be a public technical artifact that demonstrates engineering judgment through working systems, scoped non-goals, and documented tradeoffs.

---

## 3. Intended Readers

| Reader | What they look for in Prisma | What the repo should provide |
|---|---|---|
| **Developers** | A clear local setup path and understandable system boundaries | Concise README, setup docs, architecture notes, and runnable commands |
| **AI Engineers** | Practical RAG, agent workflow, context engineering, and prompt-regression patterns | Evaluation harness, prompt versioning, bounded agent workflow design |
| **ML Engineers** | Measurement discipline, reproducibility, and operational quality controls | Golden datasets, metric definitions, deterministic runs, and CI/CD gates |
| **Technical Reviewers** | Sound scope control and well-justified design decisions | This plan, ADRs, roadmap, honest non-goals, and visible tradeoffs |
| **Maintainers** | A codebase that can accept changes safely over time | Modular boundaries, regression checks, observability, and clear contribution rules |

Design implication: the repository must serve two reading depths: a quick scan through the README and architecture notes, plus a deeper path through docs, evaluations, and implementation details.

---

## 4. High-Level Architecture

This is conceptual only: component boundaries, not file layout. The defining principle is clear separation between retrieval, reasoning, evaluation, and serving.

```text
                         +------------------------------+
                         |            Client            |
                         |   HTTP request or CLI call   |
                         +---------------+--------------+
                                         |
                              +----------v----------+
                              |      API Layer      |
                              | request/response,   |
                              | schema validation   |
                              +----------+----------+
                                         |
                         +---------------v----------------+
                         |        Agent Workflow          |
                         | plan, retrieve, reason, answer |
                         | bounded and traceable          |
                         +---+-----------------------+----+
                             |                       |
              +--------------v------+      +---------v----------+
              |   Retrieval Layer   |      |    LLM Provider    |
              | embed, search,      |      | provider-neutral   |
              | rank, assemble      |      | interface          |
              | context             |      +--------------------+
              +----------+----------+
                         |
              +----------v----------+
              |       Storage       |
              | Vector: Qdrant      |
              | Metadata/runs:      |
              | SQLite              |
              +---------------------+

   Cross-cutting:
   Observability: structured logs and traces
   Evaluation: golden datasets, metrics, eval harness
   Prompt regression: versioned prompts and diff-on-change tests
   CI/CD: automated checks for quality, cost, and latency regressions
```

**Components:**

- **API** - thin, typed HTTP surface. Validates input, delegates to the agent, and returns answers with citations and a trace id.
- **Agent Workflow** - bounded graph that can decide, retrieve, optionally re-retrieve, synthesize, and answer. It uses explicit state and avoids open-ended autonomy.
- **Retrieval** - ingestion, chunking, embedding, vector search, and context assembly. It should remain pluggable enough for later ranking improvements.
- **Storage** - local vector storage for embeddings and local relational storage for metadata, runs, traces, and evaluation results.
- **LLM Provider** - provider-neutral adapter so model vendors remain configuration choices.
- **Evaluation** - golden datasets, metric definitions, and a runner that produces a readable scorecard.
- **Prompt Regression** - versioned prompts and comparisons against recorded baselines.
- **Observability** - structured logging and step-level traces with timing, token, cost, and decision metadata.
- **CI/CD** - automated checks that can fail when quality, cost, or latency regress beyond defined thresholds.

---

## 5. Repository Roadmap

Phased so each phase ends with something demonstrable. Effort is estimated in focused engineering days for one developer.

### Phase 0 - Foundations and Repo Hygiene

- **Objective:** A clean, reproducible skeleton that runs and is pleasant to read.
- **Deliverables:** project structure, dependency management, configuration strategy, base README, contribution/dev docs, lint/format/typecheck setup, local run command.
- **Effort:** about 2 days
- **Dependencies:** none

### Phase 1 - Ingestion and Indexing

- **Objective:** Turn a document corpus into a searchable local vector index.
- **Deliverables:** document loader, chunking strategy, embedding step, Qdrant indexing, small sample corpus, idempotent re-index command.
- **Effort:** about 3 days
- **Dependencies:** Phase 0

### Phase 2 - Baseline RAG API

- **Objective:** A working, typed query endpoint that retrieves and answers with citations.
- **Deliverables:** endpoint, request/response schemas, retrieval to prompt to generation flow, citations, basic error handling.
- **Effort:** about 3 days
- **Dependencies:** Phase 1

### Phase 3 - Agent Workflow

- **Objective:** Replace the linear pipeline with a bounded agent workflow that can reason about retrieval.
- **Deliverables:** explicit state graph, decision/retrieve/synthesize nodes, bounded re-retrieval, context-budget logic, trace ids threaded through the run.
- **Effort:** about 4 days
- **Dependencies:** Phase 2

### Phase 4 - Evaluation Harness

- **Objective:** Measure answer quality against golden data.
- **Deliverables:** golden question/answer dataset, metric definitions, eval runner, scorecard, recorded baseline.
- **Effort:** about 4 days
- **Dependencies:** Phase 3, though part of it can work against Phase 2 output

### Phase 5 - Prompt Regression

- **Objective:** Make prompt changes safe and reviewable.
- **Deliverables:** versioned prompt artifacts, regression run on prompt changes, baseline comparison, change report.
- **Effort:** about 2 days
- **Dependencies:** Phase 4

### Phase 6 - Observability and Cost/Latency Budgets

- **Objective:** Make every run inspectable and every run cheap and fast enough.
- **Deliverables:** structured logging, persisted traces, per-request token/cost/latency capture, budget thresholds, trace-viewer command or report.
- **Effort:** about 3 days
- **Dependencies:** Phase 3

### Phase 7 - CI/CD Gate

- **Objective:** Turn evals, regression checks, and budgets into automated quality gates.
- **Deliverables:** CI workflow running lint/type/test/eval/regression, gate policy, regression thresholds, visible status.
- **Effort:** about 2 days
- **Dependencies:** Phases 4 through 6

### Phase 8 - Reproducibility and Docs Polish

- **Objective:** One-command setup and documentation a first-time reader can follow.
- **Deliverables:** local stack orchestration, deterministic seed/data setup, architecture docs, demo recording, ADRs for key decisions, final README pass.
- **Effort:** about 3 days
- **Dependencies:** all prior phases

**Total focused effort:** about 26 engineering days.

---

## 6. MVP Definition

The smallest useful version is Phases 0 through 4 plus a thin slice of Phase 7.

> **MVP = local-first Agentic RAG with citations, a golden-dataset evaluation harness, and an automated evaluation check.**

Concretely, the MVP can:

1. Ingest and index a sample corpus locally.
2. Answer a question via an agent workflow, returning citations.
3. Run an evaluation suite producing a scorecard against golden data.
4. Run that suite through automation on code changes, starting as report-only if needed.

The MVP line exists because the evaluation harness is the cheapest feature that delivers the project's core thesis: LLM applications should be measured and gated like production software. Prompt regression, full observability, and deeper reproducibility polish can follow without weakening the core story.

**Explicitly out of MVP:** Supabase, authentication, hosted dashboard, production cloud deployment, and fine-tuning.

---

## 7. Future Extensions

Optional extensions should come after the core system is excellent. Each extension should be isolated and measurable.

**v2 candidates:**

- **Re-ranking** - add a cross-encoder or re-ranker stage and measure lift with the existing eval harness.
- **Hybrid retrieval** - combine dense and keyword search, then prove the impact through evaluations.
- **Multi-provider matrix** - run the eval suite across multiple model providers and publish a comparison scorecard.
- **Minimal UI** - a small read-only interface for asking questions and inspecting traces.

**v3 candidates:**

- **LLM-as-judge eval** - add a judged-quality metric alongside deterministic ones, with calibration notes.
- **Online evaluation and feedback loop** - capture real queries and periodically re-score.
- **Caching layer** - semantic or result caching with measured cost savings.
- **Optional cloud deploy** - a documented deployment path that remains separate from the local-first default.

Guardrail: no extension ships without an evaluation story. If a feature cannot be measured by the harness, it is probably not ready.

---

## 8. Engineering Principles

- **Local-first.** The MVP runs on a laptop with no hosted services.
- **Reproducible.** Same inputs should produce comparable setup and evaluation results.
- **Testable.** Component tests and system evaluations are first-class quality controls.
- **Observable.** Every request should produce a trace that explains what happened.
- **Modular.** Retrieval, reasoning, evaluation, and serving should remain separable.
- **Provider-neutral.** The LLM vendor should be a configuration detail behind an adapter.
- **Production-oriented.** Gates, budgets, and CI/CD reflect how reliable systems ship.
- **Honest scope.** Non-goals are documented and defended.
- **Quality over quantity.** Fewer finished capabilities are better than many unfinished ones.

---

## 9. Success Criteria

The project is ready for v1 when all of these hold:

**Functional**

- [ ] One documented command brings up the full local stack from a clean checkout.
- [ ] A documented command ingests the sample corpus and builds the index.
- [ ] The query endpoint returns an answer with citations and a trace id.
- [ ] The agent workflow performs bounded re-retrieval on at least one example.

**Quality and Operations**

- [ ] An eval suite runs against a golden dataset and emits a scorecard with at least three defined metrics.
- [ ] A recorded baseline exists and prompt changes trigger regression comparison.
- [ ] Every request trace is persisted and viewable.
- [ ] Per-request cost and latency budgets are defined and checked.
- [ ] CI/CD runs lint, type, unit, eval, and regression checks and can block regressions.

**Documentation**

- [ ] README communicates the project quickly and links to deeper docs.
- [ ] Key decisions are captured as short ADRs.
- [ ] A first-time reader can run the project end-to-end using only the docs.

---

## 10. Risks

### Technical

- **Eval flakiness and non-determinism.** LLM outputs vary, and naive metrics can be noisy. Mitigation: prefer deterministic or structural metrics first, fix temperature where possible, and treat LLM-as-judge as a later extension.
- **Provider and SDK churn.** LLM and framework APIs move quickly. Mitigation: keep provider adapters thin and dependencies pinned.
- **Agent over-complexity.** Agent graphs can grow beyond their value. Mitigation: keep the graph bounded and make each node's role explicit.
- **Local resource limits.** Vector storage, embeddings, and model calls can strain a laptop. Mitigation: keep the sample corpus small and document resource expectations.

### Scope

- **Feature creep.** The project can drift into a broad teaching system instead of a focused engineering platform. Mitigation: keep phase boundaries clear and require evaluation coverage for new capabilities.
- **Polish deferred forever.** It is easy to keep adding features and never finish docs. Mitigation: keep reproducibility and docs polish as v1 requirements.

### Complexity

- **Operational layer only partially implemented.** A broken quality gate is worse than a missing one. Mitigation: land each operational feature completely, with report-only gates allowed before blocking gates.
- **Over-engineering.** Too much machinery on a small problem can obscure the core value. Mitigation: match system complexity to a believable problem size and document why each piece exists.

### Reproducibility

- **Setup fragility.** If the project cannot run from a clean checkout, the local-first claim fails. Mitigation: validate setup regularly and keep the MVP free of hosted dependencies.

---

## 11. Estimated Timeline

Focused effort from the roadmap totals about 26 engineering days. A part-time schedule of about three focused days per week maps roughly as follows:

| Milestone | Phases | Focused days | Calendar at about 3 days/week |
|---|---|---|---|
| **Skeleton runs** | 0 | 2 | Week 1 |
| **Indexing works** | 1 | 3 | Week 1-2 |
| **Baseline RAG API** | 2 | 3 | Week 2-3 |
| **Agent workflow** | 3 | 4 | Week 3-4 |
| **MVP complete** | 4 plus Phase 7 slice | 5 | Week 5-6 |
| **Prompt regression** | 5 | 2 | Week 6 |
| **Observability and budgets** | 6 | 3 | Week 7 |
| **Full CI/CD gate** | 7 | 2 | Week 8 |
| **Reproducibility and docs polish** | 8 | 3 | Week 8-9 |

- **MVP:** about 6 calendar weeks.
- **v1:** about 9 calendar weeks.

Treat the MVP date as the first commitment and everything after as incremental production hardening.

---

## 12. Recommended Tech Stack

| Technology | Role | Why it belongs |
|---|---|---|
| **Python** | Primary language | Strong ecosystem for AI and ML engineering. |
| **FastAPI** | API layer | Typed, async-friendly HTTP surface with Pydantic integration. |
| **Pydantic** | Schemas and validation | Typed boundaries for requests, responses, configs, and model outputs. |
| **LangGraph** | Agent workflow | Explicit, bounded, stateful workflow design. |
| **LangChain** | Integrations | Practical connectors for loaders, embeddings, and retrievers when used selectively. |
| **Qdrant** | Vector store | Local vector search with production-grade semantics. |
| **SQLite** | Metadata, runs, traces, eval records | Zero-config local persistence that fits reproducible development. |
| **Pytest** | Testing | Standard Python testing foundation for unit tests and evaluation runners. |
| **Docker / Docker Compose** | Reproducibility | Local orchestration for repeatable setup. |
| **GitHub Actions** | CI/CD | Public automation surface for evaluation and regression gates. |

**Provider-neutral note:** the LLM and embedding providers sit behind interfaces and are intentionally not hard-coded in this stack table. They are configuration choices consistent with the provider-neutral principle.

**Deliberately absent:** Supabase, authentication providers, hosted dashboards, and managed cloud services. These would add operational surface before the MVP needs them.
