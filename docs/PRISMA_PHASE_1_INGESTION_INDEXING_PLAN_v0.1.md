# Phase 1 Ingestion & Indexing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn a small committed sample corpus into a searchable local vector index with deterministic ingestion, chunking, embeddings, identifiers, and manifest output.

**Architecture:** Phase 1 introduces the first real application seams inside `app/`: retrieval owns loading, chunking, and indexing orchestration; providers owns the embedding boundary; persistence owns vector-index writes and search. Data stays in `datasets/`, configuration stays in `configs/`, generated index artifacts stay under ignored local runtime state.

**Tech Stack:** Python 3.11, TOML configuration, pytest, ruff, mypy, deterministic local hash embeddings, and Qdrant Python client local mode for file-backed vector search.

---

> Production LLM Engineering Platform
> Planning document only. This document defines what Phase 1 should implement. It does not implement code, create Phase 1 directories, or modify application files.

**Status:** Draft v0.1
**Date:** 2026-06-30
**Document:** PRISMA_PHASE_1_INGESTION_INDEXING_PLAN_v0.1.md
**Audience:** developers, AI engineers, ML engineers, technical reviewers, and maintainers
**Companions:** [PRISMA_PROJECT_PLAN_v0.1.md](PRISMA_PROJECT_PLAN_v0.1.md), [PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md](PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md), [PRISMA_PHASE_0_REPOSITORY_SKELETON_PLAN_v0.1.md](PRISMA_PHASE_0_REPOSITORY_SKELETON_PLAN_v0.1.md), [ADR-0001](adr/ADR-0001-code-data-separation.md), [ADR-0002](adr/ADR-0002-provider-adapter-boundary.md), [ADR-0003](adr/ADR-0003-secrets-via-environment.md), [ADR-0004](adr/ADR-0004-evaluation-first-development.md)

---

## 1. Purpose

Phase 1 adds Prisma's first real application capability: ingesting a small local corpus and building a searchable vector index from it.

It is the first implementation phase because later RAG answering, citations, agent workflow, prompt regression, and evaluation all depend on a reliable retrieval substrate. Before Prisma can answer over documents, it must be able to:

- read a known corpus from a clean checkout,
- normalize document metadata,
- split documents into deterministic chunks,
- assign stable document and chunk identifiers,
- embed chunks through a provider-neutral boundary,
- write a local vector index,
- produce a manifest that explains exactly what was indexed,
- repeat the command without duplicating state.

Phase 1 should end with a local command that proves indexing works. It should not answer user questions yet.

## 2. Scope

### In Scope

- A committed, license-clear sample corpus under `datasets/sample_corpus/`.
- Document loading for committed Markdown files.
- Metadata normalization for source path, title, license, content hash, and document id.
- Deterministic chunking for plain text extracted from Markdown.
- Stable document ids and chunk ids.
- A provider-neutral embedding interface.
- A deterministic local embedding implementation that requires no API key.
- A local file-backed Qdrant index using Qdrant Python client local mode.
- An idempotent indexing pipeline.
- A module command: `python -m app.retrieval.index`.
- A generated manifest describing the index run.
- Code correctness tests for loading, chunking, ids, embeddings, indexing, manifest writing, idempotency, and retrieval smoke behavior.
- Phase 1 configuration keys in `configs/defaults.toml`.
- Minimal README and development-doc updates so the new command is discoverable.

### Explicit Non-Goals

- No answer generation.
- No chat interface.
- No agent workflow.
- No prompt management beyond confirming that Phase 1 needs no prompts.
- No `prompts/` directory.
- No evaluation harness.
- No `evals/` directory.
- No CI/CD.
- No `.github/` directory.
- No Docker.
- No `docker/` directory.
- No hosted services.
- No Supabase.
- No provider lock-in.
- No paid APIs.
- No secrets.
- No `.env` or `.env.example`.
- No provider-specific SDKs for model or embedding services.
- No ingestion of external URLs or runtime downloads.
- No generalized document parser for PDFs, HTML, DOCX, or remote stores.
- No production observability, trace persistence, cost budgets, or latency gates.

## 3. Architectural Alignment

### Project Plan

The project plan defines Phase 1 as "Ingestion and Indexing": document loader, chunking strategy, embedding step, local vector indexing, small sample corpus, and idempotent re-index command. This plan implements exactly that slice and stops before Phase 2 RAG answering.

The project plan names Qdrant as the vector-store technology. Phase 1 should use Qdrant Python client local mode with an on-disk path, not a Docker service or hosted instance. This keeps the implementation aligned with the approved stack while preserving local-first execution.

### Repository Architecture

Phase 1 follows the repository architecture's just-in-time rule:

- `datasets/` appears because ingestion now needs committed input data.
- `tests/` appears because the first application code now needs correctness tests.
- `app/retrieval/` appears because retrieval is the capability being implemented.
- `app/providers/` appears because embeddings need a provider-neutral boundary.
- `app/persistence/` appears because vector-index storage needs a persistence boundary.
- `scripts/` does not appear because `python -m app.retrieval.index` is sufficient and avoids a script that might grow business logic.
- `evals/`, `.github/`, and `docker/` remain absent because their phases have not started.

### ADR-0001: Code / Data Separation

Application logic lives under `app/`.

The sample corpus lives under `datasets/` as versioned data. It contains text and corpus metadata only. It must not import application code, define behavior, or contain executable logic.

Configuration remains declarative in `configs/defaults.toml`.

### ADR-0002: Provider Adapter Boundary

Embedding is accessed through a provider-neutral interface under `app/providers/`.

Phase 1's default embedding backend is local and deterministic. It is not an external provider and requires no secret. If future phases add external embedding services, they must sit behind the same interface without leaking provider types into retrieval, persistence, tests, or datasets.

### ADR-0003: Secrets via Environment

Phase 1 requires no secrets.

All configuration keys are non-secret paths, chunking parameters, embedding backend names, dimensions, and collection names. No `.env` or `.env.example` is introduced.

### ADR-0004: Evaluation-First Development

Phase 1 does not create the evaluation harness. That belongs to Phase 4.

Phase 1 still preserves evaluation-first development by making retrieval measurable later:

- deterministic corpus,
- deterministic chunk ids,
- deterministic local embeddings,
- reproducible index manifest,
- smoke retrieval test with a known expected source document.

The Phase 1 tests are code correctness tests. They are not evaluation scorecards and must not be treated as model-quality evaluation.

## 4. Repository Changes

Phase 1 implementation should create or modify only the paths listed here.

### Create Directories

```text
datasets/
datasets/sample_corpus/
app/retrieval/
app/providers/
app/persistence/
tests/
tests/retrieval/
tests/providers/
tests/persistence/
```

No other directories should be created in Phase 1.

### Create Dataset Files

```text
datasets/sample_corpus/manifest.toml
datasets/sample_corpus/LICENSE.txt
datasets/sample_corpus/prisma-overview.md
datasets/sample_corpus/local-first-development.md
datasets/sample_corpus/retrieval-pipeline.md
datasets/sample_corpus/provider-boundaries.md
datasets/sample_corpus/configuration-and-secrets.md
datasets/sample_corpus/evaluation-discipline.md
```

Responsibilities:

- `manifest.toml`: corpus metadata, license declaration, and ordered source file list.
- `LICENSE.txt`: license for the sample corpus text.
- `*.md`: original, license-clear sample documents used by ingestion.

### Create Application Files

```text
app/config.py
app/retrieval/__init__.py
app/retrieval/documents.py
app/retrieval/chunking.py
app/retrieval/identifiers.py
app/retrieval/pipeline.py
app/retrieval/index.py
app/providers/__init__.py
app/providers/embeddings.py
app/persistence/__init__.py
app/persistence/vector_index.py
```

Responsibilities:

- `app/config.py`: load Phase 1 settings from `configs/defaults.toml` and expose typed settings objects.
- `app/retrieval/documents.py`: read Markdown files, normalize text, and create document records.
- `app/retrieval/chunking.py`: split documents into deterministic overlapping chunks.
- `app/retrieval/identifiers.py`: compute stable corpus, document, chunk, and point identifiers.
- `app/retrieval/pipeline.py`: orchestrate load -> chunk -> embed -> index -> manifest.
- `app/retrieval/index.py`: module entry point for `python -m app.retrieval.index`; contains CLI parsing and calls `pipeline.py`.
- `app/providers/embeddings.py`: define the embedding protocol and deterministic local hash embedding backend.
- `app/persistence/vector_index.py`: own Qdrant local-mode collection creation, point upsert, search, and collection replacement.

### Create Test Files

```text
tests/conftest.py
tests/retrieval/test_documents.py
tests/retrieval/test_chunking.py
tests/retrieval/test_identifiers.py
tests/retrieval/test_pipeline.py
tests/retrieval/test_index_command.py
tests/providers/test_embeddings.py
tests/persistence/test_vector_index.py
```

Responsibilities:

- `tests/conftest.py`: shared temporary settings and sample paths for tests.
- Retrieval tests: loader, chunking, ids, pipeline idempotency, manifest output, and command behavior.
- Provider tests: deterministic embedding dimensions and repeatability.
- Persistence tests: local Qdrant write/search behavior using `tmp_path`.

### Modify Existing Files

```text
configs/defaults.toml
pyproject.toml
README.md
docs/DEVELOPMENT.md
```

Required modifications:

- `configs/defaults.toml`: add Phase 1 non-secret ingestion, chunking, embedding, index, and manifest defaults.
- `pyproject.toml`: add Qdrant client dependency and switch package discovery from `packages = ["app"]` to package discovery that includes `app.*` subpackages.
- `README.md`: update status from Phase 0 to Phase 1 and document the indexing command.
- `docs/DEVELOPMENT.md`: document setup, checks, and the Phase 1 indexing command.

### Do Not Create or Modify

```text
prompts/
evals/
scripts/
docker/
.github/
.env
.env.example
requirements.txt
```

No application files outside the listed `app/` paths should be created in Phase 1.

## 5. Dataset Strategy

The sample corpus should be:

- small,
- committed to the repository,
- license-clear,
- deterministic,
- suitable for retrieval correctness tests,
- free of personal or private information,
- independent of external downloads.

Recommended corpus shape:

- 6 Markdown documents.
- 400-800 words per document.
- Original text written for Prisma, not copied from external sources.
- One clear topic per document.
- Repeated but distinct vocabulary so retrieval smoke tests have obvious matches.
- Stable filenames in kebab case.

Recommended document topics:

1. Prisma overview.
2. Local-first development.
3. Retrieval pipeline.
4. Provider boundaries.
5. Configuration and secrets.
6. Evaluation discipline.

`datasets/sample_corpus/manifest.toml` should list the files in deterministic order:

```toml
[corpus]
id = "prisma-sample-corpus-v1"
title = "Prisma Sample Corpus"
license = "CC0-1.0"
created_for = "Phase 1 ingestion and indexing"

files = [
  "prisma-overview.md",
  "local-first-development.md",
  "retrieval-pipeline.md",
  "provider-boundaries.md",
  "configuration-and-secrets.md",
  "evaluation-discipline.md",
]
```

The sample corpus is input data, not evaluation ground truth. It belongs in `datasets/`, not `evals/`.

## 6. Ingestion Pipeline

The Phase 1 ingestion flow is:

```text
load documents
-> normalize metadata
-> split into chunks
-> assign stable ids
-> embed chunks
-> write vector index
-> write indexing manifest
```

### 1. Load Documents

Read only Markdown files listed in `datasets/sample_corpus/manifest.toml`. Do not recursively ingest arbitrary files. Fail fast if a listed file is missing.

Each loaded document should include:

- relative source path,
- title,
- raw text,
- normalized text,
- file content hash,
- corpus id,
- license.

### 2. Normalize Metadata

Metadata should be plain dictionaries or typed records with JSON-serializable values. Paths should be POSIX-style relative paths from the repository root or corpus root. Timestamps from source files should not be used in ids because they vary by machine.

### 3. Split into Chunks

Split normalized document text into overlapping chunks using the policy in Section 7. Chunking must be deterministic for identical input text and settings.

### 4. Assign Stable IDs

Compute document ids and chunk ids from normalized, deterministic inputs. Do not use random UUIDs, wall-clock time, filesystem inode values, or absolute paths.

### 5. Embed Chunks

Call the embedding boundary in `app/providers/embeddings.py`. Retrieval code must not know how embeddings are produced.

### 6. Write Vector Index

Use `app/persistence/vector_index.py` to write vectors and payloads into a local Qdrant collection stored under the configured index path.

### 7. Write Indexing Manifest

Write a JSON manifest atomically after index creation succeeds. The manifest is generated runtime state and should live under `.local/prisma/...`, not in the committed corpus.

## 7. Chunking Strategy

Use simple character-based chunking for Phase 1.

Initial policy:

- `chunk_size_chars = 900`
- `chunk_overlap_chars = 150`
- Normalize line endings to `\n`.
- Collapse runs of more than two blank lines to two blank lines.
- Strip leading and trailing whitespace.
- Prefer chunk boundaries at paragraph breaks.
- If no paragraph boundary exists within the target window, fall back to whitespace.
- If no whitespace boundary exists, split at the character limit.

Each chunk should include metadata:

- `chunk_id`
- `document_id`
- `chunk_index`
- `source_path`
- `title`
- `license`
- `start_char`
- `end_char`
- `text_hash`

Stable chunk id format:

```text
sha256("chunk:v1\n" + document_id + "\n" + chunk_index + "\n" + text_hash).hexdigest()
```

This is adequate for Phase 1 because the corpus is small, the goal is deterministic indexing, and semantic chunking would add complexity before retrieval behavior is measured. More advanced chunking can be proposed after Phase 1 has tests and a manifest baseline.

## 8. Embedding Strategy

Phase 1 should use a deterministic local hash embedding backend.

Decision:

- Define an embedding protocol in `app/providers/embeddings.py`.
- Implement `HashEmbeddingProvider` as the default backend.
- Use no external model APIs.
- Use no secrets.
- Use no provider-specific SDKs.
- Produce fixed-length dense vectors suitable for Qdrant local mode.

Recommended defaults:

- `embedding_backend = "hashing"`
- `embedding_dimensions = 384`
- `embedding_model_id = "hashing-v1-384"`

Implementation guidance:

- Tokenize normalized lowercase text with a simple alphanumeric token pattern.
- Hash each token into one of 384 vector dimensions.
- Add signed counts or normalized term frequency values.
- L2-normalize the final vector.
- Return a zero vector only for empty text; the loader should normally prevent empty chunks.

Justification:

- It is deterministic across machines.
- It requires no paid API.
- It requires no secret.
- It exercises the same retrieval -> provider -> persistence flow that a real embedding backend will use later.
- It avoids provider lock-in while giving Phase 1 a functional vector search path.

This backend is not intended to represent final semantic quality. It is an MVP indexing backend that keeps the provider boundary honest.

## 9. Vector Index Strategy

Phase 1 should use Qdrant now, but only in local Python-client mode with a file-backed path.

Decision:

- Add `qdrant-client` as a runtime dependency.
- Use `QdrantClient(path=<configured index path>)`.
- Do not run a Qdrant server.
- Do not use Docker.
- Do not use Qdrant Cloud or any hosted service.
- Store generated index files under `.local/prisma/index/qdrant/`.

Justification:

- The project plan names Qdrant as the vector store.
- Qdrant documents Python client local mode as a way to run without a Qdrant server for testing, debugging, and small vector sets: [Qdrant local mode](https://qdrant.tech/documentation/frameworks/langchain/#local-mode).
- Qdrant Python client local mode supports development and testing without a running server.
- A file-backed local index proves persistence and re-run behavior better than an in-memory index.
- The persistence wrapper keeps Qdrant-specific calls out of retrieval code.
- Later phases can switch the wrapper to server mode without changing the retrieval pipeline contract.

In-memory indexes are too weak for Phase 1 because they do not prove generated local state or manifest consistency. A handwritten JSON vector store is simpler, but it would defer the approved vector-store dependency and create a temporary persistence implementation to delete later.

## 10. Idempotency and Manifests

Repeated indexing runs must not duplicate chunks or append stale points.

Idempotency policy:

1. Load corpus manifest and source files.
2. Compute a corpus hash from sorted source file paths and content hashes.
3. Compute an indexing fingerprint from corpus hash, chunk settings, embedding model id, and collection name.
4. If an existing manifest has the same fingerprint and the Qdrant collection exists, report "index up to date" and exit successfully.
5. If the fingerprint differs, recreate the Qdrant collection and upsert all current chunks.
6. Write the manifest atomically after a successful index write.

Required generated manifest fields:

```json
{
  "schema_version": 1,
  "corpus_id": "prisma-sample-corpus-v1",
  "corpus_hash": "<sha256>",
  "document_count": 6,
  "chunk_count": 0,
  "chunk_size_chars": 900,
  "chunk_overlap_chars": 150,
  "embedding_backend": "hashing",
  "embedding_model_id": "hashing-v1-384",
  "embedding_dimensions": 384,
  "vector_store": "qdrant-local",
  "collection_name": "prisma_sample_corpus",
  "index_location": ".local/prisma/index/qdrant",
  "manifest_path": ".local/prisma/index/manifest.json",
  "created_timestamp": "2026-06-30T00:00:00Z",
  "source_files": [
    {
      "path": "datasets/sample_corpus/prisma-overview.md",
      "sha256": "<sha256>",
      "document_id": "<stable id>"
    }
  ]
}
```

`chunk_count` must be the actual count generated by implementation, not a hardcoded value.

Generated index and manifest files are runtime artifacts and must not be committed. Existing `.gitignore` already ignores `.local/`; Phase 1 should keep artifacts under that ignored root.

## 11. CLI / Script Entry Point

Phase 1 should expose this command:

```sh
python -m app.retrieval.index
```

The module should:

- load settings from `configs/defaults.toml`,
- allow optional non-secret path overrides through CLI flags if useful,
- run the indexing pipeline,
- print a concise summary: documents, chunks, collection, manifest path, and idempotency result,
- exit non-zero on missing files, invalid settings, or index write failure.

Recommended optional flags:

```text
--config configs/defaults.toml
--corpus-path datasets/sample_corpus
--index-path .local/prisma/index/qdrant
--manifest-path .local/prisma/index/manifest.json
--force
```

Do not create `scripts/` in Phase 1. The architecture says scripts are thin orchestration only and should appear when a repeated operation deserves a separate entry point. A module command is enough for the first indexing capability and keeps orchestration close to the retrieval package without putting business logic in a script.

## 12. Testing Strategy

Phase 1 must add code correctness tests under `tests/`. These tests verify deterministic behavior and local indexing mechanics. They are not an evaluation harness and must not create `evals/`.

Required tests:

- Document loader reads the committed sample manifest and Markdown files.
- Loader rejects missing files listed in the corpus manifest.
- Metadata normalization produces relative paths and stable content hashes.
- Chunking is deterministic for the same document and settings.
- Chunking respects size and overlap bounds.
- Document ids are stable across repeated runs.
- Chunk ids are stable across repeated runs.
- Hash embeddings are deterministic and have the configured dimension.
- Empty text embedding behavior is explicit and tested.
- Local Qdrant persistence can recreate a collection, upsert chunks, and return nearest chunks.
- Index command writes a manifest.
- Running the index command twice with unchanged inputs is idempotent.
- Changing a source document or chunk setting changes the indexing fingerprint.
- Retrieval smoke test returns the expected document or chunk for a query with distinctive corpus terms.

Recommended smoke query:

```text
provider boundaries embedding adapters
```

Expected top source:

```text
datasets/sample_corpus/provider-boundaries.md
```

The smoke test checks wiring and determinism, not answer quality.

## 13. Configuration Strategy

Phase 1 should extend `configs/defaults.toml` with non-secret defaults.

Recommended keys:

```toml
[paths]
runtime_state = ".local/prisma"
corpus_path = "datasets/sample_corpus"
index_path = ".local/prisma/index/qdrant"
manifest_path = ".local/prisma/index/manifest.json"

[retrieval]
chunk_size_chars = 900
chunk_overlap_chars = 150

[embeddings]
backend = "hashing"
dimensions = 384
model_id = "hashing-v1-384"

[vector_index]
backend = "qdrant-local"
collection_name = "prisma_sample_corpus"
distance = "cosine"
```

Configuration rules:

- Defaults are committed and non-secret.
- Runtime artifacts use paths under `.local/prisma`.
- No secret keys are introduced.
- No provider API keys are introduced.
- Environment variable overrides may be added only for non-secret path and runtime configuration if implementation needs them. They are not required for Phase 1.

## 14. Validation Commands

After Phase 1 implementation, these commands must pass from a clean checkout after installing dependencies:

```sh
python -m ruff check .
python -m ruff format --check .
python -m mypy app
python -m pytest
python -m app.retrieval.index
python -m app.retrieval.index
```

The second indexing command verifies idempotency and should exit successfully without duplicating index state.

Useful manual inspection commands:

```sh
find datasets -maxdepth 3 -type f | sort
find app -maxdepth 3 -type f | sort
find tests -maxdepth 3 -type f | sort
find .local/prisma -maxdepth 4 -type f | sort
```

Forbidden path checks:

```sh
test ! -d prompts
test ! -d evals
test ! -d docker
test ! -d .github
test ! -f .env
test ! -f .env.example
test ! -f requirements.txt
```

## 15. Deliverables

Phase 1 implementation delivers:

- A committed sample corpus under `datasets/sample_corpus/`.
- Markdown document loading from a declared corpus manifest.
- Deterministic metadata normalization.
- Deterministic chunking.
- Stable document and chunk identifiers.
- A provider-neutral embedding protocol.
- A deterministic local hash embedding backend.
- A local file-backed Qdrant index.
- An idempotent indexing pipeline.
- A generated indexing manifest under `.local/prisma`.
- The command `python -m app.retrieval.index`.
- Code correctness tests under `tests/`.
- Updated configuration defaults.
- Updated README and development docs.

### Implementation Task Order

1. Add sample corpus data and corpus manifest.
2. Add Phase 1 configuration keys and package-discovery/dependency updates.
3. Implement document loading and metadata normalization with tests.
4. Implement stable identifiers with tests.
5. Implement chunking with tests.
6. Implement deterministic local embeddings with tests.
7. Implement Qdrant local vector-index persistence with tests.
8. Implement the indexing pipeline and manifest writer with tests.
9. Implement `python -m app.retrieval.index` and command tests.
10. Update README and development docs.
11. Run all validation commands.

Each task should be small enough to review independently and should avoid adding capabilities from later phases.

## 16. Risks and Mitigations

### Over-Engineering Retrieval Too Early

Risk: Phase 1 grows into ranking, hybrid search, semantic chunking, query rewriting, or RAG answering.

Mitigation: Keep Phase 1 to load, chunk, embed, index, manifest, and smoke search. Anything that synthesizes answers belongs to Phase 2 or later.

### Confusing Tests with Evals

Risk: Retrieval smoke tests become an informal evaluation harness.

Mitigation: Keep tests deterministic and correctness-focused. Do not create golden answer datasets, scorecards, baselines, or `evals/`.

### External Dependency Fragility

Risk: Qdrant dependency or local-mode behavior creates setup friction.

Mitigation: Use only Qdrant client local mode, pin a compatible major version, cover it with tests using `tmp_path`, and keep Qdrant-specific code inside `app/persistence/vector_index.py`.

### Unstable Chunk IDs

Risk: Chunk ids change across machines or repeated runs.

Mitigation: Base ids only on normalized content, relative paths, deterministic settings, and explicit version prefixes. Never use timestamps, absolute paths, random UUIDs, or filesystem metadata.

### Sample Corpus Too Artificial

Risk: The corpus is so small or repetitive that retrieval smoke tests prove little.

Mitigation: Use six focused documents with overlapping but distinctive terms. Keep the smoke test narrow and treat richer retrieval measurement as Phase 4 evaluation work.

### Provider Leakage

Risk: Future embedding choices leak into retrieval or persistence code.

Mitigation: Retrieval calls only the embedding protocol. Provider-specific dependencies, if introduced later, must stay behind `app/providers/`.

### Generated Artifacts Accidentally Committed

Risk: Qdrant index files or manifests get committed.

Mitigation: Write generated artifacts under `.local/prisma`, which is ignored. Validate with `git status --short` after running the index command.

## 17. Success Criteria

Phase 1 is complete when:

- `python -m app.retrieval.index` works from a clean checkout after documented setup.
- Running `python -m app.retrieval.index` twice is idempotent.
- The sample corpus is committed under `datasets/sample_corpus/`.
- The index artifact is generated locally under `.local/prisma` and is not committed.
- The manifest is generated locally under `.local/prisma` and is not committed unless a later approved plan explicitly changes that policy.
- The manifest records corpus hash, document count, chunk count, embedding model/id, index location, created timestamp, and source file list.
- Tests pass with `python -m pytest`.
- Linting, formatting, and type checking pass.
- Retrieval smoke test returns the expected source document or chunk.
- No Phase 2+ capabilities are introduced.
- No `prompts/`, `evals/`, `docker/`, or `.github/` directories are created.
- No hosted services, secrets, Supabase, answer generation, chat UI, agent workflow, or evaluation harness are introduced.

## 18. Recommended Next Natural Step

Review this Phase 1 plan against the approved project plan, repository architecture, and ADRs.

After review, implement Phase 1 ingestion and indexing as one focused slice, using this document as the implementation contract.
