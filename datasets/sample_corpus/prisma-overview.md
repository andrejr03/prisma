# Prisma Overview

Prisma is a local-first engineering platform for production LLM systems. Its first goal is not to be a polished assistant or a broad demo. Its goal is to show how a careful team can build an LLM feature with the same discipline expected from production software. The system should be readable, reproducible, measurable, and small enough that every boundary can be reviewed.

The product shape is intentionally narrow. Prisma works over a document corpus, builds a retrieval index, and later uses that retrieval layer to support cited answers. The repository treats the retrieval path as an engineering surface rather than a hidden convenience. Documents are loaded from declared locations, chunks receive stable identifiers, generated state is written locally, and every later capability must be traceable back to a known input.

The project is built in phases. Phase 0 creates the repository skeleton, configuration defaults, documentation, and tooling. Phase 1 turns the first sample corpus into a searchable local vector index. Later phases add answering, bounded agent workflow, evaluation harnesses, prompt regression, observability, and automated quality gates. Each phase should leave the repository in a useful state without pretending that future work already exists.

Prisma is local-first because a clean checkout should work on a developer laptop without hosted infrastructure. Local execution keeps review and debugging direct. It also makes quality controls easier to reproduce. Generated indexes, manifests, run records, and traces belong in ignored runtime state, not in committed source. The committed repository should contain the inputs and the code needed to rebuild those artifacts.

The repository is also boundary-first. Application logic belongs in the application package. Data assets such as prompts, datasets, configuration, and evaluation files are versioned and reviewed, but they are not executable logic. Providers are reached through adapters. Secrets enter only through runtime environment variables. Evaluation is treated as an engineering concern, not as decoration after implementation.

The sample corpus exists so Phase 1 can prove the ingestion and indexing path. The text is small, original, and license-clear. It contains repeated terms such as retrieval, index, configuration, provider boundary, manifest, and evaluation so correctness tests can search for distinctive topics without requiring answer generation.
