from src.data.conversation_provenance_audit import is_valid_direct_pair, parent_chain


def row(tweet_id, author_id, inbound, parent=""):
    return {
        "tweet_id": tweet_id,
        "author_id": author_id,
        "inbound": inbound,
        "in_response_to_tweet_id": parent,
        "text": tweet_id,
    }


def test_direct_pair_requires_exact_parent_and_directions():
    customer = row("c1", "customer-1", "True")
    response = row("a1", "AmazonHelp", "False", "c1")
    assert is_valid_direct_pair(customer, response)
    assert not is_valid_direct_pair(customer, row("a1", "AmazonHelp", "False", "other"))
    assert not is_valid_direct_pair(row("c1", "customer-1", "False"), response)
    assert not is_valid_direct_pair(customer, row("a1", "other-brand", "False", "c1"))


def test_parent_chain_follows_ids_not_dictionary_order_or_adjacency():
    records = {
        "child": row("child", "customer-1", "True", "parent"),
        "noise": row("noise", "other", "True"),
        "root": row("root", "customer-1", "True"),
        "parent": row("parent", "AmazonHelp", "False", "root"),
    }
    assert [r["tweet_id"] for r in parent_chain("child", records)] == ["root", "parent", "child"]


def test_parent_chain_stops_at_missing_parent():
    records = {"child": row("child", "customer-1", "True", "missing")}
    assert [r["tweet_id"] for r in parent_chain("child", records)] == ["child"]
