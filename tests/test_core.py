"""Core engine tests — TokenMap, sanitize/desanitize round-trip, register_pattern."""

import re
from pseudonymisation_gateway import PseudonymisationGateway, TokenMap


def test_token_map_deterministic():
    tm = TokenMap()
    p1 = tm.add("John Smith", "PERSON")
    p2 = tm.add("John Smith", "PERSON")
    assert p1 == p2 == "[PERSON_1]"


def test_token_map_counters_per_type():
    tm = TokenMap()
    a = tm.add("John", "PERSON")
    b = tm.add("AB123456C", "NI_NUMBER")
    c = tm.add("Jane", "PERSON")
    assert a == "[PERSON_1]"
    assert b == "[NI_NUMBER_1]"
    assert c == "[PERSON_2]"


def test_gateway_no_patterns_no_changes():
    gw = PseudonymisationGateway(jurisdictions=[], include_shared=False)
    text = "Mr. John Smith filed."
    clean, tm = gw.sanitize(text)
    assert clean == text
    assert len(tm.forward) == 0


def test_gateway_shared_patterns_only():
    gw = PseudonymisationGateway(jurisdictions=[], include_shared=True)
    clean, tm = gw.sanitize("Mr. John Smith filed at john@example.com")
    assert "[PERSON_1]" in clean
    assert "[EMAIL_1]" in clean
    assert "john@example.com" not in clean


def test_gateway_with_uk_jurisdiction():
    gw = PseudonymisationGateway(jurisdictions=["uk"])
    clean, tm = gw.sanitize("Client AB123456C lives in London.")
    assert "AB123456C" not in clean
    assert "[NI_NUMBER_1]" in clean


def test_register_pattern_runtime():
    gw = PseudonymisationGateway(jurisdictions=[])
    gw.register_pattern(re.compile(r"MATTER-\d{4}"), "MATTER_ID")
    clean, tm = gw.sanitize("Re: MATTER-4012 hearing scheduled.")
    assert "[MATTER_ID_1]" in clean
    assert "MATTER-4012" not in clean


def test_desanitize_round_trip():
    gw = PseudonymisationGateway(jurisdictions=["uae", "india"])
    original = "Mr. Khalid Al-Mansoori filed Emirates ID 784-1985-1234567-8."
    clean, tm = gw.sanitize(original)
    # cloud response keeps placeholders unchanged
    response = clean + " Court accepted the filing."
    restored = gw.desanitize(response, tm)
    assert "Khalid" in restored
    assert "784-1985-1234567-8" in restored
    assert "[EMIRATES_ID_1]" not in restored


def test_is_safe_for_cloud_detects_pii():
    gw = PseudonymisationGateway(jurisdictions=["uk"])
    safe, detected = gw.is_safe_for_cloud("AB123456C is on file.")
    assert not safe
    assert "NI_NUMBER" in detected


def test_is_safe_for_cloud_clean_text():
    gw = PseudonymisationGateway(jurisdictions=["uk"])
    safe, detected = gw.is_safe_for_cloud("The court ruled in favor.")
    assert safe
    assert detected == []
