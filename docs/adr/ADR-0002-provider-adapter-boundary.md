# ADR-0002: Provider Adapter Boundary

## Status

Accepted

## Date

2026-06-30

## Context

Prisma must remain provider-neutral. Model and embedding services are implementation details that can change over time, while the rest of the application should speak in stable domain terms.

Without a strict adapter boundary, provider SDK types, assumptions, and failure modes would spread through the codebase. That would make provider changes expensive and would weaken the repository's modular boundaries.

## Decision

Provider SDKs are isolated behind adapters.

The rest of the application must remain provider-neutral. Code outside the provider-adapter boundary must not import provider SDKs, name provider-specific APIs, or assume provider-specific behavior.

Provider changes should be confined to the adapter boundary and configuration that selects the provider.

## Consequences

- Provider-specific dependencies have a single allowed integration boundary.
- Core application code remains easier to test and reason about.
- Changing a provider should not force broad changes across retrieval, workflow, API, or evaluation code.
- Reviews can reject provider leakage as an architecture violation.
