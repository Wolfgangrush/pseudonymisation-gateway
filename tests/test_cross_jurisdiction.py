"""Cross-jurisdiction diaspora-coverage tests.

The 6 non-India country firms layer Indian PII detection alongside their
country-native patterns because the diaspora is real: Dubai (~3.4M Indians),
Australia (~1M), UK (~1.9M), USA (~5.4M), EU (~2M), Singapore (~9.2% pop).

A Dubai lawyer handling an Indian-expat client matter benefits from both
Emirates ID AND Aadhaar detection in the same gateway.
"""

from pseudonymisation_gateway import PseudonymisationGateway


def test_dubai_lawyer_handling_indian_client():
    """Dubai firm gateway loads UAE + India patterns. Both fire."""
    gw = PseudonymisationGateway(jurisdictions=["uae", "india"])
    text = (
        "Client Mr. Khalid Al-Mansoori (Emirates ID 784-1985-1234567-8) is filing "
        "on behalf of business partner Mr. Rahul Sharma (Aadhaar 9999 9999 0019, "
        "PAN ABFPK1234L)."
    )
    clean, tm = gw.sanitize(text)
    assert "[EMIRATES_ID_1]" in clean
    assert "[AADHAAR_1]" in clean
    assert "[PAN_1]" in clean
    assert "Al-Mansoori" not in clean
    assert "Rahul" not in clean


def test_uk_lawyer_handling_indian_client():
    """UK firm gateway loads UK + India patterns."""
    gw = PseudonymisationGateway(jurisdictions=["uk", "india"])
    clean, _ = gw.sanitize(
        "Client AB123456C and partner Aadhaar 9999 9999 0019 both on file."
    )
    assert "[NI_NUMBER_1]" in clean
    assert "[AADHAAR_1]" in clean


def test_australia_lawyer_handling_indian_client():
    """Australia firm gateway loads AU + India patterns."""
    gw = PseudonymisationGateway(jurisdictions=["australia", "india"])
    clean, _ = gw.sanitize(
        "TFN: 123 456 789 for client, Aadhaar 9999 9999 0019 for spouse."
    )
    assert "[TFN_1]" in clean
    assert "[AADHAAR_1]" in clean


def test_usa_lawyer_handling_indian_client():
    """USA firm gateway loads USA + India patterns."""
    gw = PseudonymisationGateway(jurisdictions=["usa", "india"])
    clean, _ = gw.sanitize(
        "Client SSN 123-45-6789, Indian-passport spouse PAN ABFPK1234L."
    )
    assert "[SSN_1]" in clean
    assert "[PAN_1]" in clean


def test_priority_uae_first_over_indian_pattern():
    """When both UAE and India patterns match the same text, UAE fires first
    (jurisdiction-priority intentional)."""
    # Emirates ID 784-1985-1234567-8 should match EMIRATES_ID before any
    # Indian pattern can claim digits
    gw = PseudonymisationGateway(jurisdictions=["uae", "india"])
    clean, _ = gw.sanitize("ID 784-1985-1234567-8.")
    assert "[EMIRATES_ID_1]" in clean
    # Aadhaar shouldn't fire on the same string
    assert "[AADHAAR_" not in clean


def test_round_trip_with_diaspora():
    """End-to-end: sanitize → cloud response → desanitize restores both layers."""
    gw = PseudonymisationGateway(jurisdictions=["uae", "india"])
    original = (
        "Mr. Khalid Al-Mansoori (Emirates ID 784-1985-1234567-8) and partner "
        "Mr. Rahul Sharma (Aadhaar 9999 9999 0019) entered the agreement."
    )
    clean, tm = gw.sanitize(original)
    # simulate cloud LLM response (placeholders preserved)
    response = clean + " The contract is enforceable under DIFC law."
    restored = gw.desanitize(response, tm)
    assert "Khalid Al-Mansoori" in restored
    assert "784-1985-1234567-8" in restored
    assert "9999 9999 0019" in restored
    assert "Rahul Sharma" in restored
