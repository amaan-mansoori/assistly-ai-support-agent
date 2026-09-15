"""Tests for empirical intent discovery module."""

import pytest
from src.intents.discover_intents import (
    clean_customer_text,
    detect_language,
    classify_response_action,
    CANDIDATE_ISSUE_RULES,
)


def test_clean_customer_text():
    """Verify customer text cleaning and noise detection."""
    # Usable inquiry
    text = "@AmazonHelp My order hasn't arrived yet and was supposed to be here yesterday."
    cleaned, is_usable = clean_customer_text(text)
    assert is_usable is True
    assert "@AmazonHelp" not in cleaned
    assert "order hasn't arrived" in cleaned

    # Very short noise
    noise_text = "@AmazonHelp ok"
    _, is_usable_noise = clean_customer_text(noise_text)
    assert is_usable_noise is False


def test_detect_language():
    """Verify local language detection across English, Spanish, Japanese."""
    en_sample = "Where is my delivery? It has not arrived."
    assert detect_language(en_sample) == "en"

    es_sample = "Hola, mi pedido no ha llegado y la entrega era para hoy gracias."
    assert detect_language(es_sample) == "es"

    ja_sample = "荷物が届きません。確認をお願いします。"
    assert detect_language(ja_sample) == "ja"


def test_classify_response_action():
    """Verify response action pattern categorization."""
    dm_reply = "Please send us a DM with your details so we can assist."
    assert classify_response_action(dm_reply) == "dm_redirect"

    tracking_reply = "You can track your package carrier status here: https://t.co/xyz"
    assert classify_response_action(tracking_reply) == "tracking_delivery_guidance"

    return_reply = "You can request a replacement or return label here: https://t.co/xyz"
    assert classify_response_action(return_reply) == "return_replacement_guidance"


def test_candidate_issue_rules():
    """Verify rule matchers correctly identify distinct issue areas."""
    late_query = "my package is delayed and running late"
    matched_delay = any(p.search(late_query) for p in CANDIDATE_ISSUE_RULES["delivery_delay"]["compiled"])
    assert matched_delay is True

    cancel_query = "please cancel my order immediately"
    matched_cancel = any(p.search(cancel_query) for p in CANDIDATE_ISSUE_RULES["order_cancellation_modification"]["compiled"])
    assert matched_cancel is True

    prime_query = "i was charged for amazon prime without my permission"
    matched_prime = any(p.search(prime_query) for p in CANDIDATE_ISSUE_RULES["prime_benefits_membership"]["compiled"])
    assert matched_prime is True
