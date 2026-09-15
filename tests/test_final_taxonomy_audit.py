"""Focused safety checks for the local final-taxonomy audit rules."""

from src.intents.final_taxonomy_audit import classify_intent, message_type


def test_delivered_missing_beats_generic_delivery_delay():
    text = "Tracking says my package was delivered yesterday but I have not received it."
    assert classify_intent(text) == "delivery_marked_delivered_missing"


def test_delivery_delay_without_delivery_confirmation_stays_delay():
    assert classify_intent("My order is late and has not arrived yet") == "delivery_status_delay"


def test_acknowledgement_is_message_type_not_customer_intent():
    assert message_type("@AmazonHelp thank you, I will try that") == "acknowledgement"
    assert classify_intent("@AmazonHelp thank you, I will try that") == "other_unclear"
