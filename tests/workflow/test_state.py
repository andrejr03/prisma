from __future__ import annotations

from app.workflow.state import WorkflowState


def test_workflow_state_initializes_from_request():
    state = WorkflowState.from_request(
        question="  What does Prisma mean by provider boundaries?  ",
        top_k=4,
        max_context_chars=4000,
        max_retrieval_attempts=2,
    )

    assert state.original_question == "What does Prisma mean by provider boundaries?"
    assert state.active_query == state.original_question
    assert state.top_k == 4
    assert state.max_context_chars == 4000
    assert state.max_retrieval_attempts == 2
    assert state.retrieval_attempts == 0
    assert state.route() == []


def test_workflow_state_records_events_and_metadata():
    state = WorkflowState.from_request(
        question="provider boundaries",
        top_k=2,
        max_context_chars=1000,
        max_retrieval_attempts=2,
    )
    state.final_status = "completed"
    state.context_sufficient = True
    state.record_event(
        node="validate_query",
        status="completed",
        message="Query validated.",
    )
    state.record_event(
        node="retrieve_context",
        status="completed",
        message="Context retrieved.",
    )

    metadata = state.metadata()

    assert metadata.status == "completed"
    assert metadata.route == ["validate_query", "retrieve_context"]
    assert metadata.max_retrieval_attempts == 2
    assert metadata.rewritten_query is None
    assert metadata.context_sufficient is True
