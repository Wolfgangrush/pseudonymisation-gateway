"""NER-optional tests — spaCy absent → warning, pipeline still runs; release gate passes WITHOUT spaCy."""
import pytest

from pseudonymisation_gateway.ner import NERSanitiser
from pseudonymisation_gateway import PseudonymisationGateway


# ── NER unavailable (spaCy not installed) ─────────────────────────────────

def test_ner_sanitiser_available_false_without_spacy():
    """When spaCy is not installed, NERSanitiser.available is False."""
    ner = NERSanitiser()
    assert ner.available is False


def test_ner_extract_entities_empty_without_spacy():
    """When spaCy is not installed, extract_entities returns []."""
    ner = NERSanitiser()
    result = ner.extract_entities("Rahul Verma filed the petition.")
    assert result == []


# ── Gateway with enable_ner=True (spaCy absent) ───────────────────────────

def test_gateway_enable_ner_no_spacy_does_not_block():
    """Gateway with enable_ner=True still works when spaCy is absent."""
    gw = PseudonymisationGateway(
        jurisdictions=["india"],
        enable_ner=True,
    )
    # Should not raise — NER is optional
    clean, tm = gw.sanitize("Rahul Verma filed the petition.")
    assert isinstance(clean, str)
    assert len(clean) > 0


def test_gateway_enable_ner_no_spacy_sanitize_still_works():
    """sanitize() still catches regex PII even when NER is unavailable."""
    gw = PseudonymisationGateway(
        jurisdictions=["india"],
        enable_ner=True,
    )
    clean, tm = gw.sanitize("Mr. Rahul Sharma (Aadhaar 1234 5678 9012) filed.")
    assert "[PERSON_" in clean
    assert "[AADHAAR_" in clean
    assert "1234 5678 9012" not in clean


# ── Pipeline runs WITHOUT spaCy (release-gate test) ────────────────────────

def test_full_pipeline_without_spacy():
    """Full sanitize → desanitize round-trip works without spaCy."""
    gw = PseudonymisationGateway(
        jurisdictions=["india", "uae"],
        enable_ner=True,  # NER is enabled but spaCy is absent
    )
    original = (
        "Mr. Rahul Sharma (Aadhaar 1234 5678 9012, PAN ABCDE1234F) and "
        "Mr. Khalid Al-Mansoori (Emirates ID 784-1985-1234567-8) signed."
    )
    clean, tm = gw.sanitize(original)
    response = clean + " The agreement is valid."
    restored = gw.desanitize(response, tm)
    assert "Rahul Sharma" in restored
    assert "1234 5678 9012" in restored
    assert "ABCDE1234F" in restored
    assert "Khalid Al-Mansoori" in restored
    assert "784-1985-1234567-8" in restored


def test_residue_scan_works_without_spacy():
    """scan_residue() works when enable_ner=True but spaCy absent."""
    gw = PseudonymisationGateway(
        jurisdictions=["india"],
        enable_ner=True,
    )
    clean, _ = gw.sanitize("Some text.")
    report = gw.scan_residue(clean)
    assert isinstance(report.high, list)
    assert isinstance(report.low, list)


def test_audit_log_works_without_spacy():
    """Audit logging works when enable_ner=True but spaCy absent."""
    import tempfile
    from pathlib import Path

    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    gw = PseudonymisationGateway(
        jurisdictions=["india"],
        enable_ner=True,
        audit_log_path=tmp.name,
    )
    gw.sanitize("Some text.", matter_id="M-NER")
    with open(tmp.name, "r") as fh:
        raw = fh.read()
    assert "matter_id" in raw
    Path(tmp.name).unlink()
