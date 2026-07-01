"""Request-scoped runtime recorder and artifact writer."""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from app.config import ObservabilitySettings, PrismaSettings
from app.models.rag import QueryResponse
from app.observability.models import (
    RuntimeEvent,
    RuntimeEventStatus,
    RuntimeMetrics,
    RuntimeScalar,
    RuntimeStage,
    RuntimeSummary,
)
from app.observability.timing import Clock, StageSpan

_REQUEST_ID_RE = re.compile(r"^[a-f0-9]{32}$")
_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class RuntimeRecorder:
    """Collect request-local runtime events and write local artifacts."""

    repo_root: Path
    settings: ObservabilitySettings
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    clock: Clock = perf_counter
    _events: list[RuntimeEvent] = field(default_factory=list, init=False)
    _request_span: StageSpan | None = field(default=None, init=False)
    _context_char_count: int = field(default=0, init=False)
    _prompt_char_count: int = field(default=0, init=False)
    _retrieval_attempts: int = field(default=0, init=False)
    _workflow_route: list[str] = field(default_factory=list, init=False)

    @classmethod
    def from_settings(cls, settings: PrismaSettings) -> RuntimeRecorder:
        """Create a recorder from loaded application settings."""

        return cls(repo_root=settings.repo_root, settings=settings.observability)

    @property
    def enabled(self) -> bool:
        """Return whether event capture and artifact writing are enabled."""

        return self.settings.enabled

    @property
    def events(self) -> list[RuntimeEvent]:
        """Return recorded events in sequence order."""

        return list(self._events)

    def start_request(self) -> None:
        """Record the request-start event."""

        if not self.enabled:
            return
        self._validate_request_id()
        self._request_span = StageSpan(clock=self.clock)
        self._request_span.__enter__()
        self._record_event(stage="request", status="started")

    @contextmanager
    def stage(
        self,
        stage: RuntimeStage,
        *,
        error_code: str | None = None,
    ) -> Iterator[StageSpan]:
        """Record a completed or failed stage span around existing behavior."""

        if not self.enabled:
            yield StageSpan(clock=self.clock)
            return

        with StageSpan(clock=self.clock) as span:
            try:
                yield span
            except Exception:
                self._record_event(
                    stage=stage,
                    status="failed",
                    duration_ms=span.elapsed_ms(),
                    details=span.details,
                    error_code=error_code,
                )
                raise
            self._record_event(
                stage=stage,
                status="completed",
                duration_ms=span.elapsed_ms(),
                details=span.details,
            )

    def record_context(self, *, context: str) -> None:
        """Capture deterministic context metrics without storing context text."""

        if self.enabled:
            self._context_char_count = len(context)

    def record_prompt(self, *, prompt: str) -> None:
        """Capture deterministic prompt metrics without storing prompt text."""

        if self.enabled:
            self._prompt_char_count = len(prompt)

    def record_workflow_route(self, route: list[str]) -> None:
        """Capture workflow route metadata for failed requests without a response."""

        if self.enabled:
            self._workflow_route = list(route)

    def record_retrieval_attempts(self, attempts: int) -> None:
        """Capture retrieval attempts for failed requests without a response."""

        if self.enabled:
            self._retrieval_attempts = attempts

    def complete_response(self, response: QueryResponse) -> QueryResponse:
        """Finalize successful metrics, write artifacts, and return an updated response."""

        if not self.enabled:
            return response.model_copy(update={"runtime": None})

        metrics = self._finalize_metrics(response=response, status="completed", error_code=None)
        self._write_artifacts(metrics)
        return response.model_copy(update={"runtime": self.summary(metrics)})

    def fail_request(self, error_code: str) -> None:
        """Finalize failed metrics and write artifacts before re-raising the request error."""

        if not self.enabled:
            return

        metrics = self._finalize_metrics(response=None, status="failed", error_code=error_code)
        self._write_artifacts(metrics)

    def summary(self, metrics: RuntimeMetrics) -> RuntimeSummary:
        """Build the compact inline runtime summary."""

        return RuntimeSummary(
            request_id=metrics.request_id,
            total_latency_ms=metrics.total_latency_ms,
            retrieval_latency_ms=metrics.retrieval_latency_ms,
            context_assembly_latency_ms=metrics.context_assembly_latency_ms,
            generation_latency_ms=metrics.generation_latency_ms,
            validation_latency_ms=metrics.validation_latency_ms,
            retrieval_attempts=metrics.retrieval_attempts,
            citation_count=metrics.citation_count,
        )

    def _finalize_metrics(
        self,
        *,
        response: QueryResponse | None,
        status: str,
        error_code: str | None,
    ) -> RuntimeMetrics:
        request_duration = self._request_span.elapsed_ms() if self._request_span else 0.0
        self._record_event(
            stage="request",
            status="completed" if status == "completed" else "failed",
            duration_ms=request_duration,
            error_code=error_code,
        )

        if response is None:
            return RuntimeMetrics(
                request_id=self.request_id,
                total_latency_ms=request_duration,
                retrieval_latency_ms=self._stage_latency("retrieve_context"),
                context_assembly_latency_ms=self._stage_latency("assemble_context"),
                generation_latency_ms=self._stage_latency("generate_answer"),
                validation_latency_ms=self._stage_latency("validate_citations"),
                retrieval_attempts=self._retrieval_attempts,
                retrieved_context_count=0,
                retrieved_source_paths=[],
                citation_count=0,
                answer_char_count=0,
                generated_answer_sentence_count=0,
                context_char_count=self._context_char_count,
                prompt_char_count=self._prompt_char_count,
                workflow_route=self._workflow_route,
                generation_backend="",
                generation_model_id="",
                status="failed",
                error_code=error_code,
            )

        retrieved_paths = _stable_source_paths(
            item.source_path for item in response.retrieved_context
        )
        return RuntimeMetrics(
            request_id=self.request_id,
            total_latency_ms=request_duration,
            retrieval_latency_ms=self._stage_latency("retrieve_context"),
            context_assembly_latency_ms=self._stage_latency("assemble_context"),
            generation_latency_ms=self._stage_latency("generate_answer"),
            validation_latency_ms=self._stage_latency("validate_citations"),
            retrieval_attempts=response.workflow.retrieval_attempts,
            retrieved_context_count=len(response.retrieved_context),
            retrieved_source_paths=retrieved_paths,
            citation_count=len(response.citations),
            answer_char_count=len(response.answer),
            generated_answer_sentence_count=_sentence_count(response.answer),
            context_char_count=self._context_char_count,
            prompt_char_count=self._prompt_char_count,
            workflow_route=response.workflow.route,
            generation_backend=response.metadata.generation_backend,
            generation_model_id=response.metadata.generation_model_id,
            status="completed",
            error_code=None,
        )

    def _stage_latency(self, stage: RuntimeStage) -> float:
        return sum(
            event.duration_ms or 0.0
            for event in self._events
            if event.stage == stage and event.status in {"completed", "failed"}
        )

    def _record_event(
        self,
        *,
        stage: RuntimeStage,
        status: RuntimeEventStatus,
        duration_ms: float | None = None,
        details: dict[str, RuntimeScalar] | None = None,
        error_code: str | None = None,
    ) -> None:
        self._events.append(
            RuntimeEvent(
                request_id=self.request_id,
                sequence=len(self._events),
                timestamp=_utc_timestamp(),
                stage=stage,
                status=status,
                duration_ms=duration_ms,
                details=details or {},
                error_code=error_code,
            )
        )

    def _write_artifacts(self, metrics: RuntimeMetrics) -> None:
        runtime_dir = self.runtime_dir()
        payload: dict[str, Any] = {
            "events": [event.model_dump(mode="json") for event in self._events],
            "metrics": metrics.model_dump(mode="json"),
        }
        if self.settings.write_latest:
            _write_json(runtime_dir / "latest-request.json", payload)
        if self.settings.write_per_request:
            _write_json(runtime_dir / "requests" / f"{self.request_id}.json", payload)

    def runtime_dir(self) -> Path:
        """Resolve and validate the configured runtime artifact directory."""

        runtime_dir = self.repo_root / self.settings.runtime_dir
        if Path(self.settings.runtime_dir).is_absolute():
            runtime_dir = Path(self.settings.runtime_dir)

        try:
            relative_path = runtime_dir.resolve().relative_to(self.repo_root.resolve())
        except ValueError as exc:
            raise ValueError("Runtime artifact directory must be inside the repository") from exc

        relative = relative_path.as_posix()
        if relative != ".local" and not relative.startswith(".local/"):
            raise ValueError("Runtime artifact directory must be under .local/")
        return runtime_dir

    def _validate_request_id(self) -> None:
        if not is_safe_request_id(self.request_id):
            raise ValueError("Runtime request_id must be a UUID4 hex string")


def is_safe_request_id(request_id: str) -> bool:
    """Return whether a request id is safe for artifact filenames."""

    return bool(_REQUEST_ID_RE.fullmatch(request_id))


def _stable_source_paths(paths: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        ordered.append(path)
    return ordered


def _sentence_count(text: str) -> int:
    return len([sentence for sentence in _SENTENCE_BOUNDARY_RE.split(text.strip()) if sentence])


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
