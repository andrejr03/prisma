# Prisma - Phase 0 Repository Skeleton Plan v0.1

> Production LLM Engineering Platform
> Planning document only. This document defines *what Phase 0 will create*. It does not create directories or files, implement code, or modify the repository.

**Status:** Draft v0.1
**Date:** 2026-06-30
**Document:** PRISMA_PHASE_0_REPOSITORY_SKELETON_PLAN_v0.1.md
**Audience:** developers, AI engineers, ML engineers, technical reviewers, and maintainers
**Companions:** [PRISMA_PROJECT_PLAN_v0.1.md](PRISMA_PROJECT_PLAN_v0.1.md), [PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md](PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md)

---

## 0. How to Read This Document

The Repository Architecture (approved) says *how the repository should be shaped*. This document is the bridge to implementation: it says *exactly which directories and files Phase 0 brings into existence, in what order, and why* — so that executing it is almost mechanical.

It is deliberately concrete where the architecture was abstract. It names files (which the architecture avoided), because Phase 0 is the moment those files acquire a location. It still implements nothing: every file's *content* is the job of the next task. This plan defines the skeleton; the implementation task fills it.

The governing instinct, inherited from both companions: **intentional minimalism.** A directory exists in Phase 0 only if it has immediate work. Everything speculative is explicitly deferred to the phase that needs it. The architecture's just-in-time rule is the law this plan obeys.

---

## 1. Purpose

Phase 0 turns an approved architecture into a physical, runnable skeleton. Its purpose is to establish the repository's foundations and hygiene so that Phase 1 can begin writing application code without first making structural decisions.

Phase 0 exists to:

- **Instantiate the boundaries on disk.** The architecture's directories and rules become real locations a contributor can put code into.
- **Make the project runnable and checkable.** Dependency management, formatting, linting, type-checking, and testing tooling are configured so quality controls exist from the first line of real code.
- **Preserve reproducibility from commit zero.** A clean checkout behaves identically everywhere because configuration shape and ignored runtime state are declared up front.
- **Avoid premature structure.** Equally important: Phase 0 does *not* create folders for work that has not started. An empty `evals/` is a lie about progress; Phase 0 refuses it.

Phase 0 is done when the repository is a clean, minimal, runnable foundation that matches the architecture and contains no implementation.

---

## 2. Phase 0 Scope

### In scope

- Root-level project tooling: ignore rules, dependency and tool configuration, editor consistency.
- The `app/` package **root** as the single source-of-truth package, so dependency management and a local run command have a target. Its internal seam subdirectories are **not** created here.
- `configs/` with a single base default configuration profile, establishing the configuration precedence model.
- `docs/` — already populated with planning documents; Phase 0 adds this plan and a short development/contribution document.
- A README pass so the front door reflects the actual local setup path.

### Explicitly NOT in scope

- **Any business logic.** No retrieval, no agent workflow, no provider adapters, no persistence behaviour.
- **The seam subdirectories of `app/`** (API, agent workflow, retrieval, provider adapters, persistence, observability). They arrive in Phases 1–6 with their code.
- **`datasets/`, `prompts/`, `evals/`, `tests/`, `scripts/`, `docker/`, `.github/`.** Each is deferred to the phase that first needs it (see §4 and the architecture's §14 ordering).
- **Secrets, provider selection, and `.env` material.** No provider is consumed until Phase 2, so nothing secret is needed yet.
- **CI/CD workflows.** Automation gates are Phase 7.
- **Container orchestration.** Reproducible container setup is Phase 8 (architecture §14 step 10).

The scope boundary is the same test used everywhere in this plan: *does it have immediate work in Phase 0?* If not, it is deferred.

---

## 3. Initial Repository State

Before Phase 0 begins, the repository contains documentation only:

```text
prisma/
├── README.md                                   # exists — project front door
└── docs/
    ├── PRISMA_PROJECT_PLAN_v0.1.md             # exists — what/why/order
    ├── PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md  # exists — approved architecture
    └── PRISMA_PHASE_0_REPOSITORY_SKELETON_PLAN_v0.1.md  # this document
```

There is no application code, no configuration, no tooling, and no version-control hygiene yet. The repository is a planning artifact. Phase 0's job is to add exactly the foundation needed to start building — and nothing more.

---

## 4. Repository Skeleton

The complete tree that should exist immediately after Phase 0. Items are tagged by kind.

```text
prisma/
├── app/                         # [DIR, NEW]     package root only — no seam subdirs yet
│   └── __init__.py              # [FILE, NEW]    package marker; makes app importable/runnable
├── configs/                     # [DIR, NEW]     declarative configuration home
│   └── defaults.<ext>           # [FILE, NEW]    base (lowest-precedence) default profile
├── docs/                        # [DIR, EXISTS]  authoritative documentation
│   ├── PRISMA_PROJECT_PLAN_v0.1.md                 # [DOC, EXISTS]
│   ├── PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md      # [DOC, EXISTS]
│   ├── PRISMA_PHASE_0_REPOSITORY_SKELETON_PLAN_v0.1.md  # [DOC, this]
│   └── DEVELOPMENT.md           # [DOC, NEW]     local setup, run, lint/type/test commands
├── README.md                    # [DOC, UPDATE]  front door, refreshed for real setup path
├── .gitignore                   # [FILE, NEW]    excludes runtime state, secrets, caches
├── pyproject.toml               # [FILE, NEW]    dependencies + lint/format/type/test config
└── .editorconfig                # [FILE, NEW]    cross-editor formatting consistency

# Future locations — intentionally absent in Phase 0, created in the noted phase:
#   datasets/   → Phase 1 (sample corpus for ingestion)
#   prompts/    → Phase 2 (first prompt the system loads)
#   tests/      → Phase 1 (first application code worth verifying)
#   evals/      → Phase 4 (evaluation harness and golden data)
#   scripts/    → when a repeated operation needs a thin entry point
#   docker/     → Phase 8 (reproducible local orchestration)
#   .github/    → Phase 7 (CI/CD quality gates)
```

Legend: **DIR** = directory, **DOC** = documentation, **FILE** = configuration/tooling, **NEW/EXISTS/UPDATE** = action, **Future locations** = declared-but-absent.

The `<ext>` for the defaults file is left to implementation; this plan fixes its *location and role*, not its format.

What the tree communicates by what it omits: there are no empty seam folders, no placeholder `evals/`, no speculative `scripts/`. The repository after Phase 0 should *feel* like a project that just started cleanly, not one with hollow scaffolding waiting to be filled.

---

## 5. Directory Creation Order

Only two directories are *created* in Phase 0 (`docs/` already exists). The order:

1. **`app/`**
   - **Why now:** It is the package root. Dependency management (`pyproject.toml`) and the local run command both need a package to target; without it, tooling has nothing to install or run.
   - **Why not later:** Deferring it would block the "local run command" and dependency-management deliverables of project-plan Phase 0.
   - **Dependencies:** None. It is the anchor the root tooling configures against.
   - **Bound:** Created as a package *root* only. Its seam subdirectories are deferred to Phases 1–6, honoring the architecture's just-in-time rule.

2. **`configs/`**
   - **Why now:** The configuration strategy is a Phase 0 deliverable. Establishing the base default profile fixes the precedence model (defaults → profile → environment) before any code reads configuration.
   - **Why not later:** The architecture (§14 step 3) places configuration before anything that reads it; introducing it after code already reads config invites ad-hoc configuration.
   - **Dependencies:** Conceptually anchored to `app/` as the eventual reader, but it imports nothing and can be created independently.

`docs/` requires no creation step (it exists); Phase 0 only *adds documents* to it (§6, §9).

No other directory is created. Each deferred directory's creation belongs to its own phase, listed in the skeleton's future-locations block.

---

## 6. File Creation Order

Files in the order they should be created, with purpose, mandatory and optional content, and whether they start empty. No file in Phase 0 starts empty — empty files are avoided by policy (§7).

1. **`.gitignore`**
   - **Purpose:** Keep runtime state, secrets, and tool caches out of version control from the first commit.
   - **Mandatory:** Patterns for generated artifacts (indexes, run/trace stores, scorecards), environment/secret files, language and tool caches, and OS cruft.
   - **Optional:** Editor-specific ignores.
   - **Starts empty:** No.

2. **`pyproject.toml`**
   - **Purpose:** Single source of truth for dependencies and for lint/format/type/test tool configuration.
   - **Mandatory:** Project metadata, dependency declarations, and configuration for the formatter, linter, type checker, and test runner.
   - **Optional:** Optional dependency groups (e.g. a dev group).
   - **Starts empty:** No.

3. **`app/__init__.py`**
   - **Purpose:** Mark `app/` as the importable, runnable package root.
   - **Mandatory:** Package marker presence (it makes the package real for tooling and the run command).
   - **Optional:** A version or minimal package-level metadata.
   - **Starts empty:** Effectively yes by content, but it is an intentional, justified marker — not placeholder clutter. It is the one file whose *existence* rather than *content* is the point.

4. **`configs/defaults.<ext>`**
   - **Purpose:** The lowest-precedence default configuration profile; anchors the precedence model.
   - **Mandatory:** Documented default values for the runtime concerns known at Phase 0; structure that later profiles and environment overrides extend.
   - **Optional:** Comments describing intended future keys.
   - **Starts empty:** No.

5. **`.editorconfig`**
   - **Purpose:** Enforce consistent indentation and line endings across editors with zero maintenance.
   - **Mandatory:** Baseline formatting rules.
   - **Optional:** Per-filetype overrides.
   - **Starts empty:** No.

6. **`docs/DEVELOPMENT.md`**
   - **Purpose:** Tell a contributor how to set up, run, and check the project locally — the project-plan "contribution/dev docs" deliverable.
   - **Mandatory:** Local setup steps, the run command, and the lint/format/type/test commands.
   - **Optional:** Contribution conventions and a pointer to the architecture's guardrails.
   - **Starts empty:** No.

7. **`README.md`** (update)
   - **Purpose:** Keep the front door accurate now that a real setup path exists.
   - **Mandatory:** A concise local quick-start and links to the planning, architecture, and development docs.
   - **Optional:** A short status note.
   - **Starts empty:** No (it already exists; this is a refresh).

---

## 7. Placeholder Policy

The default is **no empty directories and no placeholder files.** Phase 0 achieves this naturally: every directory it creates has real content.

- **`.gitkeep`:** Use only when a directory must exist for tooling but legitimately has no content yet. **Phase 0 needs none** — `app/` carries its package marker and `configs/` carries its defaults file. A `.gitkeep` is a smell that a directory was created before its work; if one seems necessary, reconsider whether the directory belongs in this phase at all.
- **Placeholder READMEs:** Prefer a short README over a `.gitkeep` *only* when a directory needs explanation but not yet content — and even then, prefer deferring the directory until it has content. **Phase 0 introduces no placeholder READMEs**, because it introduces no contentless directories.
- **Empty directories:** Justified only if a tool hard-requires the path before content exists. No such case arises in Phase 0.

The policy is a direct expression of intentional minimalism: the cleanest signal that a directory is real is that it contains something real.

---

## 8. Configuration Files

Each candidate configuration file is assigned **Phase 0**, **Later**, or **Never**, with justification.

| File | Decision | Justification |
|---|---|---|
| `.gitignore` | **Phase 0** | Runtime state and secrets must be excluded from the very first commit; retrofitting risks committing artifacts. |
| `pyproject.toml` | **Phase 0** | Single source of truth for dependencies *and* lint/format/type/test config — all Phase 0 deliverables. |
| `.editorconfig` | **Phase 0** | Cheap, zero-maintenance editor consistency; harmless and useful from day one. |
| `requirements.txt` | **Never (as a separate source)** | A second dependency source competes with `pyproject.toml` and invites drift. If an export is ever needed for a deploy target, it is generated, not authored. |
| `.env` | **Never (committed)** | Secrets enter only at runtime via the environment (architecture guardrail). The actual `.env` is never committed. |
| `.env.example` | **Later (Phase 2)** | Documents required environment variables; meaningless until a provider/secret is first consumed in Phase 2. Adding it now would document nothing. |
| Pre-commit hook config | **Later (optional)** | Useful convenience, but the lint/format/type tooling already exists via `pyproject.toml`; hooks can be added when contributor friction justifies them. Not required to start. |
| `Dockerfile` / compose | **Later (Phase 8)** | Reproducible container orchestration belongs to Phase 8 (architecture §14 step 10); local-first development does not require it to begin. |
| CI workflow files | **Later (Phase 7)** | Automation gates are Phase 7; introducing them now would gate nothing. |

The pattern: a configuration file belongs in Phase 0 only if it configures something that exists in Phase 0. Everything that configures future capability waits for that capability.

---

## 9. Documentation Introduced

After Phase 0, the following documents should exist. Those marked *exists* predate Phase 0; Phase 0 adds or refreshes the rest.

- **`README.md`** *(exists, refreshed)* — the front door; orientation plus a real local quick-start and links inward. Belongs because the project must be approachable in one read.
- **`docs/PRISMA_PROJECT_PLAN_v0.1.md`** *(exists)* — what Prisma is and the order of build. The source of phase definitions Phase 0 obeys.
- **`docs/PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md`** *(exists)* — the approved structural contract this plan instantiates.
- **`docs/PRISMA_PHASE_0_REPOSITORY_SKELETON_PLAN_v0.1.md`** *(this document)* — the bridge from architecture to the first implementation task.
- **`docs/DEVELOPMENT.md`** *(new)* — how to set up, run, and check the project locally; the project-plan "contribution/dev docs" deliverable. Belongs because a runnable skeleton is only useful if a reader can actually run it.

Deliberately *not* introduced in Phase 0: ADRs. The architecture recommended capturing key decisions as ADRs, and that remains the recommended next step (§ Recommended next step) — but ADRs record decisions and are not part of the *skeleton*. They can land immediately after Phase 0 without blocking it, and keeping them out preserves Phase 0's minimal, mechanical character.

---

## 10. Validation Checklist

To be checked after the Phase 0 implementation task runs:

- [ ] Every directory present after Phase 0 is one the architecture defines (`app/`, `configs/`, `docs/`).
- [ ] No deferred directory exists yet (`datasets/`, `prompts/`, `evals/`, `tests/`, `scripts/`, `docker/`, `.github/` are absent).
- [ ] `app/` contains only its package root — no seam subdirectories.
- [ ] No empty directories and no `.gitkeep` or placeholder READMEs exist.
- [ ] No business logic exists anywhere; `app/` holds only its package marker.
- [ ] `pyproject.toml` is the sole dependency source; no `requirements.txt`.
- [ ] No secrets, `.env`, or provider names are present in the repository.
- [ ] No CI workflows and no container files exist.
- [ ] `.gitignore` excludes runtime artifacts, secrets, and caches.
- [ ] `configs/` contains exactly one base default profile and no secrets.
- [ ] README and `DEVELOPMENT.md` describe a setup that actually works from a clean checkout.
- [ ] The planning, architecture, and Phase 0 documents remain the authoritative description of the system; nothing in code contradicts them.
- [ ] A reader could begin Phase 1 without making any structural decision this plan should have made.

---

## 11. Risks

- **Creating directories too early.** Building `evals/`, `tests/`, or `app/` seam folders now produces hollow scaffolding that misrepresents progress and rots.
  - *Mitigation:* The just-in-time rule (§4 future-locations) and the validation checklist explicitly forbid deferred directories.

- **Empty repository syndrome.** Over-correcting into a skeleton so bare it is not runnable, defeating the "foundation" purpose.
  - *Mitigation:* Phase 0 deliberately includes runnable tooling and a package root so the project is checkable from commit zero — minimal, but not inert.

- **Placeholder overload.** A spray of `.gitkeep` and stub READMEs to make folders "look populated."
  - *Mitigation:* The placeholder policy (§7) bans empty directories; Phase 0 needs zero placeholders by design.

- **Premature implementation.** Treating "local run command" as license to write real logic.
  - *Mitigation:* Scope (§2) limits `app/` to a package root; the validation checklist asserts no business logic exists.

- **Architectural drift at birth.** The skeleton quietly diverging from the approved architecture (e.g. a stray top-level directory, observability promoted to top level).
  - *Mitigation:* The skeleton (§4) is derived directly from the architecture; the checklist verifies every directory traces back to it.

- **Dependency-source duplication.** A `requirements.txt` appearing alongside `pyproject.toml`, splitting the source of truth.
  - *Mitigation:* §8 marks it Never; the checklist verifies its absence.

---

## 12. Deliverables

When the Phase 0 implementation task runs, it will produce exactly:

- **Two new directories:** `app/` (package root) and `configs/`.
- **Five new files:** `.gitignore`, `pyproject.toml`, `app/__init__.py`, `configs/defaults.<ext>`, `.editorconfig`.
- **One new document:** `docs/DEVELOPMENT.md`.
- **One refreshed document:** `README.md`.
- **No code, no seam subdirectories, no deferred directories, no placeholders, no secrets, no CI, no containers.**

The result is a clean, minimal, runnable foundation that matches the approved architecture and is ready for Phase 1 to add the first real application code.

---

## 13. Consistency Review

A check of this plan against its sources and principles before it becomes the basis for implementation.

- **Matches the Project Plan.** Phase 0 here delivers exactly the project plan's Phase 0 set — project structure, dependency management, configuration strategy, base README, contribution/dev docs, and lint/format/typecheck setup — without exceeding it. ✅
- **Matches the Repository Architecture.** Every created directory is architecture-defined; the just-in-time ordering (§14 of the architecture) is followed; observability stays inside `app/` and is not surfaced; data directories are deferred. ✅
- **Local-first preserved.** No hosted service, no container requirement, no cloud dependency is introduced; a clean checkout runs locally. ✅
- **Provider neutrality preserved.** No provider is named, no provider SDK is added, and no provider config or secret appears; provider material is deferred to Phase 2. ✅
- **Evaluation-first preserved.** `evals/` is deferred to Phase 4 *as the architecture intends* — preserving its first-class status by not reducing it to an empty Phase 0 folder. The principle is honored by correct timing, not by premature creation. ✅
- **No unnecessary structure.** Two directories, five files, two documents. No placeholders, no speculative folders. ✅
- **No premature implementation.** `app/` is a package root only; the checklist enforces the absence of business logic. ✅

No contradictions were found with the project plan or architecture. Terminology is consistent across all three documents.

---

## 14. Phase 0 Readiness Assessment

This plan is **ready to implement.** It is fully derived from approved sources, introduces no decisions left open, and reduces the implementation task to mechanical creation: two directories, five files, two documents, in a fixed order, each with a stated purpose and content boundary. The risks are identified with mitigations already encoded in the scope and validation checklist.

The one judgment call worth surfacing is the depth of `app/` in Phase 0 — resolved here as "package root only" to satisfy the runnable-skeleton deliverable without creating empty seam folders. That decision is recorded in §2 and §5 and is reversible.

## 15. Open Questions

1. **`app/` package depth.** This plan creates only the package root. If the local run command requires a minimal entry beyond the marker, that entry is *implementation content* (next task), not skeleton — confirm the boundary holds when the run command is defined.
2. **`configs/defaults` format and contents.** The location and role are fixed; the concrete format and which default keys exist at Phase 0 are deferred to implementation. Confirm there are real defaults to declare, or the file risks being a placeholder by another name.
3. **ADR timing.** ADRs are recommended immediately after Phase 0 but excluded from the skeleton. Confirm whether the first ADRs should land *within* Phase 0 or as the very next step (this plan assumes the latter).
4. **Development vs contribution docs.** `DEVELOPMENT.md` covers both setup and contribution conventions. If contribution norms grow, confirm whether they split into a separate document later.

## 16. Recommended Next Natural Step

Execute this plan as the **Phase 0 implementation task**: create the two directories, five files, and two documents in the order specified in §5–§6, then run the §10 validation checklist. In parallel or immediately after, capture the architecture's load-bearing decisions as the first **ADRs** in `docs/` (the architecture document's recommended next step), so the now-physical repository carries its rationale alongside its structure.
