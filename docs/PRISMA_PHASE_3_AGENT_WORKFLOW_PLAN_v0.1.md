# Phase 3 Agent Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a small bounded workflow over the Phase 2 RAG capability so Prisma can inspect, route, optionally re-retrieve once, and return cited answers with workflow metadata.

**Architecture:** Phase 3 keeps `POST /query` as the public API and introduces an internal workflow layer under `app/workflow/`. The workflow is a deterministic state machine, not an autonomous agent, and it coordinates the existing retrieval, context assembly, generation, and citation validation components without adding hosted services or provider-specific APIs.

**Tech Stack:** Python 3.11, FastAPI, Pydantic, pytest, ruff, mypy, Qdrant local mode, deterministic local embeddings, deterministic local grounded generation, and a small internal workflow runner.

---

> Production LLM Engineering Platform
> Planning document only. This document defines what Phase 3 should implement. It does not implement code, create directories, or modify application files.

**Status:** Draft v0.1
**Date:** 2026-06-30
**Document:** PRISMA_PHASE_3_AGENT_WORKFLOW_PLAN_v0.1.md
**Audience:** developers, AI engineers, ML engineers, technical reviewers, and maintainers
**Companions:** [PRISMA_PROJECT_PLAN_v0.1.md](PRISMA_PROJECT_PLAN_v0.1.md), [PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md](PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md), [PRISMA_PHASE_1_INGESTION_INDEXING_PLAN_v0.1.md](PRISMA_PHASE_1_INGESTION_INDEXING_PLAN_v0.1.md), [PRISMA_PHASE_2_BASELINE_RAG_API_PLAN_v0.1.md](PRISMA_PHASE_2_BASELINE_RAG_API_PLAN_v0.1.md), [ADR-0001](adr/ADR-0001-code-data-separation.md), [ADR-0002](adr/ADR-0002-provider-adapter-boundary.md), [ADR-0003](adr/ADR-0003-secrets-via-environment.md), [ADR-0004](adr/ADR-0004-evaluation-first-development.md)

---

## 1. Purpose

Phase 3 exists to turn the Phase 2 linear RAG path into a bounded workflow that can make explicit, inspectable decisions before returning an answer.

Phase 2 proved that Prisma can:

- accept a typed query request,
- retrieve relevant chunks from the local Phase 1 index,
- assemble bounded context,
- generate a deterministic grounded answer,
- validate citations,
- return a structured API response.

Phase 3 builds directly on that capability. It introduces explicit workflow state and deterministic routing around the same retrieval and generation components. The workflow can validate a query, decide that grounded retrieval is required, retrieve context, assess whether that context is usable, optionally rewrite the query once, retry retrieval once, assemble context, generate an answer, validate citations, and return workflow metadata with the existing response.

The purpose is controlled orchestration, not autonomy. Phase 3 should make Prisma's RAG behavior easier to inspect and test without adding open-ended agents, tools, memory, hosted infrastructure, or evaluation machinery.

## 2. Scope

### In Scope

- Bounded workflow orchestration over the existing Phase 2 RAG capability.
- Explicit workflow state for each request.
- Deterministic routing decisions.
- Deterministic context sufficiency checks.
- Optional single re-retrieval after deterministic query rewrite.
- Query rewrite for one retry only.
- Workflow metadata in successful API responses.
- Structured workflow details on no-context failures where useful.
- Correctness tests for workflow state transitions, routing, rewrite, re-retrieval bounds, citation validation, and API compatibility.
- README and development-doc updates for the workflow smoke path.
- Non-secret workflow configuration defaults.

### Explicit Non-Goals

- No open-ended agents.
- No autonomous tool use.
- No multi-agent systems.
- No LangGraph Platform.
- No LangGraph dependency in Phase 3.
- No MCP.
- No A2A.
- No memory.
- No conversation history.
- No human-in-the-loop workflow.
- No evaluation harness.
- No `evals/` directory.
- No prompt regression.
- No prompt registry or prompt versioning system.
- No CI/CD.
- No Docker.
- No `.github/` workflows.
- No hosted services.
- No UI.
- No authentication.
- No authorization.
- No reranking.
- No hybrid search.
- No streaming responses.
- No provider-specific model APIs.
- No secrets.
- No `.env` or `.env.example`.
- No `requirements.txt`.

## 3. Architectural Alignment

### Project Plan

The project plan defines Phase 3 as the point where Prisma introduces a bounded agent workflow that can reason about retrieval. This plan implements that slice by adding explicit state, routing, retrieval attempts, one deterministic rewrite path, and workflow metadata.

This plan does not add Phase 4 evaluation assets, Phase 5 prompt regression, Phase 6 observability budgets, Phase 7 CI, or Phase 8 Docker/reproducibility polish.

### Repository Architecture

The repository architecture places agent workflow logic inside `app/`. Phase 3 should therefore introduce `app/workflow/` as executable application logic and `tests/workflow/` as code correctness tests.

The planned control flow becomes:

```text
API -> RAG service facade -> workflow runner -> retrieval/context/generation -> structured response
```

The workflow layer coordinates existing components. It does not embed retrieval internals, provider details, prompt logic, persistence details, or API transport concerns.

### Phase 1

Phase 3 continues to rely on the Phase 1 local Qdrant index, deterministic chunk identifiers, deterministic local embeddings, and committed sample corpus. It does not change ingestion, indexing, chunking, document loading, or vector persistence.

### Phase 2

Phase 3 preserves the Phase 2 `POST /query` endpoint and existing response fields:

- `answer`
- `citations`
- `retrieved_context`
- `metadata`

It adds workflow metadata without removing or renaming Phase 2 fields. The same provider-neutral generation boundary, prompt asset, context assembly behavior, and citation validation discipline continue to apply.

### ADR-0001: Code / Data Separation

Workflow business logic lives inside `app/workflow/`. Configuration remains declarative in `configs/defaults.toml`. Prompt assets remain under `prompts/`. No workflow logic is placed in prompts, datasets, or configuration.

### ADR-0002: Provider Adapter Boundary

The workflow never imports provider SDKs or assumes provider-specific response objects. It calls existing provider-neutral generation and embedding boundaries indirectly through retrieval and generation services.

### ADR-0003: Secrets via Environment

Phase 3 requires no secrets. All workflow configuration is non-secret: enablement, maximum retrieval attempts, sufficiency thresholds, and rewrite behavior. No `.env` or `.env.example` is introduced.

### ADR-0004: Evaluation-First Development

Phase 3 includes a clear evaluation strategy for the future: workflow metadata, deterministic routing, stable citations, and explicit state will make Phase 4 evaluation measurable through the public API.

Phase 3 itself adds correctness tests only. It does not create the Phase 4 evaluation harness, golden datasets, scorecards, or baselines.

## 4. Workflow Model

Phase 3 should implement a small internal state machine. LangGraph is not justified for this phase because the graph is fixed, deterministic, local, and small enough to test directly without another runtime dependency.

### Nodes

| Node | Responsibility |
|---|---|
| `validate_query` | Trim and validate the question plus request-level bounds using the same limits enforced in Phase 2. Validation failure is terminal and performs no retrieval. |
| `decide_retrieval` | Record that grounded retrieval is required for every valid Phase 3 answer. Phase 3 has no non-retrieval answer path. |
| `retrieve_context` | Query the existing Phase 1 local index through the Phase 2 retrieval wrapper. Increment retrieval attempts exactly once per retrieval call. |
| `assess_context` | Decide whether retrieved chunks are usable according to deterministic sufficiency rules. |
| `rewrite_query` | Rewrite the active query deterministically for one retry only when context is insufficient and retry is allowed. |
| `assemble_context` | Assemble retrieved chunks into bounded context using the existing context assembly behavior. |
| `generate_answer` | Call the provider-neutral generation boundary with the assembled context. |
| `validate_citations` | Verify generated citation ids and answer markers reference only assembled context items. Fail closed on invalid citations. |
| `finalize_response` | Build the existing structured response and add workflow metadata. |

### Allowed Transitions

```text
validate_query -> decide_retrieval
validate_query -> terminal(validation_failed)

decide_retrieval -> retrieve_context

retrieve_context -> assess_context
retrieve_context -> terminal(index_not_ready)

assess_context -> assemble_context
assess_context -> rewrite_query
assess_context -> terminal(no_context)

rewrite_query -> retrieve_context
rewrite_query -> terminal(no_context)

assemble_context -> generate_answer
assemble_context -> terminal(no_context)

generate_answer -> validate_citations

validate_citations -> finalize_response
validate_citations -> terminal(citation_failed)

finalize_response -> terminal(completed)
```

No other transitions are allowed.

### Terminal States

- `completed`: answer returned with citations and workflow metadata.
- `validation_failed`: invalid query or request bounds; mapped to existing structured `422` behavior.
- `index_not_ready`: local index missing; mapped to existing structured `503 index_not_ready` behavior.
- `no_context`: retrieval and optional retry did not produce sufficient context; mapped to structured `404 no_context`.
- `citation_failed`: generated answer failed citation validation; mapped to structured `500 invalid_citations`.
- `failed`: unexpected workflow failure; mapped to structured `500 internal_error`.

### Retrieval Attempt Bound

The maximum number of retrieval attempts is `2`:

1. first attempt with the original question,
2. optional second attempt with one deterministic rewritten query.

The workflow must never perform a third retrieval attempt. The workflow must not loop.

## 5. State Model

Phase 3 should define explicit workflow state in `app/workflow/state.py`.

Recommended state fields:

- `original_question`: the trimmed user question.
- `active_query`: the query used for the current retrieval attempt.
- `top_k`: resolved retrieval limit.
- `max_context_chars`: resolved context budget.
- `retrieval_attempts`: count of retrieval calls made.
- `max_retrieval_attempts`: configured hard attempt limit.
- `retrieved_chunks`: retrieved chunks from the most recent successful retrieval attempt.
- `context_items`: assembled context items with citation ids.
- `generation_result`: provider-neutral generation result, if generation ran.
- `citations`: validated citations for the final response.
- `errors`: structured workflow errors encountered before terminal failure.
- `workflow_events`: ordered event list recording node execution and routing decisions.
- `rewritten_query`: rewritten query used for retry, or `None`.
- `context_sufficient`: boolean assessment result for the active attempt.
- `final_status`: terminal workflow status.

Recommended workflow event fields:

- `node`: workflow node name.
- `status`: `started`, `completed`, `skipped`, or `failed`.
- `message`: short deterministic description.
- `details`: JSON-serializable dictionary with non-secret debug details.

Workflow events are returned only as request-local metadata. Phase 3 must not persist traces or run records; persistent observability remains a later phase.

## 6. Routing Rules

Routing must be deterministic and testable.

Rules:

1. If the question is shorter than the configured minimum, `validate_query` fails and no retrieval occurs.
2. If the question is longer than the configured maximum, `validate_query` fails and no retrieval occurs.
3. If `top_k` or `max_context_chars` violates configured limits, `validate_query` fails and no retrieval occurs.
4. Every valid Phase 3 question proceeds to retrieval because answers must be grounded in retrieved context.
5. If the index is missing, the workflow stops with `index_not_ready` and preserves the existing `503` error code and message.
6. If first retrieval returns sufficient context, the workflow proceeds directly to context assembly.
7. If first retrieval returns no chunks or insufficient chunks, and query rewrite is enabled, the workflow performs one deterministic rewrite.
8. If the rewritten query is empty or identical to the active query, the workflow does not retry and returns `no_context`.
9. If retry is allowed, the workflow performs exactly one second retrieval.
10. If the second retrieval returns no sufficient context, the workflow returns `no_context`.
11. If context assembly yields no context items, the workflow returns `no_context`.
12. If generation returns no citation ids, unknown citation ids, or answer markers that do not match returned citation ids, the workflow fails closed with `invalid_citations`.
13. Successful responses include the existing Phase 2 fields plus workflow metadata.

## 7. Query Rewrite Strategy

Phase 3 query rewrite must be deterministic and transparent. It must not call an LLM.

Recommended rewrite steps:

1. Lowercase the original question.
2. Remove punctuation except whitespace and alphanumeric characters.
3. Tokenize on whitespace.
4. Remove a small fixed stopword set committed in code.
5. Preserve token order.
6. Remove duplicate tokens while preserving first occurrence.
7. Join remaining tokens with a single space.

Example:

```text
Original:  "What does Prisma mean by provider boundaries?"
Rewritten: "prisma provider boundaries"
```

Fallback behavior:

- If rewrite produces an empty string, keep `rewritten_query = None` and do not retry.
- If rewrite is identical to the active query, keep `rewritten_query = None` and do not retry.
- If rewrite produces a shorter useful query, retry once with that query.

Do not append terms from external sources. Do not inspect hosted services. Do not infer synonyms. Do not use prompt assets for rewrite rules.

## 8. Context Sufficiency Strategy

Phase 3 sufficiency checks must be deterministic and local. Do not introduce an LLM-as-judge.

Initial sufficiency rules:

1. At least one chunk exists after retrieval.
2. At least one chunk has `score >= workflow.min_context_score`.
3. At least one eligible chunk has non-empty text after trimming.
4. At least one non-stopword query token appears in the eligible chunk text.

If all rules pass, context is sufficient.

If any rule fails on the first attempt, the workflow may perform one rewrite retry when enabled.

If any rule fails on the second attempt, the workflow returns structured `no_context`.

This is intentionally simple. It is not a quality metric and must not be treated as an evaluation score.

## 9. Integration with Existing RAG Service

Phase 3 should preserve the API-facing `RagService` abstraction and have it delegate to the workflow runner when workflow execution is enabled.

Recommended integration:

1. Keep `app/api/routes.py` stable so the route still depends on `RagService`.
2. Add `app/workflow/runner.py` with a `RagWorkflowRunner` that orchestrates the existing retrieval, context assembly, generation provider, and citation validation behavior.
3. Modify `app/generation/service.py` so `RagService.answer()` delegates to `RagWorkflowRunner` by default when `settings.workflow.enabled` is true.
4. Keep existing Phase 2 helper behavior available through private functions or small shared helpers; do not duplicate citation response shaping in multiple places if a small extraction is cleaner.
5. Preserve Phase 2 errors and response fields.

The implementation should be a minimal refactor. It should not rewrite retrieval, generation, FastAPI route registration, prompt loading, or Qdrant persistence.

## 10. API Changes

`POST /query` remains the only Phase 3 endpoint.

Request schema remains unchanged:

```json
{
  "question": "What does Prisma mean by provider boundaries?",
  "top_k": 4,
  "max_context_chars": 4000
}
```

Successful response keeps all Phase 2 fields and adds a top-level `workflow` object:

```json
{
  "answer": "Provider boundaries keep model details behind adapters. [1]",
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
  },
  "workflow": {
    "status": "completed",
    "retrieval_attempts": 1,
    "max_retrieval_attempts": 2,
    "route": [
      "validate_query",
      "decide_retrieval",
      "retrieve_context",
      "assess_context",
      "assemble_context",
      "generate_answer",
      "validate_citations",
      "finalize_response"
    ],
    "rewritten_query": null,
    "context_sufficient": true
  }
}
```

Error schema remains unchanged:

```json
{
  "error": {
    "code": "no_context",
    "message": "No sufficient context was retrieved for the question.",
    "details": {
      "workflow": {
        "status": "no_context",
        "retrieval_attempts": 2,
        "rewritten_query": "prisma provider boundaries"
      }
    }
  }
}
```

Do not add streaming, authentication, session state, conversation ids, or new endpoints in Phase 3.

## 11. Testing Strategy

Phase 3 tests are correctness tests. They are not evaluation tests and must not create `evals/`.

Required tests:

- Workflow state initializes from the request with expected defaults.
- `validate_query` failures do not call retrieval.
- Valid queries route to retrieval.
- First-attempt sufficient context routes to context assembly and generation.
- First-attempt no context triggers one rewrite when rewrite is enabled.
- Rewritten query behavior is deterministic.
- Rewritten query retry never exceeds two total retrieval attempts.
- Empty or unchanged rewrites do not cause duplicate retrieval.
- No context after the second attempt returns structured `no_context`.
- Context sufficiency requires non-empty text and configured minimum score.
- Context sufficiency uses deterministic token overlap and no LLM judge.
- Citation validation still fails closed on unknown citations.
- `POST /query` preserves existing Phase 2 fields.
- `POST /query` returns workflow metadata on success.
- Missing index still returns `503 index_not_ready`.
- No Phase 4 evaluation files or directories are created.

Recommended test files:

```text
tests/workflow/test_state.py
tests/workflow/test_routing.py
tests/workflow/test_runner.py
tests/api/test_query_endpoint.py
tests/api/test_error_responses.py
tests/generation/test_rag_service.py
```

Test setup should keep using temporary index paths and `run_indexing()` where index-backed behavior is required. Unit tests for routing and rewrite should not require Qdrant.

## 12. Configuration

Phase 3 should extend `configs/defaults.toml` with non-secret workflow keys:

```toml
[workflow]
enabled = true
max_retrieval_attempts = 2
min_context_score = 0.0
enable_query_rewrite = true
require_context_token_overlap = true
```

Configuration rules:

- `max_retrieval_attempts` must be `2` in Phase 3.
- Values greater than `2` are out of scope and should fail configuration validation.
- `min_context_score` is a deterministic threshold, not an evaluation metric.
- `enable_query_rewrite = false` should keep the workflow linear after first retrieval.
- No secrets are needed.

## 13. Repository Changes

Phase 3 implementation should create or modify only the paths listed here.

### Create Directories

```text
app/workflow/
tests/workflow/
```

Do not create `evals/`, `docker/`, `.github/`, `scripts/`, UI directories, MCP directories, or agent-platform directories.

### Create Application Files

```text
app/workflow/__init__.py
app/workflow/state.py
app/workflow/routing.py
app/workflow/runner.py
```

Responsibilities:

- `app/workflow/state.py`: workflow status values, event model, error model, and explicit request state.
- `app/workflow/routing.py`: deterministic rewrite, tokenization, sufficiency checks, and route decisions.
- `app/workflow/runner.py`: node orchestration for the bounded workflow.

### Create Test Files

```text
tests/workflow/test_state.py
tests/workflow/test_routing.py
tests/workflow/test_runner.py
```

### Modify Existing Files

```text
app/config.py
configs/defaults.toml
app/models/rag.py
app/generation/service.py
tests/api/test_query_endpoint.py
tests/api/test_error_responses.py
tests/generation/test_rag_service.py
README.md
docs/DEVELOPMENT.md
```

Required modifications:

- `app/config.py`: add typed workflow settings and validation that `max_retrieval_attempts` is exactly `2` for Phase 3.
- `configs/defaults.toml`: add the `[workflow]` section.
- `app/models/rag.py`: add `WorkflowMetadata` and include it in successful query responses.
- `app/generation/service.py`: keep `RagService` as the API-facing facade and delegate to the workflow runner.
- API tests: assert existing response fields remain and workflow metadata is present.
- Service tests: verify workflow-backed service behavior and citation failure behavior.
- README and development docs: document workflow behavior and smoke commands.

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

No new runtime dependency is expected for Phase 3. Do not add LangGraph or platform dependencies unless a separate ADR supersedes this plan.

## 14. Validation Commands

After Phase 3 implementation, these commands must pass:

```sh
python -m ruff check .
python -m ruff format --check .
python -m mypy app
python -m pytest
python -m app.retrieval.index
```

Existing API smoke path:

```sh
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
assert body["retrieved_context"]
assert body["metadata"]
print(body["answer"])
PY
```

Workflow-specific smoke path:

```sh
python - <<'PY'
from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)
response = client.post(
    "/query",
    json={"question": "What does Prisma mean by provider boundaries?", "top_k": 4},
)
assert response.status_code == 200, response.text
workflow = response.json()["workflow"]
assert workflow["status"] == "completed"
assert 1 <= workflow["retrieval_attempts"] <= 2
assert workflow["max_retrieval_attempts"] == 2
assert workflow["route"][0] == "validate_query"
assert "finalize_response" in workflow["route"]
print(workflow)
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

Additional repository checks:

```sh
git diff --check
tree -a -L 4
git status --short
```

## 15. Deliverables

Phase 3 deliverables:

- Internal bounded workflow package under `app/workflow/`.
- Explicit workflow state and event records.
- Deterministic routing decisions.
- Deterministic query rewrite for one retry only.
- Deterministic context sufficiency checks.
- Workflow-backed `RagService` preserving `POST /query`.
- Successful API responses with workflow metadata.
- Structured no-context behavior after at most two retrieval attempts.
- Correctness tests for workflow state, routing, rewrite, runner behavior, API compatibility, and citation validation.
- Non-secret `[workflow]` defaults.
- README and development guide updates.

## 16. Risks

### Agent Scope Creep

Risk: The workflow could become an open-ended agent.

Mitigation: Use a fixed internal state machine, a fixed node list, explicit transitions, and `max_retrieval_attempts = 2`.

### Hidden Autonomy

Risk: Query rewrite or routing could quietly become model-driven.

Mitigation: Keep rewrite and routing as deterministic string/token logic. Do not call the generation provider for routing.

### Brittle Routing

Risk: Token-overlap sufficiency can reject useful context or accept weak context.

Mitigation: Treat sufficiency as a simple Phase 3 guardrail, not a quality metric. Phase 4 evaluation will measure answer quality.

### Query Rewrite Harming Retrieval

Risk: Removing stopwords or punctuation can make retrieval worse.

Mitigation: Retry at most once, preserve original query in state, and include tests for deterministic rewrite behavior.

### Response Schema Drift

Risk: Adding workflow metadata could break existing clients or tests.

Mitigation: Preserve all existing Phase 2 response fields and add only a new top-level `workflow` object.

### Confusing Workflow Tests with Evals

Risk: Tests could start asserting answer quality instead of code behavior.

Mitigation: Tests verify transitions, bounds, fields, and citation integrity only. No golden-answer scoring, baselines, or scorecards are introduced.

## 17. Success Criteria

Phase 3 is complete when:

- A bounded workflow is implemented under `app/workflow/`.
- `POST /query` still works with the existing Phase 2 request shape.
- Existing response fields remain present and compatible.
- Successful responses include workflow metadata.
- The workflow performs at most one re-retrieval.
- Query rewrite is deterministic and non-LLM-based.
- Context sufficiency is deterministic and non-LLM-based.
- Citation validation still fails closed.
- Missing index still returns structured `503 index_not_ready`.
- No-context after the retry path returns structured `404 no_context`.
- Deterministic correctness tests pass.
- No Phase 4 evaluation harness, `evals/`, prompt regression, CI, Docker, hosted service, multi-agent, tool-use, memory, or UI capability is introduced.

## 18. Recommended Next Natural Step

Review this Phase 3 plan against the approved architecture and ADRs. After approval, implement Phase 3 Agent Workflow as one focused development slice.

Expected next phase after implementation:

- Phase 4 - Evaluation Harness.
