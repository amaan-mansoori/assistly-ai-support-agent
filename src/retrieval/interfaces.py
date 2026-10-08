"""Structural interface shared by retrieval implementations."""
from __future__ import annotations

from typing import Any, Protocol


class Retriever(Protocol):
    def retrieve(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """Return historical customer/response pairs with normalized scores."""
        ...
