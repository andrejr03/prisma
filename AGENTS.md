# AGENTS.md

## 1. Purpose

This file defines mandatory operational rules for every coding agent working on Prisma.

Treat these rules as repository policy. Follow them before any tool default, personal preference, or inferred workflow.

## 2. Git Workflow

- MUST work on the current branch unless explicitly instructed otherwise.
- MUST NOT create branches unless explicitly instructed.
- MUST NOT rename branches.
- MUST NOT delete branches unless explicitly instructed.
- MUST NOT create tags.
- MUST NOT rewrite Git history.
- MUST NOT force push.
- MUST NOT add Git remotes.
- MUST NOT push unless explicitly instructed.
- MUST treat all commits as local by default.
- MUST NOT revert or discard user work unless explicitly instructed.

## 3. Planning Rules

- MUST have an approved plan before every implementation.
- MUST NOT implement directly from discussion, brainstorming, or unresolved design notes.
- If no approved plan exists, stop and report that implementation is blocked.
- MUST follow the approved plan exactly once implementation begins.

## 4. Architecture Authority

Implementation MUST follow, in order:

1. The Project Plan.
2. The Repository Architecture.
3. Accepted ADRs.
4. The current approved Phase Plan.

If these documents contradict each other, stop. Report the contradiction. Do not improvise.

## 5. Scope Control

- MUST implement only the approved phase.
- MUST NOT anticipate future phases.
- MUST NOT introduce future-phase capabilities.
- MUST NOT create unapproved directories, services, workflows, dashboards, registries, CI, Docker, hosted integrations, or provider comparisons.
- If a correct implementation appears to require future work, report that requirement instead of implementing it.

## 6. Simplicity Rule

- When multiple solutions satisfy the approved plan, choose the simplest.
- MUST avoid speculative abstractions.
- MUST avoid premature optimization.
- MUST prefer existing repository patterns over new machinery.

## 7. Documentation Rules

- If public behavior changes, update `README.md` and `docs/DEVELOPMENT.md` in the same task.
- Update architecture documents only when architecture changes.
- MUST NOT edit plans or ADRs to justify an implementation after the fact.
- Keep documentation concise and operational.

## 8. Validation Rules

- MUST run every validation command required by the current phase.
- MUST NOT report success unless every mandatory validation passes.
- MUST report validation failures explicitly, including the command and failure summary.
- MUST run `git diff --check` before final reporting.
- MUST run `git status --short` before final reporting.

## 9. Provider Neutrality

- MUST NOT introduce provider-specific logic outside provider adapters.
- MUST NOT leak provider SDKs, provider response types, provider retry behavior, or provider credentials into application logic.
- MUST keep retrieval, workflow, evaluation, and API code provider-neutral.

## 10. Secrets

MUST NOT commit:

- secrets
- API keys
- tokens
- `.env`
- private credentials

MUST NOT introduce secrets unless the approved phase explicitly requires them.

## 11. Repository Philosophy

Prisma prioritizes:

- deterministic behavior
- local-first execution
- reproducibility
- provider neutrality
- explicit architecture
- evaluation-first engineering
- maintainability
- simplicity over cleverness

Use these priorities to resolve low-level choices that the approved plan leaves open.

## 12. Decision Rule

If an implementation detail is not explicitly defined by the approved plan:

1. Choose the simplest solution fully consistent with the Repository Architecture and ADRs.
2. Do not invent new architecture.
3. Document the decision in the final implementation report.

## 13. Reporting

Every implementation report MUST include:

- files created
- files modified
- validation results
- git status summary
- confirmation that no forbidden scope was introduced
- recommended next natural step

If work was blocked, report the blocker instead of presenting the task as complete.
