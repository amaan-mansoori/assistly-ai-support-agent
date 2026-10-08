"""Bounds recent conversational context before classification and generation."""
from __future__ import annotations

from collections.abc import Sequence


def bounded_conversation_history(
    history: Sequence[str],
    *,
    max_turns: int,
    max_chars: int,
) -> tuple[str, ...]:
    if max_turns < 1 or max_chars < 1:
        raise ValueError("conversation history limits must be positive")
    recent = [turn.strip() for turn in history if turn.strip()][-max_turns:]
    selected: list[str] = []
    remaining = max_chars
    for turn in reversed(recent):
        if remaining <= 0:
            break
        bounded = turn[-remaining:]
        selected.append(bounded)
        remaining -= len(bounded)
    return tuple(reversed(selected))
