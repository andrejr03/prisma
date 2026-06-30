# Configuration and Secrets

Configuration tells Prisma how to run without changing application code. It includes paths, chunking parameters, embedding backend names, vector index settings, and other non-secret defaults. In Phase 1, configuration should be enough to locate the sample corpus, decide how chunks are created, choose the deterministic embedding backend, and place generated index artifacts under ignored runtime state.

Committed configuration is declarative. It should describe defaults that are safe to review. A default corpus path, index path, manifest path, collection name, chunk size, overlap, and embedding dimension are all acceptable. These values shape local behavior, but they are not credentials and they do not expose private information.

Secrets are different. A secret is a credential or private value that grants access to a service or protected resource. Secrets do not belong in source code, datasets, prompts, committed configuration, documentation examples, or test fixtures. They should enter only through runtime environment variables when a later phase needs them.

Phase 1 does not need secrets. The sample corpus is committed. The embedding backend is local and deterministic. The vector index is local file-backed state. The indexing command should run without any `.env` file and without any external account. This is intentional because the first implementation phase should prove the ingestion path rather than provider authentication.

The distinction between defaults and runtime state is also important. The default configuration can say that the index path is `.local/prisma/index/qdrant` and the manifest path is `.local/prisma/index/manifest.json`. The files at those paths are generated artifacts. They should not be committed because they can be rebuilt from source data and settings.

Good configuration keeps the system reproducible. If the corpus and settings do not change, the corpus hash, chunk count, embedding model id, and indexing fingerprint should remain stable. If a setting changes, the manifest should make that change visible. This lets reviewers understand whether a new index is expected.

The rule for Phase 1 is therefore simple: add only non-secret configuration keys, keep generated artifacts under ignored paths, and avoid `.env` files entirely.
