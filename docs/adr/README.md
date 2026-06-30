# Architecture Decision Records

Architecture Decision Records (ADRs) capture stable decisions that shape Prisma's repository and implementation boundaries. They explain why a decision exists so future reviews can cite the decision directly instead of re-arguing settled architecture.

ADRs are documentation only. They do not implement behavior.

## Numbering Policy

ADRs are numbered sequentially with a four-digit identifier:

```text
ADR-0001-short-title.md
ADR-0002-short-title.md
```

Numbers are never reused. If an ADR is proposed but not accepted, its number is still reserved once the file is committed.

## Superseding Policy

Accepted ADRs are superseded by creating a new ADR with a new number. The new ADR should name the ADR it supersedes and explain the changed decision.

Do not rewrite history by replacing an old decision in place.

## Immutability Policy

After an ADR is accepted, keep it stable. Corrections for typos, broken links, or formatting are allowed, but the decision and rationale should not be materially changed.

Material changes require a new ADR.

## Creating Future ADRs

1. Choose the next sequential ADR number.
2. Use the lightweight structure: Status, Date, Context, Decision, Consequences.
3. Keep the ADR focused on one decision.
4. Tie the decision back to the project plan, repository architecture, or an approved design document.
5. Keep the decision implementation-independent unless the approved architecture explicitly requires an implementation choice.
6. Mark the ADR as Proposed while under review and Accepted once approved.
