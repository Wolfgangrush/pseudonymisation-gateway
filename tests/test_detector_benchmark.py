"""Detector benchmark — the adversarial PII-detector stress test, formalised.

This is the reusable corpus behind the v0.4/v0.5 precision work: the same
two-sided audit a reviewer used to find the original defects, turned into a
permanent regression gate. For each jurisdiction and identifier it pins:

- ``must_redact``   — checksum-valid exemplars + every format variant.
                      A miss here = a real ID silently sent to the cloud (LEAK).
- ``must_not_redact`` — shaped-but-invalid look-alikes (invoice / timestamp /
                      barcode numbers, tampered checksums, wrong holder-type).
                      A hit here = a false positive that garbles the prompt.

All exemplars are synthetic or published test vectors (UIDAI test Aadhaar,
Wikipedia IBANs) — never a real identifier. Run it against any detector change:

    pytest tests/test_detector_benchmark.py -q
"""
import pytest

from pseudonymisation_gateway import PseudonymisationGateway


# (jurisdiction, must_redact[], must_not_redact[])
BENCHMARK = [
    (
        "india",
        [
            "Aadhaar 9999 9999 0019",      # UIDAI test Aadhaar (Verhoeff-valid)
            "PAN ABFPK1234L",              # 4th char 'P' (individual)
            "GSTIN 27AAPFU0939F1ZV",       # state 27, check digit 'V'
            "Vehicle 22 BH 1234 AB",       # Bharat (BH) series
            "Vehicle MH 12 AB 1234",       # state series
            "Owed -₹5,000",                # negative amount
            "Loss of (₹5,000)",            # accounting amount
        ],
        [
            "Invoice 1234 5678 9012",      # 12-digit, starts 1 (not Aadhaar)
            "Timestamp 202606260112",      # 12-digit, fails Verhoeff
            "Barcode 890123456784",        # 12-digit, fails Verhoeff
            "String 27ABCDE1234F1Z5",      # GSTIN-shaped, bad checksum + bad PAN
            "Ref ABCDE1234F here",         # PAN-shaped, 4th char 'D' invalid
        ],
    ),
    (
        "uae",
        ["Transfer AE070331234567890123456", "Loss (AED 5,000)", "-AED 5,000"],
        ["String AE070331234567890123450"],   # tampered IBAN check
    ),
    (
        "uk",
        ["IBAN GB82WEST12345698765432", "Owed -£5,000", "Loss (£5,000)"],
        ["String GB28NWBK60161331926819"],     # tampered IBAN check
    ),
    (
        "eu",
        ["Wire DE89370400440532013000", "Loss (€5.000)", "-€5.000"],
        ["String DE89370400440532013001"],     # tampered IBAN check
    ),
    (
        "singapore",
        ["NRIC S1234567D", "FIN F1234567N", "Fee -S$5,000", "Loss (S$5,000)"],
        ["Ref S1234567A here"],                 # wrong NRIC check letter
    ),
    (
        "usa",
        ["ITIN 912-70-5678", "SSN 123-45-6789", "Refund (USD 5,000)", "-US$5,000"],
        ["Number 912-34-5678 here"],            # ITIN group out of range
    ),
    (
        "australia",
        ["Loss (A$5,000)", "-A$5,000"],
        [],                                     # AU IDs are keyword-gated by design
    ),
]


def _params(kind):
    out = []
    for juris, redact, not_redact in BENCHMARK:
        items = redact if kind == "redact" else not_redact
        for text in items:
            out.append(pytest.param(juris, text, id=f"{juris}:{text[:30]}"))
    return out


@pytest.mark.parametrize("juris,text", _params("redact"))
def test_must_redact(juris, text):
    """RECALL: every valid exemplar / variant must be tokenised (no leak)."""
    gw = PseudonymisationGateway(jurisdictions=[juris])
    clean, tm = gw.sanitize(text)
    assert clean != text and tm.forward, (
        f"LEAK: detector failed to redact {text!r} in {juris}"
    )


@pytest.mark.parametrize("juris,text", _params("not_redact"))
def test_must_not_redact(juris, text):
    """PRECISION: shaped-but-invalid look-alikes must survive verbatim."""
    gw = PseudonymisationGateway(jurisdictions=[juris])
    clean, _ = gw.sanitize(text)
    assert clean == text, (
        f"FALSE POSITIVE: detector redacted look-alike {text!r} in {juris} -> {clean!r}"
    )
