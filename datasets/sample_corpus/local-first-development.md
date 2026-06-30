# Local-First Development

Local-first development means Prisma should be useful from a clean checkout on a developer laptop. The default path does not require hosted services, remote databases, cloud credentials, or paid APIs. A contributor should be able to install dependencies, run checks, build the local index, and inspect generated artifacts without leaving the repository.

This choice is about engineering control. When the default system runs locally, failures are easier to reproduce. A missing file, a changed chunk id, or a broken manifest can be inspected directly. The developer does not need to ask whether a hosted service changed underneath the test. The repository carries the source data, configuration shape, and commands needed to rebuild the local state.

Local-first does not mean production concerns are ignored. Prisma still cares about traceability, stable identifiers, dependency boundaries, and repeatable outputs. It simply introduces those concerns in the smallest environment that can exercise them. The same discipline that makes a local run understandable later helps hosted or distributed deployments remain understandable.

Runtime artifacts are not source. A vector index, an indexing manifest, a run record, or a trace file may be important for debugging, but those files are generated state. They should be written under an ignored local runtime directory and rebuilt from committed inputs. Keeping artifacts out of version control prevents stale state from becoming confused with source data.

Configuration follows the same pattern. Committed defaults describe non-secret behavior such as corpus paths, chunk sizes, embedding backend names, index locations, and collection names. Machine-specific values can be supplied at runtime when needed. Secret values do not belong in committed files. The local default should not need any secret at all during Phase 1.

The local-first rule also constrains dependencies. Phase 1 uses a local deterministic embedding backend and a file-backed local vector index. That combination proves the ingestion, embedding, persistence, and search boundaries without requiring external accounts. Later provider integrations can be added behind adapters, but the first implementation should not depend on them.

For contributors, the outcome is simple: the documented indexing command should work repeatedly. Running it twice should not create duplicate state. If nothing changed in the corpus or indexing settings, Prisma should report that the index is already current.
