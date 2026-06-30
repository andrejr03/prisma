# Evaluation Discipline

Evaluation discipline is one of Prisma's core principles, but Phase 1 does not implement the evaluation harness. That separation is deliberate. Phase 1 builds the retrieval substrate that future evaluation will measure. It should not create golden answer datasets, scorecards, baselines, or evaluation runners before the system has an answering surface.

Even without the evaluation harness, Phase 1 can prepare for measurement. The sample corpus should be deterministic. Documents should have stable identifiers. Chunks should have stable identifiers. The embedding backend should produce repeatable vectors. The index manifest should record the corpus hash, chunk settings, embedding model id, collection name, source files, document count, and chunk count.

These details matter because evaluation depends on reproducibility. If the same source files produce different chunk ids on different machines, later scorecards will be hard to trust. If an index can contain duplicate stale chunks after repeated runs, a retrieval result may reflect old state instead of the current corpus. If the manifest does not describe the index, reviewers cannot tell what was measured.

Phase 1 tests are correctness tests. They should verify that the loader reads files, chunking is deterministic, ids are stable, the embedding backend is repeatable, the vector index can store and return chunks, and the indexing command is idempotent. These tests make sure the machinery works. They do not judge answer quality or retrieval quality across a benchmark.

Later phases can add evaluation assets in the dedicated evaluation area. Those assets will define expected behavior, metrics, baselines, and scorecards. They will measure the system through its public boundary. They should not replace unit tests, and unit tests should not pretend to be scorecards.

The retrieval smoke test in Phase 1 has a narrow purpose. A query such as "provider boundaries embedding adapters" should return the provider-boundaries document near the top because the words are distinctive in the corpus. That confirms wiring across embedding and persistence. It is not a claim that the retrieval system is production quality.

Evaluation-first development means every significant capability needs a measurement story. For Phase 1, the story is groundwork: deterministic indexing today, evaluation harness later.
