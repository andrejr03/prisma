"""Timing helpers for request-local runtime instrumentation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from time import perf_counter

from app.observability.models import RuntimeScalar

Clock = Callable[[], float]


@dataclass
class StageSpan:
    """Measure a runtime stage and carry safe scalar details for the event."""

    clock: Clock = perf_counter
    details: dict[str, RuntimeScalar] = field(default_factory=dict)
    _start: float | None = None

    def __enter__(self) -> StageSpan:
        self._start = self.clock()
        return self

    def __exit__(self, *_exc_info: object) -> None:
        return None

    def set_detail(self, key: str, value: RuntimeScalar) -> None:
        """Attach one non-secret scalar detail to the span."""

        self.details[key] = value

    def set_details(self, values: dict[str, RuntimeScalar]) -> None:
        """Attach non-secret scalar details to the span."""

        self.details.update(values)

    def elapsed_ms(self) -> float:
        """Return elapsed milliseconds since span entry."""

        if self._start is None:
            return 0.0
        return max((self.clock() - self._start) * 1000.0, 0.0)
