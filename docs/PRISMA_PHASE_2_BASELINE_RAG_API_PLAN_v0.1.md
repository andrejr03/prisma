# Phase 2 Baseline RAG API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first user-facing Prisma capability: a minimal REST API that retrieves indexed corpus chunks, assembles grounded context, generates a deterministic cited answer, and returns a structured response.

**Architecture:** Phase 2 adds a thin API layer above Phase 1 retrieval and a provider-neutral generation boundary. Retrieval remains responsible for vector search, generation remains grounded in supplied context, prompts are data assets, and no agent workflow is introduced.

**Tech Stack:** Python 3.11, FastAPI, Pydantic, pytest, ruff, mypy, Qdrant local mode, deterministic local embeddings, and a deterministic local grounded generation backend.

---

> Production LLM Engineering Platform
> Planning document only. This document defines what Phase 2 should implement. It does not implement code, create directories, or modify application files.

**Status:** Draft v0.1
**Date:** 2026-06-30
**Document:** PRISMA_PHASE_2_BASELINE_RAG_API_PLAN_v0.1.md
**Audience:** developers, AI engineers, ML engineers, technical reviewers, and maintainers
**Companions:** [PRISMA_PROJECT_PLAN_v0.1.md](PRISMA_PROJECT_PLAN_v0.1.md), [PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md](PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md), [PRISMA_PHASE_0_REPOSITORY_SKELETON_PLAN_v0.1.md](PRISMA_PHASE_0_REPOSITORY_SKELETON_PLAN_v0.1.md), [PRISMA_PHASE_1_INGESTION_INDEXING_PLAN_v0.1.md](PRISMA_PHASE_1_INGESTION_INDEXING_PLAN_v0.1.md), [ADR-0001](adr/ADR-0001-code-data-separation.md), [ADR-0002](adr/ADR-0002-provider-adapter-boundary.md), [ADR-0003](adr/ADR-0003-secrets-via-environment.md), [ADR-0004](adr/ADR-0004-evaluation-first-development.md)

---

## 1. Purpose

Phase 2 exists to turn the indexed corpus from Phase 1 into the first user-facing Prisma capability: a baseline Retrieval-Augmented Generation API.

Phase 1 proved that Prisma can:

- load a committed sample corpus,
- split documents into deterministic chunks,
- embed chunks through a provider-neutral boundary,
- write a local Qdrant index,
- search indexed chunks,
- generate an indexing manifest.

Phase 2 builds directly on that substrate. It accepts a question, retrieves relevant chunks from the existing local index, assembles those chunks into bounded context, sends the question and context through a provider-neutral generation boundary, and returns a structured answer with citations.

The point of this phase is not agentic reasoning. It is the smallest production-oriented RAG surface that proves Prisma can answer from its indexed corpus while preserving validation, explicit contracts, local-first execution, and citation discipline.

## 2. Scope

### In Scope

- Similarity retrieval over the Phase 1 Qdrant local index.
- Top-k retrieval with configurable defaults and request-level bounds.
- Context assembly from retrieved chunks.
- Provider-neutral generation boundary.
- Deterministic local grounded generation backend.
- Minimal prompt asset required to instruct grounded answering.
- FastAPI application and one baseline query endpoint.
- Pydantic request, response, citation, and error schemas.
- Request validation.
- Structured responses.
- Citations tied to retrieved chunks.
- Basic error handling for invalid input, missing index, no retrieved context, unsupported backends, and unexpected failures.
- Correctness tests for retrieval, context assembly, generation boundary, citations, API behavior, errors, and deterministic behavior.
- README and development-doc updates for the API smoke path.
- Non-secret configuration defaults.

### Explicit Non-Goals

- No agent workflow.
- No LangGraph.
- No planning/reasoning graph.
- No autonomous tool use.
- No prompt versioning.
- No prompt registry.
- No prompt management system.
- No evaluation harness.
- No `evals/` directory.
- No reranking.
- No hybrid search.
- No streaming responses.
- No authentication.
- No authorization.
- No Docker.
- No CI.
- No `.github/` workflows.
- No hosted services.
- No UI.
- No chat session memory.
- No conversation history.
- No production observability, trace persistence, cost budgets, or latency gates.
- No provider-specific model APIs.
- No secrets.
- No `.env` or `.env.example`.

## 3. Architectural Alignment

### Project Plan

The project plan defines Phase 2 as "Baseline RAG API": a typed query endpoint that retrieves and answers with citations, request/response schemas, retrieval-to-prompt-to-generation flow, and basic error handling.

This plan implements that slice only. It does not add the Phase 3 agent workflow, Phase 4 evaluation harness, Phase 5 prompt regression, Phase 6 observability budgets, Phase 7 CI, or Phase 8 Docker/reproducibility polish.

### Repository Architecture

Phase 2 follows the repository architecture's boundaries:

- `app/api/` appears because the first HTTP API surface now has real work.
- `app/models/` appears because request/response/error contracts now need typed shared schemas.
- `app/generation/` appears because answer generation and context assembly are now first-class application behavior.
- `prompts/` appears because the first prompt text is now loaded by the system as a data asset.
- `tests/api/` and `tests/generation/` appear because new application behavior needs correctness tests.
- `evals/`, `.github/`, `docker/`, and `scripts/` remain absent because their responsibilities are not active in Phase 2.

Control flow remains simple:

```text
API -> retrieval search -> context assembly -> generation boundary -> structured response
```

No agent layer is inserted.

### ADR-0001: Code / Data Separation

RAG business logic lives inside `app/`.

The minimal prompt is a versioned data asset under `prompts/`; it is loaded by application code but does not contain executable logic. The sample corpus remains data under `datasets/`. Configuration remains declarative under `configs/`.

### ADR-0002: Provider Adapter Boundary

Generation is accessed through a provider-neutral interface. The default Phase 2 backend is local and deterministic so the API works from a clean checkout without secrets or hosted services.

No provider-specific SDK, response object, model name, environment variable, or API detail may leak into API, retrieval, context assembly, tests, prompts, or datasets.

### ADR-0003: Secrets via Environment

Phase 2 requires no secrets.

All new configuration keys are non-secret: retrieval top-k defaults, context size limits, prompt path, generation backend name, and local generator model id. No `.env` or `.env.example` is introduced.

### ADR-0004: Evaluation-First Development

Phase 2 does not create the evaluation harness. That remains Phase 4.

Phase 2 supports future evaluation by returning deterministic structured responses, explicit citations, and stable source metadata. Tests verify correctness of contracts and grounding behavior; they do not score answer quality.

## 4. Repository Changes

Phase 2 implementation should create or modify only the paths listed here.

### Create Directories

```text
app/api/
app/generation/
app/models/
prompts/
tests/api/
tests/generation/
```

Do not create `evals/`, `docker/`, `.github/`, `scripts/`, or UI directories.

### Create Application Files

```text
app/api/__init__.py
app/api/main.py
app/api/errors.py
app/api/routes.py
app/generation/__init__.py
app/generation/context.py
app/generation/service.py
app/models/__init__.py
app/models/rag.py
app/providers/generation.py
app/retrieval/search.py
```

Responsibilities:

- `app/api/main.py`: FastAPI app construction and exception-handler registration.
- `app/api/routes.py`: `POST /query` endpoint only.
- `app/api/errors.py`: application error types and JSON error response mapping.
- `app/models/rag.py`: Pydantic models for requests, responses, citations, retrieved context, and errors.
- `app/generation/context.py`: deterministic context assembly and truncation.
- `app/generation/service.py`: orchestration for retrieve -> assemble -> generate -> cite.
- `app/providers/generation.py`: provider-neutral generation protocol and local deterministic grounded backend.
- `app/retrieval/search.py`: query-facing retrieval wrapper over Phase 1 `search_index`.

### Create Prompt File

```text
prompts/baseline_rag.txt
```

This is the only prompt asset for Phase 2. It contains concise grounded-answering instructions. It is not a registry, versioning system, prompt management layer, or prompt regression setup.

### Create Test Files

```text
tests/api/test_query_endpoint.py
tests/api/test_error_responses.py
tests/generation/test_context.py
tests/generation/test_generation_provider.py
tests/generation/test_rag_service.py
tests/retrieval/test_search.py
```

Responsibilities:

- API tests verify request validation, response schema, error schema, and citation fields.
- Generation tests verify deterministic local generation and no unsupported citation ids.
- Context tests verify ordering, separators, max-size truncation, and metadata preservation.
- Retrieval tests verify top-k behavior and returned payload metadata.
- Service tests verify end-to-end RAG orchestration without starting a server.

### Modify Existing Files

```text
app/config.py
configs/defaults.toml
pyproject.toml
README.md
docs/DEVELOPMENT.md
```

Required modifications:

- `app/config.py`: add typed Phase 2 API, retrieval-query, context, prompt, and generation settings.
- `configs/defaults.toml`: add non-secret Phase 2 defaults.
- `pyproject.toml`: add FastAPI dependency and any local API-test dependency not already provided.
- `README.md`: document the Phase 2 API smoke path.
- `docs/DEVELOPMENT.md`: document API validation commands and local run instructions.

### Do Not Create or Modify

```text
evals/
docker/
.github/
scripts/
.env
.env.example
requirements.txt
```

No Phase 3+ application files should be introduced.

## 5. Retrieval Strategy

Phase 2 uses the Phase 1 vector index and embedding backend.

Retrieval flow:

1. Validate the question and `top_k`.
2. Embed the question through the existing provider-neutral embedding boundary.
3. Query Qdrant local mode through `app/persistence/vector_index.py`.
4. Return top-k chunks sorted by vector score.
5. Preserve payload metadata from indexed chunks.

Default retrieval settings:

```toml
[rag]
default_top_k = 4
max_top_k = 8
min_score = 0.0
```

Returned metadata per chunk:

- `chunk_id`
- `document_id`
- `chunk_index`
- `source_path`
- `title`
- `license`
- `score`
- `text`

Determinism rules:

- Use the existing deterministic embedding backend by default.
- Preserve Qdrant score ordering.
- Break equal-score ties by `source_path`, then `chunk_index`, then `chunk_id`.
- Do not rerank.
- Do not use hybrid search.
- Do not query external services.

If the local index is missing, the API returns a structured `503 Service Unavailable` error with code `index_not_ready` and a message telling the caller to run `python -m app.retrieval.index`.

## 6. Context Assembly

Context assembly converts retrieved chunks into a bounded string for generation while preserving citation metadata.

Ordering:

1. Sort by retrieval rank.
2. Preserve rank numbers starting at 1.
3. Do not reorder by source document.
4. Do not deduplicate in Phase 2 unless the same `chunk_id` appears twice.

Separators:

```text
[1] title="Provider Boundaries" source_path="datasets/sample_corpus/provider-boundaries.md" chunk_id="<chunk id>"
<chunk text>

---

[2] title="..." source_path="..." chunk_id="..."
<chunk text>
```

Maximum context size:

```toml
[rag]
max_context_chars = 4000
max_answer_sentences = 3
```

Truncation strategy:

- Include chunks in retrieval order until adding the next chunk would exceed `max_context_chars`.
- Never split a chunk in Phase 2.
- If the first chunk alone exceeds `max_context_chars`, truncate that chunk text at the nearest whitespace before the limit and mark `truncated = true` on that context item.
- Preserve metadata even when text is truncated.

Metadata preservation:

- The assembled context returns both the context string and a structured list of context items.
- Each context item retains `citation_id`, `chunk_id`, `source_path`, `source_document`, `chunk_index`, `score`, `text`, and `truncated`.
- The generation backend may cite only citation ids present in this list.

## 7. Generation Boundary

Phase 2 defines a provider-neutral generation interface in `app/providers/generation.py`.

Recommended protocol:

```python
class GenerationProvider(Protocol):
    model_id: str

    def generate(self, request: GenerationRequest) -> GenerationResult:
        ...
```

Recommended request fields:

- `question`
- `prompt`
- `context`
- `context_items`
- `max_answer_sentences`

Recommended result fields:

- `answer`
- `cited_context_ids`
- `model_id`

Default backend:

- `backend = "local-grounded"`
- `model_id = "local-grounded-v1"`

The local grounded backend is deterministic. It should:

1. Tokenize the question.
2. Select sentences from context items that overlap with question terms.
3. Prefer higher-ranked context items.
4. Produce at most `max_answer_sentences`.
5. Add citation markers such as `[1]` for the context item used.
6. If no sentence overlaps, return a conservative answer based on the highest-ranked context item with its citation.
7. Never cite a context id that was not retrieved.

Justification:

- The API remains useful from a clean checkout.
- No paid API or hosted service is required.
- No secret is required.
- Generation is exercised through the same boundary a later model provider would use.
- Responses are deterministic enough for correctness tests.

This is not a final answer-quality strategy. It is a Phase 2 local generation backend that establishes the contract and grounding discipline. External model providers may be added later behind the same boundary when secrets and provider configuration are intentionally introduced.

## 8. API Design

### Endpoint

```text
POST /query
Content-Type: application/json
Accept: application/json
```

No authentication is required in Phase 2.

### Request Schema

```json
{
  "question": "What does Prisma mean by provider boundaries?",
  "top_k": 4,
  "max_context_chars": 4000
}
```

Validation:

- `question`: required string, trimmed length from 3 to 500 characters.
- `top_k`: optional integer, default from config, minimum 1, maximum `rag.max_top_k`.
- `max_context_chars`: optional integer, minimum 500, maximum configured hard limit.
- Unknown fields should be rejected.

### Response Schema

```json
{
  "answer": "Provider boundaries keep model and embedding details behind adapters. [1]",
  "citations": [
    {
      "citation_id": 1,
      "source_document": "Provider Boundaries",
      "source_path": "datasets/sample_corpus/provider-boundaries.md",
      "chunk_id": "<stable chunk id>",
      "chunk_index": 0,
      "score": 0.82
    }
  ],
  "retrieved_context": [
    {
      "citation_id": 1,
      "chunk_id": "<stable chunk id>",
      "source_document": "Provider Boundaries",
      "source_path": "datasets/sample_corpus/provider-boundaries.md",
      "chunk_index": 0,
      "score": 0.82,
      "text": "<retrieved chunk text>",
      "truncated": false
    }
  ],
  "metadata": {
    "retrieval_top_k": 4,
    "context_item_count": 1,
    "generation_backend": "local-grounded",
    "generation_model_id": "local-grounded-v1"
  }
}
```

### Error Schema

```json
{
  "error": {
    "code": "index_not_ready",
    "message": "Local index is missing. Run python -m app.retrieval.index.",
    "details": {}
  }
}
```

### Status Codes

- `200 OK`: answer returned with citations.
- `422 Unprocessable Entity`: request validation failed.
- `404 Not Found`: retrieval completed but no context was available.
- `503 Service Unavailable`: local index is missing or not ready.
- `500 Internal Server Error`: unexpected application failure.

All responses are JSON.

## 9. Citations

Every successful answer must cite retrieved context.

Citation rules:

- A citation can only reference a retrieved context item.
- Every cited item must include `source_document`, `chunk_id`, and `source_path`.
- The `source_document` should be the chunk title from Phase 1 metadata.
- The `chunk_id` must be the stable Phase 1 chunk id.
- The `source_path` must be the relative repository path from the indexed payload.
- Citation ids are assigned by context assembly in retrieval rank order.
- Citation markers in `answer` must correspond to entries in `citations`.
- If generation produces no valid citation, the API must fail closed rather than invent one.

No hallucinated citations are allowed. The service should validate generation output before returning the response.

## 10. Prompt Strategy

Phase 2 uses one minimal prompt asset:

```text
prompts/baseline_rag.txt
```

Prompt intent:

- Answer only from supplied context.
- Cite every factual claim with provided citation ids.
- Say when the supplied context is insufficient.
- Do not invent citations.
- Do not use outside knowledge.

Constraints:

- No prompt registry.
- No prompt versioning.
- No prompt management system.
- No prompt regression.
- No prompt directory beyond the single Phase 2 prompt asset.

The prompt is a data asset because the repository architecture says prompts are data, not hardcoded strings in `app/`. The code may load this one file directly from the configured path.

## 11. Testing Strategy

Phase 2 tests are correctness tests. They are not evaluation and must not create `evals/`.

Required tests:

- API returns `200` for a valid question after the local index exists.
- API response matches the response schema.
- API rejects empty, too-short, too-long, malformed, and unknown-field requests.
- API returns a structured error when the index is missing.
- Retrieval wrapper returns top-k chunks with required metadata.
- Retrieval uses deterministic ordering for repeated identical queries.
- Context assembly preserves retrieval order.
- Context assembly uses required separators and citation ids.
- Context assembly respects `max_context_chars`.
- Context assembly preserves metadata during truncation.
- Generation provider returns deterministic answers for the same input.
- Generation provider cites only supplied context ids.
- RAG service rejects generated citations that are not in context.
- Successful API answers include citations with `source_document`, `chunk_id`, and `source_path`.
- The smoke query returns an answer citing `datasets/sample_corpus/provider-boundaries.md`.

Recommended smoke question:

```text
What does Prisma mean by provider boundaries?
```

Expected citation source:

```text
datasets/sample_corpus/provider-boundaries.md
```

Test setup should reuse Phase 1 indexing against temporary paths where possible. Tests may call `run_indexing()` with test settings; they should not rely on committed generated `.local` artifacts.

## 12. Configuration

Phase 2 should extend `configs/defaults.toml` with non-secret keys.

Recommended keys:

```toml
[api]
host = "127.0.0.1"
port = 8000

[rag]
default_top_k = 4
max_top_k = 8
min_question_chars = 3
max_question_chars = 500
max_context_chars = 4000
max_context_chars_hard_limit = 8000
max_answer_sentences = 3

[generation]
backend = "local-grounded"
model_id = "local-grounded-v1"
prompt_path = "prompts/baseline_rag.txt"
```

No secrets are required.

If a later provider backend needs secrets, that must be planned separately and must follow ADR-0003. Phase 2 should not introduce `.env` or `.env.example`.

## 13. Validation Commands

After Phase 2 implementation, these commands must pass:

```sh
python -m ruff check .
python -m ruff format --check .
python -m mypy app
python -m pytest
```

The API smoke path must also pass:

```sh
python -m app.retrieval.index
python - <<'PY'
from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)
response = client.post(
    "/query",
    json={"question": "What does Prisma mean by provider boundaries?", "top_k": 4},
)
assert response.status_code == 200, response.text
body = response.json()
assert body["answer"]
assert body["citations"]
assert body["citations"][0]["source_path"] == "datasets/sample_corpus/provider-boundaries.md"
assert body["citations"][0]["chunk_id"]
print(body["answer"])
PY
```

Forbidden path checks:

```sh
test ! -d evals
test ! -d docker
test ! -d .github
test ! -d scripts
test ! -f .env
test ! -f .env.example
test ! -f requirements.txt
```

Manual local server check, optional after automated smoke passes:

```sh
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

Then in a second terminal:

```sh
curl -s \
  -H "Content-Type: application/json" \
  -d '{"question":"What does Prisma mean by provider boundaries?","top_k":4}' \
  http://127.0.0.1:8000/query
```

## 14. Deliverables

Phase 2 implementation delivers:

- Minimal FastAPI application.
- `POST /query` endpoint.
- Typed request, response, citation, retrieved-context, metadata, and error schemas.
- Query-facing retrieval wrapper over the Phase 1 local vector index.
- Deterministic context assembly.
- Provider-neutral generation protocol.
- Deterministic local grounded generation backend.
- One minimal prompt asset under `prompts/`.
- Citation validation.
- Structured error handling.
- API and service correctness tests.
- Updated non-secret configuration defaults.
- Updated README and development docs.

### Implementation Task Order

1. Add FastAPI/Pydantic API dependencies and Phase 2 config settings.
2. Add request/response/error schema models.
3. Add retrieval search wrapper tests and implementation.
4. Add context assembly tests and implementation.
5. Add minimal prompt asset and prompt loading.
6. Add provider-neutral generation tests and local grounded backend.
7. Add RAG service orchestration tests and implementation.
8. Add FastAPI app, route, and error handlers with tests.
9. Update README and development docs.
10. Run validation commands and forbidden-path checks.

Each task should preserve the Phase 2 boundary and avoid Phase 3+ capabilities.

## 15. Risks

### Scope Creep Toward Agents

Risk: The endpoint grows planning, re-retrieval loops, tool use, or graph abstractions.

Mitigation: Keep the flow linear: retrieve once, assemble once, generate once.

### Retrieval Leakage

Risk: API or generation code reaches into Qdrant payload details directly.

Mitigation: Add `app/retrieval/search.py` as the query-facing retrieval boundary. API and generation consume typed retrieval/context records.

### Oversized Contexts

Risk: Retrieved text grows beyond manageable prompt/context limits.

Mitigation: Enforce `max_context_chars`, deterministic truncation, and tests for truncation metadata.

### Provider Coupling

Risk: Generation introduces provider-specific concepts outside the provider boundary.

Mitigation: Use only `GenerationProvider` and `GenerationResult` outside `app/providers/generation.py`.

### Unstable Responses

Risk: Local generation varies across runs, making tests unreliable.

Mitigation: Use deterministic sentence selection and deterministic tie-breaking.

### Fake Citations

Risk: An answer cites chunks that were not retrieved.

Mitigation: Validate citations after generation. Fail closed if cited ids are not in the assembled context.

### Prompt Management Creep

Risk: A single prompt becomes a registry or versioning system too early.

Mitigation: Add one prompt file only. Defer prompt versioning and regression to later phases.

## 16. Success Criteria

Phase 2 is complete when:

- `POST /query` returns a successful structured JSON response for a valid question after the local index is built.
- The response contains `answer`, `citations`, `retrieved_context`, and `metadata`.
- Every successful answer has deterministic citations.
- Every citation includes `source_document`, `chunk_id`, and `source_path`.
- Retrieval returns relevant chunks from the Phase 1 local index.
- The provider-neutral generation boundary is used.
- The default generation backend runs locally without secrets or hosted services.
- API validation rejects invalid requests.
- Missing-index and no-context cases return structured errors.
- All Phase 2 correctness tests pass.
- No evaluation harness is introduced.
- No Phase 3 agent workflow, LangGraph usage, re-retrieval loop, planner, or tool abstraction is introduced.
- No Docker, CI, hosted service, authentication, UI, streaming, reranking, or hybrid search is introduced.

## 17. Recommended Next Natural Step

Review this Phase 2 plan against the approved project plan, repository architecture, Phase 1 implementation, and ADRs.

After review, implement Phase 2 as one focused development slice.

After Phase 2 implementation is complete and validated, the next planned phase is **Phase 3 — Agent Workflow**.
