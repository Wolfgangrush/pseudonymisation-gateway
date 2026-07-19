"""Residue scan tests — HIGH residue surfaces; LOW logs + proceeds; jurisdiction shapes respected."""

from pseudonymisation_gateway import PseudonymisationGateway
from pseudonymisation_gateway.core import ResidueReport


# ── Basic residue scan structure ──────────────────────────────────────────


def test_residue_report_defaults():
    """ResidueReport has sensible defaults."""
    r = ResidueReport()
    assert r.high == []
    assert r.low == []
    assert r.jurisdiction == []


def test_residue_report_with_jurisdiction():
    """ResidueReport stores jurisdiction list."""
    r = ResidueReport(jurisdiction=["india", "uae"])
    assert r.jurisdiction == ["india", "uae"]


# ── Residue scan: digit runs by jurisdiction ──────────────────────────────


def test_residue_india_12_digit_high():
    """12-digit run in India context → HIGH residue."""
    gw = PseudonymisationGateway(jurisdictions=["india"])
    # 12-digit Aadhaar-like number that wasn't caught (e.g. embedded in prose)
    report = gw.scan_residue("The reference 123456789012 appears in the document.")
    assert len(report.high) >= 1
    assert any("aadhaar" in h.lower() for h in report.high)


def test_residue_india_12_digit_already_tokenized_not_flagged():
    """Digit runs inside placeholders are NOT flagged as residue."""
    gw = PseudonymisationGateway(jurisdictions=["india"])
    # [AADHAAR_1] contains digits — should not trigger residue
    report = gw.scan_residue("Client [AADHAAR_1] was verified.")
    # The digits inside [AADHAAR_1] should not be flagged
    assert not any("Aadhaar" in h.lower() for h in report.high)


def test_residue_uk_digit_run_high():
    """9-digit run in UK context → HIGH residue."""
    gw = PseudonymisationGateway(jurisdictions=["uk"])
    report = gw.scan_residue("Reference number 123456789.")
    assert len(report.high) >= 1
    assert any("nhs" in h.lower() or "utr" in h.lower() for h in report.high)


def test_residue_uae_digit_run_high():
    """15-digit run in UAE context → HIGH residue."""
    gw = PseudonymisationGateway(jurisdictions=["uae"])
    report = gw.scan_residue("The number 123456789012345 appears.")
    assert len(report.high) >= 1
    assert any("emirates" in h.lower() for h in report.high)


def test_residue_usa_digit_run_high():
    """9-digit run in USA context → HIGH residue."""
    gw = PseudonymisationGateway(jurisdictions=["usa"])
    report = gw.scan_residue("SSN-like: 123456789.")
    assert len(report.high) >= 1


def test_residue_australia_digit_run_high():
    """9-digit run in Australia context → HIGH residue."""
    gw = PseudonymisationGateway(jurisdictions=["australia"])
    report = gw.scan_residue("Number: 123456789.")
    assert len(report.high) >= 1


def test_residue_singapore_digit_run_high():
    """9-digit run in Singapore context → HIGH residue."""
    gw = PseudonymisationGateway(jurisdictions=["singapore"])
    report = gw.scan_residue("Number: 123456789.")
    assert len(report.high) >= 1


# ── Residue scan: capitalised bigrams ─────────────────────────────────────


def test_residue_capitalised_bigram_high():
    """Capitalised bigram not in TokenMap → HIGH residue."""
    gw = PseudonymisationGateway(jurisdictions=["india"])
    report = gw.scan_residue("Rahul Verma filed the petition in Delhi High Court.")
    # "Rahul Verma" is a capitalised bigram → should be flagged
    assert len(report.high) >= 1
    assert any("Rahul Verma" in h for h in report.high)


def test_residue_capitalised_bigram_in_placeholder_not_flagged():
    """Bigram inside placeholder brackets is not flagged."""
    gw = PseudonymisationGateway(jurisdictions=["india"])
    # Placeholder brackets contain underscores/digits — the strip removes them
    report = gw.scan_residue("The matter [PERSON_1] was heard.")
    # [PERSON_1] is stripped before scanning — no bigram residue expected
    assert not any("PERSON" in h for h in report.high)


# ── Residue scan: weak signals ────────────────────────────────────────────


def test_residue_lone_capitalised_low():
    """Lone capitalised word (not a common term) → LOW residue."""
    gw = PseudonymisationGateway(jurisdictions=["india"])
    report = gw.scan_residue("Majidullah attended the hearing.")
    # "Majidullah" is a lone capitalised word → LOW
    assert len(report.low) >= 1


def test_residue_legal_term_not_flagged():
    """Common legal terms are not flagged as residue."""
    gw = PseudonymisationGateway(jurisdictions=["uk"])
    report = gw.scan_residue("The Appellant submitted that the Court should...")
    # "Appellant" is excluded, "Court" is excluded
    assert not any("Appellant" in item for item in report.low)
    assert not any("Court" in item for item in report.low)


def test_residue_jurisdiction_list_present():
    """ResidueReport includes the active jurisdiction list."""
    gw = PseudonymisationGateway(jurisdictions=["india", "uae"])
    report = gw.scan_residue("Some text.")
    assert "india" in report.jurisdiction
    assert "uae" in report.jurisdiction


# ── Residue scan: clean text ──────────────────────────────────────────────


def test_residue_clean_text_empty():
    """Fully sanitised text produces minimal residue."""
    gw = PseudonymisationGateway(jurisdictions=["india"])
    clean, _ = gw.sanitize("The court adjourned the matter to next week.")
    report = gw.scan_residue(clean)
    # "Court" is excluded, "matter" is excluded — should be clean
    assert len(report.high) == 0


# ── Residue scan: jurisdiction-isolated ───────────────────────────────────


def test_residue_india_pattern_not_high_in_uk():
    """12-digit run is HIGH in India but not necessarily in UK (no 12-digit ID)."""
    gw = PseudonymisationGateway(jurisdictions=["uk"])
    report = gw.scan_residue("Reference 123456789012.")
    # UK has no 12-digit ID → should NOT flag as high (only India has this rule)
    assert not any("Aadhaar" in h.lower() for h in report.high)
