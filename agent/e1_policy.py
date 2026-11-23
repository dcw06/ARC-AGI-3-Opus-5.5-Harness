"""The result type a model backend returns to the harness.

In the parent project this module also holds that project's own policy. The harness imports only
`CompletionResult` (and the `CompletionClient` protocol it satisfies), so only those are kept here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True, slots=True)
class CompletionResult:
    content: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    elapsed_seconds: float | None = None


class CompletionClient(Protocol):
    def complete(self, request: Mapping[str, Any]) -> CompletionResult: ...
