import pytest

from src.agent.context import bounded_conversation_history


def test_bounded_history_keeps_recent_nonempty_turns_within_character_budget():
    history = bounded_conversation_history(
        [" old ", "", "middle", "newest"],
        max_turns=2,
        max_chars=20,
    )

    assert history == ("middle", "newest")
    assert sum(map(len, history)) <= 20


def test_bounded_history_truncates_oversized_latest_turn_and_rejects_bad_limits():
    assert bounded_conversation_history(
        ["older", "x" * 10],
        max_turns=5,
        max_chars=4,
    ) == ("xxxx",)
    with pytest.raises(ValueError, match="limits must be positive"):
        bounded_conversation_history(["turn"], max_turns=0, max_chars=10)
