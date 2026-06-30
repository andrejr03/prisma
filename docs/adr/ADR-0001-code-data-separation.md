# ADR-0001: Code / Data Separation

## Status

Accepted

## Date

2026-06-30

## Context

Prisma is intended to remain reproducible, reviewable, and locally runnable. The repository architecture separates executable application behavior from assets that shape or measure that behavior.

Prompts, datasets, configuration, and evaluation assets change for different reasons than application code. If these assets become executable logic, the system becomes harder to review, reproduce, and test.

## Decision

Business logic lives only inside `app/`.

Prompts, datasets, configs, and evaluation assets are versioned data assets. They may be loaded, reviewed, diffed, and measured, but they must not become executable logic.

Data assets must not import application code, define runtime behavior, or become a second implementation surface.

## Consequences

- Application behavior has a single implementation home: `app/`.
- Data asset changes stay visible as data changes and can be reviewed independently.
- Prompt, config, dataset, and evaluation updates remain reproducible from declared files.
- Any logic discovered in data assets must move into the appropriate application boundary.
