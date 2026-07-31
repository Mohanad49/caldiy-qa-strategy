from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CleanupFailure:
    label: str
    error: str


@dataclass(slots=True)
class CleanupStack:
    _callbacks: list[tuple[str, Callable[[], None]]] = field(default_factory=list)

    def add(self, label: str, callback: Callable[[], None]) -> None:
        self._callbacks.append((label, callback))

    def close(self) -> list[CleanupFailure]:
        failures: list[CleanupFailure] = []
        while self._callbacks:
            label, callback = self._callbacks.pop()
            try:
                callback()
            except Exception as error:  # cleanup must attempt the rest of the LIFO stack
                failures.append(CleanupFailure(label=label, error=f"{type(error).__name__}: {error}"))
        return failures
