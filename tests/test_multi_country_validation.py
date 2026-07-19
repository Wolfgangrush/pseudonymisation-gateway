"""Regression tests for the multi-country detector-precision fixes (v0.5).

Mirrors the India work for the other six jurisdictions:

- IBAN (UAE / UK / EU): mod-97 validated — random AE/GB/EU-prefixed runs rejected.
- Singapore NRIC / FIN: weighted check-letter validated — wrong-letter rejected.
- USA ITIN: group-number range validated.
- Currency amounts (AED / AUD / GBP / USD / EUR / SGD): negative + accounting forms.

Same privacy stance as India: validators add precision to the auto-redaction
detector; they do not weaken recall (the residue scanner still surfaces look-alike
digit runs for human review).
"""

import pytest

from pseudonymisation_gateway import PseudonymisationGateway
from pseudonymisation_gateway.patterns._checksums import (
    iban_validate,
    nric_validate,
    itin_validate,
)


# ── IBAN (mod-97) across UAE / UK / EU ────────────────────────────────────


@pytest.mark.parametrize(
    "jurisdiction,label,iban",
    [
        ("uae", "UAE_IBAN", "AE070331234567890123456"),
        ("uk", "UK_IBAN", "GB82WEST12345698765432"),
        ("eu", "EU_IBAN", "DE89370400440532013000"),
    ],
)
def test_valid_iban_redacted(jurisdiction, label, iban):
    gw = PseudonymisationGateway(jurisdictions=[jurisdiction])
    clean, _ = gw.sanitize(f"Transfer to {iban} today.")
    assert f"[{label}_1]" in clean


@pytest.mark.parametrize(
    "jurisdiction,iban",
    [
        ("uae", "AE070331234567890123450"),  # tampered check digit
        ("uk", "GB00WEST12345698765432"),  # wrong check digits
        ("eu", "DE89370400440532013001"),  # tampered last digit
    ],
)
def test_invalid_iban_not_redacted(jurisdiction, iban):
    gw = PseudonymisationGateway(jurisdictions=[jurisdiction])
    clean, _ = gw.sanitize(f"String {iban} is not an IBAN.")
    assert "_IBAN_" not in clean


def test_iban_validate_unit():
    assert iban_validate("GB29NWBK60161331926819") is True
    assert iban_validate("GB82 WEST 1234 5698 7654 32") is True  # spaced
    # Valid GB29NWBK... with its check digits tampered to 28 → fails mod-97.
    assert iban_validate("GB28NWBK60161331926819") is False


# ── Singapore NRIC / FIN (weighted check letter) ──────────────────────────


def test_valid_nric_fin_redacted():
    gw = PseudonymisationGateway(jurisdictions=["singapore"])
    clean, _ = gw.sanitize("Client S1234567D and worker F1234567N attended.")
    assert "[NRIC_1]" in clean
    assert "[FIN_1]" in clean


def test_wrong_check_letter_not_redacted():
    gw = PseudonymisationGateway(jurisdictions=["singapore"])
    # S1234567A has the wrong check letter (correct is 'D').
    clean, _ = gw.sanitize("Reference S1234567A is not an NRIC.")
    assert "[NRIC_" not in clean


def test_nric_validate_unit():
    assert nric_validate("S1234567D") is True
    assert nric_validate("T0123456G") is True
    assert nric_validate("F1234567N") is True
    assert nric_validate("G1234567X") is True
    assert nric_validate("S1234567A") is False
    assert nric_validate("F1234567B") is False
    # M-series (FIN from 2022) accepted on structure to avoid false negatives.
    assert nric_validate("M5009281N") is True


# ── USA ITIN (group-number range) ─────────────────────────────────────────


def test_valid_itin_redacted():
    gw = PseudonymisationGateway(jurisdictions=["usa"])
    clean, _ = gw.sanitize("ITIN 912-70-5678 on file.")
    assert "[ITIN_1]" in clean


def test_itin_invalid_group_not_redacted():
    gw = PseudonymisationGateway(jurisdictions=["usa"])
    # group '34' is outside the IRS-assigned ITIN ranges.
    clean, _ = gw.sanitize("Number 912-34-5678 is not an ITIN.")
    assert "[ITIN_" not in clean


def test_itin_validate_unit():
    assert itin_validate("912-70-5678") is True
    assert itin_validate("900-88-0000") is True
    assert itin_validate("999-99-9999") is True
    assert itin_validate("912-34-5678") is False  # group 34 invalid
    assert itin_validate("812-70-5678") is False  # does not start with 9


# ── Currency amounts — negative + accounting forms across all 6 ───────────


@pytest.mark.parametrize(
    "jurisdiction,label,amount",
    [
        ("uae", "AED_AMOUNT", "(AED 5,000)"),
        ("uae", "AED_AMOUNT", "-AED 5,000"),
        ("australia", "AUD_AMOUNT", "-A$5,000"),
        ("australia", "AUD_AMOUNT", "(A$5,000)"),
        ("uk", "GBP_AMOUNT", "-£5,000"),
        ("uk", "GBP_AMOUNT", "(£5,000)"),
        ("usa", "USD_AMOUNT", "-US$5,000"),
        ("usa", "USD_AMOUNT", "(USD 5,000)"),
        ("eu", "EUR_AMOUNT", "-€5.000"),
        ("eu", "EUR_AMOUNT", "(€5.000)"),
        ("singapore", "SGD_AMOUNT", "-S$5,000"),
        ("singapore", "SGD_AMOUNT", "(S$5,000)"),
    ],
)
def test_negative_and_accounting_amounts_redacted(jurisdiction, label, amount):
    gw = PseudonymisationGateway(jurisdictions=[jurisdiction])
    clean, _ = gw.sanitize(f"Net position {amount} this quarter.")
    assert f"[{label}_1]" in clean
