"""Inspect the latest local Prisma runtime artifact.

Invoke with:

    python -m app.observability.inspect
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.config import PrismaSettings, load_settings
from app.observability.models import RuntimeEvent, RuntimeMetrics
from app.observability.runtime import RuntimeRecorder, is_safe_request_id


class RuntimeArtifactError(RuntimeError):
    """Raised when a runtime artifact cannot be loaded."""


def main(argv: list[str] | None = None, settings: PrismaSettings | None = None) -> int:
    """CLI entry point for `python -m app.observability.inspect`."""

    parser = argparse.ArgumentParser(description="Inspect local Prisma runtime artifacts.")
    parser.add_argument("--request-id", help="Read requests/<request_id>.json instead of latest.")
    args = parser.parse_args(argv)

    resolved_settings = settings or load_settings()
    try:
        events, metrics, path = load_runtime_artifact(
            settings=resolved_settings,
            request_id=args.request_id,
        )
    except RuntimeArtifactError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(render_summary(events=events, metrics=metrics, path=path))
    return 0


def load_runtime_artifact(
    *,
    settings: PrismaSettings,
    request_id: str | None = None,
) -> tuple[list[RuntimeEvent], RuntimeMetrics, Path]:
    """Load and validate one generated runtime artifact without mutating it."""

    runtime_dir = RuntimeRecorder.from_settings(settings).runtime_dir()
    if request_id is None:
        path = runtime_dir / "latest-request.json"
    else:
        if not is_safe_request_id(request_id):
            raise RuntimeArtifactError("request_id must be a UUID4 hex string")
        path = runtime_dir / "requests" / f"{request_id}.json"

    if not path.exists():
        raise RuntimeArtifactError("no runtime artifact found; issue a request first")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeArtifactError(f"invalid runtime artifact JSON: {exc.msg}") from exc
    except OSError as exc:
        raise RuntimeArtifactError(f"unable to read runtime artifact: {exc}") from exc

    if not isinstance(raw, dict):
        raise RuntimeArtifactError("runtime artifact must be a JSON object")
    return _parse_artifact(raw, path)


def render_summary(
    *,
    events: list[RuntimeEvent],
    metrics: RuntimeMetrics,
    path: Path,
) -> str:
    """Render a concise runtime summary for local inspection."""

    lines = [
        "Prisma runtime request",
        f"Artifact: {path.as_posix()}",
        f"Request ID: {metrics.request_id}",
        f"Status: {metrics.status}",
        f"Total latency: {metrics.total_latency_ms:.3f} ms",
        f"Retrieval latency: {metrics.retrieval_latency_ms:.3f} ms",
        f"Context assembly latency: {metrics.context_assembly_latency_ms:.3f} ms",
        f"Generation latency: {metrics.generation_latency_ms:.3f} ms",
        f"Validation latency: {metrics.validation_latency_ms:.3f} ms",
        f"Retrieval attempts: {metrics.retrieval_attempts}",
        f"Retrieved context count: {metrics.retrieved_context_count}",
        f"Citation count: {metrics.citation_count}",
        (
            "Workflow route: "
            f"{' -> '.join(metrics.workflow_route) if metrics.workflow_route else '(none)'}"
        ),
        f"Generation backend: {metrics.generation_backend or '(none)'}",
        f"Generation model: {metrics.generation_model_id or '(none)'}",
        f"Events: {len(events)}",
    ]
    if metrics.error_code is not None:
        lines.insert(4, f"Error code: {metrics.error_code}")
    return "\n".join(lines)


def _parse_artifact(
    raw: dict[str, Any],
    path: Path,
) -> tuple[list[RuntimeEvent], RuntimeMetrics, Path]:
    events_raw = raw.get("events")
    metrics_raw = raw.get("metrics")
    if not isinstance(events_raw, list):
        raise RuntimeArtifactError("runtime artifact events must be a list")
    if not isinstance(metrics_raw, dict):
        raise RuntimeArtifactError("runtime artifact metrics must be an object")

    try:
        events = [RuntimeEvent.model_validate(event) for event in events_raw]
        metrics = RuntimeMetrics.model_validate(metrics_raw)
    except ValidationError as exc:
        message = exc.errors()[0]["msg"]
        raise RuntimeArtifactError(f"invalid runtime artifact shape: {message}") from exc

    return events, metrics, path


if __name__ == "__main__":
    raise SystemExit(main())
