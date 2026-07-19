"""Regression tests for the India detector-precision fixes.

Each test pins one deficiency reported against the v0.3 India patterns:

1. Aadhaar over-matched *any* 12-digit run (invoices, timestamps, barcodes,
   UPI references) — now Verhoeff + first-digit validated.
2. PAN accepted any 5 letters — now the 4th letter (holder-type code) is
   constrained.
3. GSTIN accepted any GSTIN-shaped string — now the base-36 check digit is
   verified.
4. Vehicle registration missed the Bharat (BH) series — now covered.
5. ₹ amounts missed negative and accounting (parenthesised) forms — now covered.

Detector precision must NOT weaken the privacy guarantee: a 12-digit run that
fails the Aadhaar checksum is still surfaced by the residue scanner for human
review (see the final test).
"""

import pytest

from pseudonymisation_gateway import PseudonymisationGateway
from pseudonymisation_gateway.patterns.india import (
    aadhaar_validate,
    gstin_validate,
)


# ── 1. Aadhaar — Verhoeff + first-digit validation ────────────────────────


def test_valid_aadhaar_is_redacted():
    gw = PseudonymisationGateway(jurisdictions=["india"])
    clean, _ = gw.sanitize("Aadhaar 9999 9999 0019 on record.")
    assert "[AADHAAR_1]" in clean
    assert "9999 9999 0019" not in clean


@pytest.mark.parametrize(
    "text",
    [
        "Invoice number 1234 5678 9012 dated today.",  # starts with 1
        "Order ref 100020003000 shipped.",  # fails Verhoeff
        "Timestamp 202606260112 logged.",  # fails Verhoeff
        "Barcode 890123456784 scanned.",  # fails Verhoeff
        "UPI txn 123456789012 settled.",  # starts with 1
    ],
)
def test_twelve_digit_lookalikes_not_redacted_as_aadhaar(text):
    """The exact false-positive classes reported: invoice/timestamp/barcode/UPI."""
    gw = PseudonymisationGateway(jurisdictions=["india"])
    clean, _ = gw.sanitize(text)
    assert "[AADHAAR_" not in clean


def test_aadhaar_validate_unit():
    assert aadhaar_validate("9999 9999 0019") is True
    assert aadhaar_validate("999999990019") is True
    assert aadhaar_validate("123456789012") is False  # starts with 1
    assert aadhaar_validate("999999990018") is False  # bad check digit
    assert aadhaar_validate("99999999001") is False  # 11 digits


# ── 2. PAN — holder-type (4th letter) validation ──────────────────────────


def test_valid_pan_is_redacted():
    gw = PseudonymisationGateway(jurisdictions=["india"])
    clean, _ = gw.sanitize("PAN ABFPK1234L on file.")
    assert "[PAN_1]" in clean


def test_pan_with_invalid_holder_type_not_redacted():
    """4th letter 'D' is not a valid PAN holder-type code."""
    gw = PseudonymisationGateway(jurisdictions=["india"])
    clean, _ = gw.sanitize("Reference ABCDE1234F is not a PAN.")
    assert "[PAN_" not in clean


# ── 3. GSTIN — checksum validation ────────────────────────────────────────


def test_valid_gstin_is_redacted():
    gw = PseudonymisationGateway(jurisdictions=["india"])
    clean, _ = gw.sanitize("GSTIN 27AAPFU0939F1ZV verified.")
    assert "[GSTIN_1]" in clean


def test_gstin_with_bad_checksum_not_redacted():
    gw = PseudonymisationGateway(jurisdictions=["india"])
    # 27AAPFU0939F1ZX is structurally a valid GSTIN shape (real state code,
    # valid embedded PAN) but the final check character is wrong (should be 'V').
    clean, _ = gw.sanitize("String 27AAPFU0939F1ZX is not a GSTIN.")
    assert "[GSTIN_" not in clean


def test_gstin_validate_unit():
    assert gstin_validate("27AAPFU0939F1ZV") is True
    assert gstin_validate("27AAPFU0939F1ZX") is False  # wrong check digit
    assert gstin_validate("00AAPFU0939F1ZV") is False  # invalid state code
    assert gstin_validate("27AAPFU0939F1ZV ") is True  # surrounding space tolerated


# ── 4. Vehicle registration — Bharat (BH) series ──────────────────────────


@pytest.mark.parametrize(
    "plate",
    ["22 BH 1234 AB", "21BH5678CD", "23-BH-4567-XY"],
)
def test_bh_series_plate_is_redacted(plate):
    gw = PseudonymisationGateway(jurisdictions=["india"])
    clean, _ = gw.sanitize(f"Vehicle {plate} registered.")
    assert "[INDIA_VEHICLE_1]" in clean
    assert plate not in clean


def test_state_series_plate_still_redacted():
    gw = PseudonymisationGateway(jurisdictions=["india"])
    clean, _ = gw.sanitize("Vehicle MH 12 AB 1234 seized.")
    assert "[INDIA_VEHICLE_1]" in clean


# ── 5. ₹ amounts — negative and accounting forms ──────────────────────────


@pytest.mark.parametrize(
    "amount",
    ["-₹5,000", "₹-5,000", "(₹5,000)", "Rs. -5,000", "(Rs 1,200.50)", "-Rs.750"],
)
def test_negative_and_accounting_amounts_redacted(amount):
    gw = PseudonymisationGateway(jurisdictions=["india"])
    clean, _ = gw.sanitize(f"Net position {amount} this quarter.")
    assert "[INR_AMOUNT_1]" in clean


def test_positive_amount_still_redacted():
    gw = PseudonymisationGateway(jurisdictions=["india"])
    clean, _ = gw.sanitize("Fee of ₹5,00,000 was paid.")
    assert "[INR_AMOUNT_1]" in clean


# ── Privacy guarantee preserved: residue net still surfaces look-alikes ────


def test_invalid_aadhaar_lookalike_still_surfaced_by_residue():
    """A 12-digit run the detector skipped is NOT silently sent — the residue
    scanner surfaces it for the practitioner (surface, never block)."""
    gw = PseudonymisationGateway(jurisdictions=["india"])
    text = "Invoice number 100020003000 dated today."
    clean, _ = gw.sanitize(text)
    assert "[AADHAAR_" not in clean  # detector did not false-redact
    report = gw.scan_residue(clean)
    assert any("aadhaar" in h.lower() for h in report.high)  # but it IS surfaced
