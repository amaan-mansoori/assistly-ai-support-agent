"""Tests for taxonomy refinement module."""

import pytest
from src.intents.refine_taxonomy import (
    is_dialogue_artifact,
    PROPOSED_TAXONOMY,
)


def test_is_dialogue_artifact():
    """Verify dialogue artifacts are identified."""
    assert is_dialogue_artifact("@AmazonHelp sent you a DM with details") is True
    assert is_dialogue_artifact("@AmazonHelp done, check DM") is True
    assert is_dialogue_artifact("@AmazonHelp thank you so much!") is True
    assert is_dialogue_artifact("@AmazonHelp order id: 123-4567890-1234567") is True

    # Initial problem statements should NOT be dialogue artifacts
    assert is_dialogue_artifact("@AmazonHelp My order was supposed to arrive yesterday and is still delayed") is False
    assert is_dialogue_artifact("@AmazonHelp The package arrived completely damaged and broken") is False


def test_proposed_taxonomy_patterns():
    """Verify proposed taxonomy regex matches target problem areas."""
    # 1. Delivery delay
    assert any(p.search("my order is late and taking so long to arrive") for p in PROPOSED_TAXONOMY["order_delivery_delay"]["compiled"]) is True

    # 2. Marked delivered missing
    assert any(p.search("tracking says delivered but not in mailbox or porch") for p in PROPOSED_TAXONOMY["delivery_marked_delivered_missing"]["compiled"]) is True

    # 3. Damaged / wrong item
    assert any(p.search("the screen is shattered and completely defective") for p in PROPOSED_TAXONOMY["damaged_wrong_defective_item"]["compiled"]) is True
    assert any(p.search("you sent me the wrong item entirely") for p in PROPOSED_TAXONOMY["damaged_wrong_defective_item"]["compiled"]) is True

    # 4. Return & refund
    assert any(p.search("where is my refund for the return package") for p in PROPOSED_TAXONOMY["return_and_refund_status"]["compiled"]) is True

    # 5. Order cancellation
    assert any(p.search("please cancel my order before it ships") for p in PROPOSED_TAXONOMY["order_cancellation_modification"]["compiled"]) is True

    # 6. Prime membership
    assert any(p.search("why was i charged for prime membership fee") for p in PROPOSED_TAXONOMY["prime_membership_billing"]["compiled"]) is True

    # 7. Account access
    assert any(p.search("my account is locked out and reset password not working") for p in PROPOSED_TAXONOMY["account_access_security"]["compiled"]) is True

    # 8. Payment dispute
    assert any(p.search("my credit card was charged twice for the same order") for p in PROPOSED_TAXONOMY["payment_charge_dispute"]["compiled"]) is True

    # 9. Product stock
    assert any(p.search("when will this item be back in stock") for p in PROPOSED_TAXONOMY["product_stock_inquiry"]["compiled"]) is True

    # 10. Third-party seller
    assert any(p.search("the third party seller refused to reply to my message") for p in PROPOSED_TAXONOMY["third_party_seller_marketplace"]["compiled"]) is True
