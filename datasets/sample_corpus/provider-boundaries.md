# Provider Boundaries

Provider boundaries keep Prisma from hardcoding one model or embedding service into the rest of the application. A provider may be useful, but it should not become part of every module's vocabulary. Retrieval, persistence, configuration, and tests should speak in neutral terms such as embedding vector, model id, dimension, and document chunk.

The boundary matters most when embeddings are introduced. Embeddings are required for vector search, but the retrieval pipeline should not import a provider SDK directly. Instead, retrieval calls an embedding interface. That interface accepts text and returns vectors with a declared model id and dimension. The implementation behind the interface can change without forcing retrieval code to change.

Phase 1 uses a deterministic local hash embedding backend. This backend is not a hosted provider and it does not require secrets. It exists to exercise the provider boundary and make indexing work from a clean checkout. The vectors are stable across repeated runs, so tests can verify idempotency and search wiring without depending on a remote model.

A later implementation may add an external embedding adapter. If that happens, provider-specific dependencies, request formats, retry behavior, and authentication details should stay inside the provider adapter. They should not leak into chunking, indexing, command parsing, or dataset files. The rest of the system should continue to ask for embeddings through the neutral interface.

Provider boundaries also protect tests. A correctness test for chunking should not care which embedding service exists. A persistence test should be able to use deterministic vectors. A pipeline test should verify that chunks are passed to the embedding boundary and then written to the vector index. None of those tests should require a secret key or a network connection.

Configuration belongs outside provider code, but it remains declarative. Phase 1 can name the embedding backend as `hashing`, set a dimension, and record a model id. That is not provider lock-in. It is a local default. Provider lock-in would appear if provider-specific classes, response objects, environment variable names, or SDK assumptions spread through application code.

The practical review rule is straightforward: if a provider detail appears outside the adapter boundary, the change should be rejected or redesigned. Keeping provider boundaries tight lets Prisma evolve without broad rewrites when embedding choices change.
