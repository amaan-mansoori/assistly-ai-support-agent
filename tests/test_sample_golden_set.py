from src.evaluation.sample_golden_set import chain, clean_key
from src.evaluation.create_final_worksheet import non_english_flags
from src.evaluation.propose_golden_labels import proposed_label


def test_clean_key_removes_nonsemantic_handles_and_urls():
    assert clean_key("@AmazonHelp My order is late https://t.co/x") == "my order is late"


def test_chain_uses_parent_ids_and_roles():
    records = {
        "root": {"tweet_id": "root", "author_id": "u", "inbound": "True", "in_response_to_tweet_id": "", "text": "root"},
        "agent": {"tweet_id": "agent", "author_id": "AmazonHelp", "inbound": "False", "in_response_to_tweet_id": "root", "text": "help"},
        "child": {"tweet_id": "child", "author_id": "u", "inbound": "True", "in_response_to_tweet_id": "agent", "text": "more"},
        "noise": {"tweet_id": "noise", "author_id": "other", "inbound": "True", "in_response_to_tweet_id": "", "text": "noise"},
    }
    assert [t["tweet_id"] for t in chain("child", records)] == ["root", "agent"]
    assert chain("child", records)[1]["role"] == "AmazonHelp"


def test_non_english_screen_is_local_and_non_destructive():
    assert non_english_flags("Hola gracias para pedido") == ["non-English marker tokens"]
    assert non_english_flags("My order is late") == []


def test_proposed_label_uses_other_unclear_for_ambiguous_short_text():
    assert proposed_label({
        "customer_text": "????",
        "conversation_context": "",
    }) == "other_unclear"
