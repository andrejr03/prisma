# Prisma - Repository Architecture v0.1

> Production LLM Engineering Platform
> Architectural blueprint only. This document defines how the repository is organised and which boundaries must hold. It does not implement code, create directories, or define source, infrastructure, CI, or package files.

**Status:** Draft v0.1
**Date:** 2026-06-30
**Document:** PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md
**Audience:** developers, AI engineers, ML engineers, technical reviewers, and maintainers
**Companion:** [PRISMA_PROJECT_PLAN_v0.1.md](PRISMA_PROJECT_PLAN_v0.1.md)

---

## 0. How to Read This Document

The project plan answers *what* Prisma is and *in what order* it should be built. This document answers a narrower, earlier question: *how should the repository be shaped so that the plan can be executed without the codebase decaying.*

It is deliberately implementation-independent. No filenames are named except inside the repository tree. No framework, library, or language API is treated as load-bearing. If FastAPI becomes something else, if Qdrant is swapped, if LangGraph is replaced, this document should still hold. It describes **boundaries and responsibilities**, which outlive tools.

The contract is the point. Once accepted, this document is the reference that pull requests, ADRs, and design docs are checked against. A change that violates a boundary defined here is a change to the architecture, and should be argued as such, not slipped in.

Throughout, the same instinct as the project plan applies: discipline over surface area. A directory that does one thing well is worth more than a directory that does five things vaguely.

---

## 1. Purpose

Repository architecture is decided before implementation because the cost of getting it wrong rises every day code exists. The first commit sets gravity. Once a module imports across a boundary, every later module follows that path, and the boundary is gone before anyone defends it.

Deciding structure first gives the project four things:

- **A shared mental model.** Contributors know where a thing goes before they write it. "Where does this belong?" has an answer that does not require a meeting.
- **Reviewable boundaries.** A reviewer can reject a change for crossing a line that was drawn on purpose, rather than negotiating taste case by case.
- **Reproducibility by construction.** When data, configuration, prompts, and code live in declared places, a clean checkout behaves the same on every machine. Local-first only works if there is nothing hidden.
- **Survivability.** Prisma is intended to remain legible years from now, across multiple implementation iterations. Tools will be replaced. The skeleton should not have to be.

This document exists so that the repository starts correct rather than being refactored toward correctness under pressure later. The cheapest architecture decision is the one made before there is code to migrate.

---

## 2. Repository Philosophy

The architecture is shaped by a small set of principles. Where they conflict, simplicity and clarity win.

- **Boundary-first, feature-aware.** Prisma is not organised by technical layer alone, nor by feature alone. Top-level directories separate *kinds of responsibility* (application code, data, evaluation, prompts, operational scripts, docs). Inside the application, organisation may follow the system's natural seams — retrieval, agent workflow, providers, persistence. The repository optimises for "I can find the boundary," not "everything of one file type lives together."

- **Explicit boundaries.** Every boundary in this document is named and directional. Implicit coupling is treated as a defect. If two parts of the system need to talk, the path between them is declared, not discovered.

- **Low coupling, high cohesion.** A directory's contents should change together and for the same reasons. Things that change for different reasons live apart. The test of a good boundary is that a change on one side rarely forces a change on the other.

- **Data is not code.** Prompts, datasets, golden answers, baselines, and configuration are *assets*. They are versioned, reviewed, and diffed, but they are never executable logic and never import application code. This separation is load-bearing for reproducibility and regression testing.

- **Reproducibility.** Anything required to reproduce a run — sample data, configuration shape, prompt versions, evaluation baselines — lives in the repository in a declared location. Nothing essential lives only on a developer's machine.

- **Local-first.** The default execution model assumes a laptop and no hosted services. Hosted or cloud concerns, if they ever arrive, are isolated and optional, never woven into core paths.

- **Provider neutrality.** Model and embedding vendors are reached only through adapters. No directory outside the adapter boundary may name a provider, import a provider SDK, or assume a provider's behaviour.

- **Evaluation-first.** Evaluation is a first-class part of the repository, not a test afterthought. Evaluation assets and harnesses have their own home, and new capability is expected to arrive with an evaluation story.

- **Documentation-first.** The repository is a technical artifact meant to be read. Architecture, decisions, and plans are written down and kept current, because an unread system cannot be maintained.

---

## 3. Proposed Repository Structure

The following tree is the proposed top-level shape. It is a definition, not an instruction to create anything. Comments state each directory's single responsibility; Section 4 expands them.

```text
prisma/
├── app/                  # Application code: API, agent workflow, retrieval, provider adapters, persistence, observability
├── prompts/              # Versioned prompt assets (data, not code)
├── configs/              # Declarative configuration: defaults, profiles, provider/runtime config shapes (no secrets)
├── datasets/             # Input corpora and sample data used by ingestion and runs
├── evals/                # Evaluation harness, metric definitions, golden datasets, baselines, scorecards
├── tests/                # Unit, integration, and end-to-end tests for application code
├── scripts/              # Operational entry points and one-shot utilities (orchestration only, no business logic)
├── docker/               # Local orchestration and image definitions for reproducible setup
├── docs/                 # Architecture, ADRs, plans, design docs, RFCs, and reader-facing documentation
├── .github/              # CI/CD workflows and repository automation
├── README.md             # Entry point: what Prisma is, how to run it, where to read next
└── ...                   # Root-level project metadata and tooling configuration (defined at implementation time)
```

Notes on the shape:

- **`observability` is not a top-level directory.** Logging and tracing are a cross-cutting concern of the running application and live as a component *inside* `app/`, behind the persistence and infrastructure boundaries. Promoting it to top level would imply it is a separate product surface; it is not.
- **Generated artifacts** (vector indexes, run records, trace stores, scorecard outputs) are runtime state. They are not source and do not get their own committed top-level directory; their on-disk location is a configuration concern, and they are excluded from version control.
- **The `...` placeholder** stands for root-level tooling and metadata (dependency, lint, type, and ignore configuration) whose concrete form is intentionally deferred to implementation. Its existence is acknowledged; its contents are out of scope here.

The set is intentionally small. Each new top-level directory must justify itself against an existing one; the default answer to "should this be a new top-level directory" is no.

---

## 4. Directory Responsibilities

Each top-level directory has exactly one responsibility. For each: its purpose, who owns it, what it may contain, and what it must not.

### `app/`

- **Purpose:** All executable application logic — the running system. Internally organised by the system's seams: presentation/API surface, agent workflow, retrieval, provider adapters, persistence, and observability.
- **Ownership:** Application and AI engineers.
- **Allowed:** Business logic, typed boundaries, the agent workflow, retrieval logic, provider adapters, persistence access, and observability instrumentation.
- **Forbidden:** Hardcoded prompts (they live in `prompts/`), hardcoded secrets, direct provider SDK use outside the adapter boundary, test code, evaluation logic, and operational orchestration that belongs in `scripts/`.

### `prompts/`

- **Purpose:** The canonical, versioned home for prompt assets. Prompts are treated as data the system loads, not as strings embedded in code.
- **Ownership:** AI engineers, with review from anyone whose behaviour a prompt change affects.
- **Allowed:** Prompt templates, prompt metadata, and version history of prompts.
- **Forbidden:** Executable logic, provider-specific code, application imports, and secrets.

### `configs/`

- **Purpose:** Declarative configuration: default values, named profiles (e.g. local vs CI), the *shape* of provider and runtime configuration, and threshold definitions.
- **Ownership:** Maintainers, with input from whoever owns the configured component.
- **Allowed:** Non-secret declarative configuration and documented defaults.
- **Forbidden:** Secrets and credentials, executable logic, and per-developer machine state.

### `datasets/`

- **Purpose:** Input data — the sample corpus and any source documents that ingestion consumes.
- **Ownership:** AI/ML engineers.
- **Allowed:** Small, license-clear sample corpora and the data ingestion reads.
- **Forbidden:** Evaluation ground truth (that is `evals/`), generated indexes or embeddings (runtime state), application code, and large or unlicensed data.

### `evals/`

- **Purpose:** The evaluation system: the harness, metric definitions, golden datasets, recorded baselines, and emitted scorecards. The home of evaluation-first development.
- **Ownership:** ML/AI engineers.
- **Allowed:** Evaluation runners, metric definitions, golden question/answer sets, expected outputs, regression baselines, and scorecard formats.
- **Forbidden:** Business logic that belongs in `app/`, dependence on live production state, and provider-specific assumptions. Evaluation orchestrates and measures the application across its public boundary; it does not reimplement it.

### `tests/`

- **Purpose:** Automated verification of application code — unit, integration, and end-to-end.
- **Ownership:** Whoever writes the code under test.
- **Allowed:** Test code and fixtures for `app/`.
- **Forbidden:** Being depended on by `app/`, and standing in for evaluation. Quality measurement of model output is `evals/`'s job; correctness of code is `tests/`'s job.

### `scripts/`

- **Purpose:** Thin operational entry points: setup, ingestion triggers, index rebuilds, eval invocation, and similar one-shot utilities.
- **Ownership:** Maintainers.
- **Allowed:** Orchestration that wires together capabilities already implemented in `app/` or `evals/`.
- **Forbidden:** Business logic. A script must call into application code; logic that grows inside a script is a defect and belongs in `app/`. Scripts are not allowed to become a second, undocumented application.

### `docker/`

- **Purpose:** Local orchestration and image definitions that make setup reproducible from a clean checkout.
- **Ownership:** Maintainers.
- **Allowed:** Container and local-stack orchestration definitions.
- **Forbidden:** Application logic, secrets, and anything that makes local-first execution depend on hosted services.

### `docs/`

- **Purpose:** Reader-facing and decision-facing documentation: architecture, ADRs, plans, design docs, and future RFCs.
- **Ownership:** Whoever makes the decision being documented; maintainers keep it coherent.
- **Allowed:** Prose, diagrams, decision records, and planning documents.
- **Forbidden:** Implementation logic, executable source, and being the place where behaviour is *defined* rather than *described*.

### `.github/`

- **Purpose:** CI/CD workflows and repository automation that run quality, evaluation, and regression gates.
- **Ownership:** Maintainers.
- **Allowed:** Automation that invokes existing capabilities (lint, type, test, eval, regression) and policy for gates.
- **Forbidden:** Business logic, and embedding behaviour that should live in `app/`, `scripts/`, or `evals/`. CI orchestrates; it does not implement.

### `README.md`

- **Purpose:** The front door. Says what Prisma is, how to run it locally, and where to read next.
- **Ownership:** Maintainers.
- **Allowed:** Concise orientation and links into `docs/`.
- **Forbidden:** Becoming the architecture document or the full manual.

---

## 5. Dependency Rules

Dependencies flow in declared directions only. The governing rules:

1. **`app/` is the only home of business logic.** Nothing depends *on* `tests/`, and `app/` never imports `tests/` or `evals/`.
2. **`tests/` and `evals/` may depend on `app/`, never the reverse.** Verification and measurement observe the system; the system never observes its observers.
3. **`prompts/`, `configs/`, and `datasets/` are data.** They depend on nothing and import nothing. `app/` and `evals/` *read* them; they never read back.
4. **`evals/` reaches the application across its public boundary only.** It does not reach into internal components or share private state with `app/`.
5. **`scripts/`, `docker/`, and `.github/` are orchestration.** They may invoke `app/` and `evals/` and read data directories. They contain no business logic and are never depended on by `app/`.
6. **`docs/` depends on nothing and is depended on by nothing at runtime.** It describes; it never executes.
7. **Provider SDKs are reachable only from the provider-adapter boundary inside `app/`.** No other directory may import them.

### Dependency matrix

Rows may depend on columns marked ✅. Blank means must-not-depend.

| ↓ depends on → | app | prompts | configs | datasets | evals | tests | scripts | docker | docs | .github |
|---|---|---|---|---|---|---|---|---|---|---|
| **app**     | —  | ✅ | ✅ | ✅ |    |    |    |    |    |    |
| **prompts** |    | —  |    |    |    |    |    |    |    |    |
| **configs** |    |    | —  |    |    |    |    |    |    |    |
| **datasets**|    |    |    | —  |    |    |    |    |    |    |
| **evals**   | ✅ | ✅ | ✅ | ✅ | —  |    |    |    |    |    |
| **tests**   | ✅ | ✅ | ✅ | ✅ |    | —  |    |    |    |    |
| **scripts** | ✅ | ✅ | ✅ | ✅ | ✅ |    | —  |    |    |    |
| **docker**  |    |    | ✅ |    |    |    | ✅ | —  |    |    |
| **docs**    |    |    |    |    |    |    |    |    | —  |    |
| **.github** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |    | —  |

The shape to notice: data columns (`prompts`, `configs`, `datasets`) receive arrows but send none. `app` is depended on widely but depends only on data. `docs` is an island. This is the intended gravity.

---

## 6. Layer Boundaries

Inside `app/`, responsibility is organised as conceptual layers with a single downward flow of control. A layer may call the layer below it; it may not reach upward or skip past a layer to grab something deeper than its immediate need.

```text
   Presentation        user-facing surface (CLI, and any future read-only UI)
        │
        ▼
       API              typed request/response boundary, validation, trace-id issuance
        │
        ▼
  Agent Workflow        bounded plan/retrieve/reason/answer orchestration with explicit state
        │
        ▼
    Retrieval           ingestion, chunking, embedding, search, ranking, context assembly
        │
        ▼
 Provider Adapters      provider-neutral interface to model and embedding vendors
        │
        ▼
   Persistence          vector storage, metadata, runs, traces, evaluation records
        │
        ▼
   Evaluation           measurement of outputs against golden data (consumes the system across its boundary)
        │
        ▼
  Infrastructure        cross-cutting observability, configuration access, runtime concerns
```

Layer responsibilities:

- **Presentation** translates between humans and the API. It holds no business logic; it formats requests and renders responses.
- **API** is the typed contract. It validates input, issues a trace id, delegates to the workflow, and shapes the response. It never reasons about retrieval or models directly.
- **Agent Workflow** is the system's brain: a bounded, stateful graph that decides, retrieves, optionally re-retrieves, synthesises, and answers. It coordinates lower layers; it does not embed their internals.
- **Retrieval** owns everything about turning a corpus into relevant context. It calls provider adapters for embeddings and persistence for storage.
- **Provider Adapters** are the only place a vendor exists. Above this line, the system speaks in neutral terms; below it, a specific provider is reached. Swapping a provider is a change confined to this layer.
- **Persistence** owns durable state: embeddings, metadata, runs, traces, eval records. Layers above ask it to store and fetch; they do not know its backend.
- **Evaluation** is shown as a layer to fix its position in the flow, but architecturally it lives in `evals/` and observes the running system through its public boundary. It depends downward on nothing it should not see and never feeds state back up.
- **Infrastructure** is cross-cutting: observability (structured logs, step traces), configuration access, and runtime concerns. It is available to layers but is the lowest concern and must not leak upward as business assumptions.

The rule that makes layers worth having: **control flows down, and knowledge does not flow up.** A lower layer never imports or assumes a higher one. The API does not know who called it; the provider adapter does not know it serves an agent.

---

## 7. Configuration Strategy

Configuration is declarative, layered, and free of secrets. Four concerns are kept separate:

- **Defaults and profiles (`configs/`).** Committed, declarative, non-secret. Defaults define how Prisma behaves with no overrides. Named profiles (for example local and CI) capture environment-shaped differences. These are reviewed like any other asset.
- **Environment variables.** The mechanism for machine- and run-specific values and for injecting secrets at runtime. They override file defaults. The *shape* of expected variables is documented; their values are not committed.
- **Secrets.** Never committed, never in `configs/`, never in `prompts/`, never in code. Provider keys and credentials arrive only through the environment at runtime. The repository documents which secrets exist and how they are supplied, and nothing more.
- **Provider configuration.** Choosing a model or embedding vendor is configuration, not code. The provider is selected through config and reached through the adapter boundary, consistent with provider neutrality. No core path names a provider.

**Precedence (lowest to highest):** committed defaults → selected profile → environment variables. Higher layers override lower ones; secrets enter only at the top, only from the environment.

The principle: a clean checkout runs on defaults; a specific environment is reached by *adding* configuration, never by editing core code.

---

## 8. Prompt Management

Prompts are versioned data assets with the same seriousness as code, governed from `prompts/`.

- **Prompts are data, never code.** They are loaded by the application, not embedded in it. No prompt string is hardcoded in `app/`. This keeps prompt changes visible, reviewable, and independently versionable.
- **Versioning.** Prompts carry explicit versions. A behavioural change to a prompt is a new version, not a silent edit, so that any answer or evaluation result can be traced to the exact prompt that produced it.
- **Ownership.** AI engineers own prompt content, but a prompt change is reviewed by anyone whose surface it affects, because a prompt edit is a behaviour change.
- **Review process.** Prompt changes are reviewed like code changes: diffed, discussed, and approved. The fact that a prompt is text does not make its change low-stakes.
- **Regression.** Every prompt change is expected to run against the evaluation harness and be compared to the recorded baseline. A prompt change that moves quality is a result to record, not a surprise to discover later. This is the link between `prompts/` and `evals/`: prompts are versioned here, and their effect is measured there.

---

## 9. Evaluation Assets

Evaluation assets live in `evals/` and define what "good" means, separately from the code that tries to be good.

- **Golden datasets.** Curated question/answer (or input/expected) pairs that represent correct behaviour. They are the ground truth and are kept distinct from `datasets/`, which holds *input* data the system reads, not the answers it is judged against.
- **Benchmarks.** Defined task sets the system is measured on, stable enough that results compare across time and across changes.
- **Expected outputs.** The reference results a run is scored against, versioned so that "expected" is never ambiguous.
- **Regression baselines.** Recorded prior results that new runs are compared to. A baseline is the memory that lets the project detect drift rather than rediscover it.
- **Metrics.** Explicit metric definitions — what is measured and how — preferring deterministic and structural metrics first, with judged metrics treated as a later, calibrated addition. Metric definitions are assets, so that a score's meaning is fixed and reproducible.

The boundary that protects all of this: **evaluation must not depend on production or live runtime state.** Evaluation runs from declared assets against the system's public boundary. If an eval result depends on something not captured in the repository, it is not reproducible, and reproducibility is the point.

---

## 10. Testing Strategy

Testing is layered, and each layer answers a different question. Tests of code correctness live in `tests/`; measurement of model quality lives in `evals/`. The two are kept distinct on purpose.

- **Unit.** Verify a single component in isolation — a retrieval step, an adapter contract, a workflow node. Fast, deterministic, no external services.
- **Integration.** Verify that components cooperate across a boundary — retrieval to persistence, workflow to adapter — using local resources only.
- **Evaluation.** Measure answer *quality* against golden data via the `evals/` harness. This is not a pass/fail unit test; it is a scorecard. It belongs to evaluation, not to `tests/`.
- **Regression.** Detect change against a recorded baseline — for prompts, retrieval behaviour, and workflow. Regression is the safety net that makes change reviewable rather than risky.
- **End-to-end.** Exercise the full local path from request to cited answer with a trace, proving the system holds together from the outside.

The dividing line to keep sharp: **`tests/` proves the code is correct; `evals/` measures whether the output is good.** Collapsing them — using unit tests to assert model quality, or treating eval scores as build-breaking unit assertions — erodes both. Each stays in its home.

---

## 11. Documentation Strategy

Documentation is organised by *intent*, all under `docs/` except the README.

- **README (root).** Orientation only. What Prisma is, how to run it locally, and where to read next. It points inward; it is not the manual.
- **Architecture (this document and successors).** How the repository and system are shaped and which boundaries hold. Describes structure; never defines behaviour.
- **ADRs (Architecture Decision Records).** Short, dated records of a single decision and its rationale. They capture *why*, so a future reader does not have to reverse-engineer intent. An ADR is immutable once accepted; it is superseded, not edited.
- **Plans.** Forward-looking scope and sequencing, such as the project plan. They say what will be built and in what order.
- **Design docs.** Focused proposals for how a specific component will work, written before that component is built and traceable back to plans and ADRs.
- **Future RFCs.** A path for proposing larger changes for discussion before commitment, used when a change is big enough to deserve debate.

The discipline: documentation *describes* and *decides*, but never *executes*. Behaviour is defined in `app/`, `prompts/`, `configs/`, and `evals/`. If a document is the only place something is true, that thing is not yet implemented.

---

## 12. Repository Evolution

The architecture is meant to grow without decaying. Three questions govern growth.

**How new modules are added.** A new capability first finds its home in the existing structure. New application logic is a component inside `app/`, organised along the existing seams; new prompts go to `prompts/`; new measurement goes to `evals/`. A new *top-level* directory is the exception, not the reflex: it is justified only when a genuinely new kind of responsibility appears that no existing directory can hold without violating its single purpose. The default answer to "new top-level directory?" is no.

**How architectural drift is avoided.** Drift is the slow erosion of boundaries under deadline pressure. It is countered by making boundaries reviewable: this document is the reference, the dependency matrix in Section 5 is checkable, and a change that crosses a declared line is treated as an architecture change requiring an explicit decision (and usually an ADR). The CI gates and regression baselines make behavioural drift visible the same way the matrix makes structural drift visible.

**How deprecated components are handled.** Removal is a first-class action, not abandonment. A component being retired is marked, its replacement is identified, and its removal is recorded — ideally in an ADR that explains what replaced it and why. Dead code, stale prompts, and orphaned eval assets are removed rather than left to confuse future readers. A repository that only ever adds becomes unreadable; pruning is maintenance.

---

## 13. Architectural Guardrails

These are the non-negotiable rules. They are stated in MUST / MUST NOT terms because they are the lines a review can reject a change for crossing.

- The `app/` layer **MUST** contain all business logic. Business logic **MUST NOT** live in `scripts/`, `docker/`, `.github/`, or `docs/`.
- Prompts **MUST** live in `prompts/` as versioned assets. They **MUST NOT** be hardcoded in application code.
- Provider and embedding SDKs **MUST** be reached only through the provider-adapter boundary. No directory outside that boundary **MUST** name a provider or import its SDK.
- Secrets **MUST** be supplied at runtime through the environment. They **MUST NOT** appear in `configs/`, `prompts/`, code, or version control.
- Evaluation **MUST** run from declared assets against the system's public boundary. It **MUST NOT** depend on live production or runtime state.
- `app/` **MUST NOT** depend on `tests/` or `evals/`. Verification observes the system; the system **MUST NOT** observe its verifiers.
- `prompts/`, `configs/`, and `datasets/` **MUST** remain data. They **MUST NOT** contain executable logic or import application code.
- Infrastructure and observability concerns **MUST** stay cross-cutting and below business logic. They **MUST NOT** leak into application logic as behavioural assumptions.
- The default execution path **MUST** remain local-first. Core paths **MUST NOT** require a hosted service.
- `docs/` **MUST** describe and decide only. It **MUST NOT** contain executable behaviour or be the sole place a behaviour is defined.
- New capability **MUST** arrive with an evaluation story where its quality is measurable. A capability that cannot be measured by the harness is **MUST NOT** be treated as production-ready.

---

## 14. Recommended Initial Repository Skeleton

This is the recommended *order* in which directories should eventually be created, aligned with the project plan's phases. It is a sequence, not an instruction to create anything now. Each directory is introduced only when the work that justifies it begins, so the structure grows with real need rather than appearing empty.

1. **`docs/`** — already in use; decisions and architecture precede code.
2. **`README.md`** — the front door, early enough to orient the first contributor.
3. **`configs/`** — configuration strategy exists before anything reads configuration.
4. **`app/`** — introduced as the API and core paths begin (plan Phases 0–2), organised by seam from the start.
5. **`datasets/`** — when ingestion needs a sample corpus (plan Phase 1).
6. **`prompts/`** — when the first generation step needs a prompt to load (plan Phase 2).
7. **`tests/`** — alongside the first application code worth verifying.
8. **`evals/`** — when measurement against golden data begins (plan Phase 4).
9. **`scripts/`** — when repeated operations deserve a thin, declared entry point.
10. **`docker/`** — when reproducible local orchestration is needed (plan Phases 0/8).
11. **`.github/`** — when evals, regression, and budgets become automated gates (plan Phase 7).

The ordering principle: a directory appears the moment its single responsibility has real work, and not before. Boundaries are declared up front in this document; the folders that embody them arrive just in time.

---

## 15. Consistency Review

A check of this architecture against its own principles before it becomes a contract.

- **One responsibility per directory.** Each top-level directory in Section 4 has a single stated purpose with explicit forbidden contents. ✅
- **No directory overlaps another.** The two adjacencies that could blur are separated explicitly: `datasets/` (input data) versus `evals/` (ground truth), and `tests/` (code correctness) versus `evals/` (output quality). Observability is placed inside `app/` rather than competing as a top-level directory. ✅
- **Dependency directions are consistent.** The narrative rules (Section 5), the dependency matrix, and the layer flow (Section 6) agree: data is depended upon but depends on nothing; `app/` depends only on data; verification depends on `app/` and never the reverse; orchestration depends inward and is depended on by nothing. ✅
- **Local-first is preserved.** No core path requires a hosted service; `docker/` and configuration support local execution; hosted concerns are explicitly excluded from default paths. ✅
- **Provider neutrality is preserved.** Providers exist only behind the adapter boundary; a guardrail forbids naming or importing providers elsewhere; provider choice is configuration. ✅
- **Evaluation-first is maintained.** `evals/` is a first-class top-level directory; evaluation assets have a defined home; new capability requires an evaluation story by guardrail. ✅
- **Not over-engineered.** The top-level set is small (ten directories plus README), no speculative layers are introduced, and Section 12 makes "no new top-level directory by default" an explicit rule. The structure matches a believable single-developer, local-first project. ✅

No internal contradictions were found between sections. Terminology is consistent with the companion project plan.

---

## 16. Architecture Decision Summary

- The repository is organised **boundary-first**: top-level directories separate *kinds of responsibility*, and `app/` is internally organised by the system's natural seams.
- **Code and data are strictly separated.** `prompts/`, `configs/`, and `datasets/` are versioned assets that import nothing; `app/` holds all business logic and depends only on data.
- **Dependencies flow one way.** Verification (`tests/`, `evals/`) and orchestration (`scripts/`, `docker/`, `.github/`) depend on `app/`; `app/` depends on neither. The dependency matrix is the checkable form of this rule.
- **Layers inside `app/` flow downward only** — Presentation → API → Agent Workflow → Retrieval → Provider Adapters → Persistence, with Evaluation observing from outside and Infrastructure cross-cutting beneath.
- **Providers live only behind adapters; secrets live only in the environment; prompts live only in `prompts/`.** These three guardrails carry most of the architecture's long-term protection.
- **Evaluation is first-class and reproducible**, depending on declared assets and never on live state.
- The structure is **deliberately small** and grows just-in-time, with new top-level directories treated as exceptions requiring justification.
- The document is **implementation-independent** and intended to survive framework and provider changes across multiple iterations.

## 17. Open Questions

These are boundary questions worth resolving before or during early implementation. None block acceptance of the architecture.

1. **Generated-artifact location.** Indexes, run records, and trace stores are runtime state excluded from version control. Their on-disk root is a configuration concern — should it be a single declared working directory, or per-component? (Leaning: one declared, configurable working directory.)
2. **Prompts versus prompt code.** Prompts are data, but template *rendering* logic is code. Confirm that rendering lives in `app/` and `prompts/` holds only template content and metadata.
3. **Shared types across the data boundary.** Schemas describing the *shape* of config, prompt metadata, and eval records may be referenced by both `app/` and `evals/`. Decide whether these definitions live in `app/` (as the owner) or in a small shared location, without creating a back-dependency.
4. **Eval/test overlap at the edges.** End-to-end tests and evaluation runs both exercise the full path. Confirm the dividing line (correctness in `tests/`, quality in `evals/`) holds for cases that touch both.
5. **Future UI placement.** If a read-only UI arrives, does it sit inside `app/` as the Presentation layer or as a separate top-level surface? (Leaning: inside `app/` until it clearly warrants separation.)

## 18. Recommended Next Natural Step

Capture the load-bearing decisions from this document as short **ADRs** in `docs/` — at minimum: code/data separation, the provider-adapter boundary, the secrets-via-environment rule, and the evaluation-first guardrail. Doing so converts this blueprint's principles into individually citable decisions that pull requests can be checked against, and gives Phase 0 of the project plan a concrete, reviewable starting point before any application code is written.
