from support_classifier.config import ROUTING_GROUPS, SUPPORTED_INTENTS


def test_every_supported_intent_has_a_route():
    assert set(SUPPORTED_INTENTS) == set(ROUTING_GROUPS)

