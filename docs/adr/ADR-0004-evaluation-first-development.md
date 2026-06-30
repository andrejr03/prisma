# ADR-0004: Evaluation-First Development

## Status

Accepted

## Date

2026-06-30

## Context

Prisma treats LLM behavior as production software. Functional changes are not complete merely because they run; they must also be measurable against declared expectations.

The project plan and repository architecture make evaluation a first-class concern so quality, regressions, and tradeoffs are visible during review.

## Decision

Every significant capability introduced into Prisma must have an evaluation strategy.

Evaluation is treated as a first-class engineering concern. Evaluation assets and harnesses measure the system through its public boundary and must not become hidden business logic.

Regression is measured before functionality is considered complete.

## Consequences

- New capabilities need a clear measurement story before they are treated as complete.
- Review can ask how quality, regressions, and expected behavior are measured.
- Evaluation assets become part of the project's durable engineering record.
- Capabilities that cannot be measured are not production-ready within Prisma's standards.
