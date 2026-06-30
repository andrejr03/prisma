# Retrieval Pipeline

The retrieval pipeline is the first application capability in Prisma. It turns source documents into searchable chunks. The pipeline is deliberately small in Phase 1, but it establishes the contracts that later answering and evaluation depend on.

The first step is document loading. Prisma reads a declared corpus manifest and then loads only the files listed there. It does not crawl arbitrary directories and it does not download remote documents. This makes the input set stable. Each document receives normalized metadata such as source path, title, license, content hash, corpus id, and document id.

The second step is text normalization. Documents may have different line endings or extra blank lines depending on editing tools. Normalization gives the chunker a stable input. The goal is not to understand every document format. Phase 1 handles committed Markdown files because they are readable, reviewable, and enough to prove indexing.

The third step is chunking. Long documents are split into overlapping text windows. Each chunk records its source document, chunk index, character offsets, text hash, title, license, and stable chunk id. The chunk id must not depend on timestamps, absolute paths, or random values. A repeated run over the same inputs and settings should produce the same chunks.

The fourth step is embedding. Retrieval code calls a provider-neutral embedding boundary and receives numeric vectors. In Phase 1 the default backend is deterministic and local. It uses hashing rather than an external embedding service. The important point is the boundary: retrieval should not know or care whether the vector came from a local implementation or a later provider adapter.

The fifth step is indexing. The persistence layer writes vectors and payload metadata into a local vector index. Phase 1 uses Qdrant local mode with files stored under ignored runtime state. Retrieval orchestration should not scatter Qdrant calls across the application. A persistence wrapper owns collection creation, replacement, upsert, and search.

The final step is manifest writing. The manifest records the corpus hash, document count, chunk count, embedding model id, index path, collection name, creation timestamp, and source file list. It is generated runtime state, not committed source. It tells a developer what the local index contains and whether it matches the current corpus and settings.

A good Phase 1 pipeline is boring and repeatable. It does not answer questions. It does not invoke an agent. It makes later retrieval behavior possible by ensuring that the index can be rebuilt and inspected.
