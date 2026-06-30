# ADR-0003: Secrets via Environment

## Status

Accepted

## Date

2026-06-30

## Context

Prisma's default workflow is local-first and reproducible from a clean checkout. Committed configuration should describe non-secret defaults and shapes, while machine-specific values and credentials must remain outside version control.

Secrets in source files, configuration files, prompts, datasets, or documentation create security risk and make the repository unsafe to share.

## Decision

Secrets are never committed.

Configuration is declarative. Committed configuration may define defaults, profiles, and expected shapes, but it must not contain credentials or secret values.

Secrets enter only through runtime environment variables. No `.env` files are committed.

## Consequences

- A clean checkout contains no credentials.
- Runtime environments provide secret values without changing committed files.
- Configuration remains reviewable without exposing private data.
- Any committed secret is treated as a security defect and must be removed.
