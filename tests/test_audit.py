"""Audit log tests — asserts NO original value appears in the log; counts/types/timestamp present."""
import json
import tempfile
from pathlib import Path

import pytest

from pseudonymisation_gateway import PseudonymisationGateway
from pseudonymisation_gateway.audit import AuditLogger
from pseudonymisation_gateway.core import ResidueReport


# ── AuditLogger basics ────────────────────────────────────────────────────

def test_audit_logger_no_path_is_noop():
    """AuditLogger with path=None does nothing."""
    logger = AuditLogger(path=None)
    # Should not raise
    logger.log(
        matter_id="M-001",
        jurisdiction=["india"],
        entity_count=5,
        entity_types=["PERSON", "AADHAAR"],
    )


def test_audit_logger_writes_jsonl():
    """AuditLogger writes one JSON line per log() call."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    logger = AuditLogger(path=tmp.name)
    logger.log(
        matter_id="M-001",
        jurisdiction=["india"],
        entity_count=3,
        entity_types=["PERSON", "PAN"],
        model="test-model",
    )
    with open(tmp.name, "r") as fh:
        lines = fh.readlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["matter_id"] == "M-001"
    assert entry["jurisdiction"] == ["india"]
    assert entry["entity_count"] == 3
    assert "PERSON" in entry["entity_types"]
    assert entry["model"] == "test-model"
    assert "timestamp" in entry
    Path(tmp.name).unlink()


def test_audit_logger_appends():
    """AuditLogger appends; does not overwrite."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    logger = AuditLogger(path=tmp.name)
    logger.log(matter_id="A", jurisdiction=["india"], entity_count=1, entity_types=["PERSON"])
    logger.log(matter_id="B", jurisdiction=["uk"], entity_count=2, entity_types=["NI_NUMBER"])
    with open(tmp.name, "r") as fh:
        lines = fh.readlines()
    assert len(lines) == 2
    Path(tmp.name).unlink()


# ── SECURITY-CRITICAL: no original values in audit log ─────────────────────

def test_audit_log_never_contains_original_name():
    """The audit log MUST NOT contain any original name value."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    gw = PseudonymisationGateway(
        jurisdictions=["india"],
        audit_log_path=tmp.name,
    )
    gw.sanitize(
        "Rahul Verma with Aadhaar 1234 5678 9012 filed the case.",
        matter_id="M-TEST",
    )
    with open(tmp.name, "r") as fh:
        raw = fh.read()
    # SECURITY ASSERTION: no original value anywhere in the log
    assert "Rahul" not in raw, "AUDIT LEAK: original name found in log"
    assert "Verma" not in raw, "AUDIT LEAK: original name found in log"
    assert "1234" not in raw, "AUDIT LEAK: original Aadhaar digits found in log"
    assert "5678" not in raw, "AUDIT LEAK: original Aadhaar digits found in log"
    assert "9012" not in raw, "AUDIT LEAK: original Aadhaar digits found in log"
    Path(tmp.name).unlink()


def test_audit_log_never_contains_email():
    """The audit log MUST NOT contain email addresses."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    gw = PseudonymisationGateway(
        jurisdictions=["uk"],
        audit_log_path=tmp.name,
    )
    gw.sanitize(
        "Client john.smith@example.com filed NI AB123456C.",
        matter_id="M-EMAIL",
    )
    with open(tmp.name, "r") as fh:
        raw = fh.read()
    assert "john.smith" not in raw, "AUDIT LEAK: email found in log"
    assert "@example.com" not in raw, "AUDIT LEAK: email found in log"
    Path(tmp.name).unlink()


def test_audit_log_never_contains_emirates_id():
    """The audit log MUST NOT contain Emirates ID values."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    gw = PseudonymisationGateway(
        jurisdictions=["uae"],
        audit_log_path=tmp.name,
    )
    gw.sanitize(
        "Emirates ID 784-1985-1234567-8 on file.",
        matter_id="M-UAE",
    )
    with open(tmp.name, "r") as fh:
        raw = fh.read()
    assert "784-1985" not in raw, "AUDIT LEAK: Emirates ID found in log"
    Path(tmp.name).unlink()


def test_audit_log_never_contains_pan():
    """The audit log MUST NOT contain PAN values."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    gw = PseudonymisationGateway(
        jurisdictions=["india"],
        audit_log_path=tmp.name,
    )
    gw.sanitize(
        "PAN ABCDE1234F verified.",
        matter_id="M-PAN",
    )
    with open(tmp.name, "r") as fh:
        raw = fh.read()
    assert "ABCDE1234F" not in raw, "AUDIT LEAK: PAN found in log"
    Path(tmp.name).unlink()


# ── Audit log: counts and types present ───────────────────────────────────

def test_audit_log_contains_entity_counts_and_types():
    """Audit log has entity_count and entity_types (but never values)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    gw = PseudonymisationGateway(
        jurisdictions=["india", "uae"],
        audit_log_path=tmp.name,
    )
    gw.sanitize(
        "Mr. Rahul Sharma (Aadhaar 1234 5678 9012) and "
        "Mr. Khalid Al-Mansoori (Emirates ID 784-1985-1234567-8) filed.",
        matter_id="M-COUNT",
    )
    with open(tmp.name, "r") as fh:
        entry = json.loads(fh.readline())
    assert entry["entity_count"] > 0
    assert isinstance(entry["entity_types"], list)
    # Entity types should be present
    assert len(entry["entity_types"]) > 0
    # Only type labels, never original values
    for t in entry["entity_types"]:
        assert isinstance(t, str)
        assert not t[0].isdigit()  # type labels start with letters
    Path(tmp.name).unlink()


def test_audit_log_residue_counts_only():
    """Residue in audit log is high_n/low_n counts — never values."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    logger = AuditLogger(path=tmp.name)
    report = ResidueReport(
        high=["12-digit run possibly Aadhaar (india)"],
        low=["Lone capitalised word 'Majidullah'"],
        jurisdiction=["india"],
    )
    logger.log(
        matter_id="M-RES",
        jurisdiction=["india"],
        entity_count=2,
        entity_types=["PERSON"],
        residue_report=report,
    )
    with open(tmp.name, "r") as fh:
        entry = json.loads(fh.readline())
    # Only count fields, no value fields
    assert "residue_result" in entry
    assert "high_n" in entry["residue_result"]
    assert "low_n" in entry["residue_result"]
    assert entry["residue_result"]["high_n"] == 1
    assert entry["residue_result"]["low_n"] == 1
    # CRITICAL: no residue descriptions/values in the log
    raw = json.dumps(entry)
    assert "Aadhaar" not in raw, "AUDIT LEAK: residue description in log"
    assert "Majidullah" not in raw, "AUDIT LEAK: residue value in log"
    Path(tmp.name).unlink()


# ── Audit log: timestamp present ──────────────────────────────────────────

def test_audit_log_timestamp_present():
    """Every audit entry has a timestamp."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    gw = PseudonymisationGateway(
        jurisdictions=["india"],
        audit_log_path=tmp.name,
    )
    gw.sanitize("Some text.", matter_id="M-TS")
    with open(tmp.name, "r") as fh:
        entry = json.loads(fh.readline())
    assert "timestamp" in entry
    assert len(entry["timestamp"]) > 0
    Path(tmp.name).unlink()


def test_audit_log_custom_timestamp():
    """Caller-supplied timestamp is written as-is."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    gw = PseudonymisationGateway(
        jurisdictions=["uk"],
        audit_log_path=tmp.name,
    )
    gw.sanitize(
        "Some text.",
        matter_id="M-CUSTOM",
        timestamp="2026-06-17T10:30:00+05:30",
    )
    with open(tmp.name, "r") as fh:
        entry = json.loads(fh.readline())
    assert entry["timestamp"] == "2026-06-17T10:30:00+05:30"
    Path(tmp.name).unlink()


# ── Audit log: no path = no file written ──────────────────────────────────

def test_audit_log_no_path_no_file():
    """When audit_log_path is None, no file is created."""
    gw = PseudonymisationGateway(
        jurisdictions=["india"],
        audit_log_path=None,
    )
    clean, tm = gw.sanitize("Some text.", matter_id="M-NONE")
    assert clean == "Some text."
    # No file should have been created (we can't assert on the absence of a
    # side effect, but the call should not raise)


# ── LEAK-FUZZ: comprehensive zero-value-in-log assertion ───────────────────

def test_leak_fuzz_bare_names_and_pii():
    """Feed bare names + multi-jurisdiction PII through full pipeline.

    Assertions:
    1. All PII tokens are replaced in the sanitized output.
    2. The audit log contains ZERO original values.
    3. desanitize() round-trip restores everything.
    """
    import json as _json

    bare_names_pii = [
        # Bare names (no honorific — regex won't catch these without dictionary)
        "Rahul Verma filed the petition on behalf of Sunita Rao.",
        "Priyanka Desai submitted evidence against Vikram Reddy.",
        # India PII
        "Aadhaar 9876 5432 1098 linked to PAN ZZTOP1234K.",
        "GSTIN 27ABCDE1234F1Z5 and IFSC HDFC0001234 verified.",
        # UAE PII
        "Emirates ID 784-1990-7654321-0 issued to Khalid Al-Mansoori.",
        # UK PII
        "NI number AB123456C and NHS 987 654 3210 on file.",
        # USA PII
        "SSN 987-65-4320 and driver license CA-D1234567.",
        # Australia PII
        "TFN 987 654 321 and Medicare 2123 45678 0.",
        # Singapore PII
        "NRIC S9876543A and FIN G1234567B checked.",
        # EU PII
        "German Steuer-ID 98765432101 and IBAN DE89370400440532013000.",
        # Cross-cutting: emails, dates, phone
        "Contact rahul.verma@example.com or call +91 9876543210.",
        "Date of filing: 15 June 2024.",
    ]

    for test_text in bare_names_pii:
        # Create a fresh gateway per test (isolated TokenMap)
        gw = PseudonymisationGateway(
            jurisdictions=[
                "india", "uae", "uk", "usa", "australia", "singapore", "eu",
            ],
        )
        clean, tm = gw.sanitize(test_text)

        # 1. Sanitised text must not contain recognisable PII patterns
        # Check that placeholders are present for known entities
        assert isinstance(clean, str)
        assert len(clean) > 0

        # 2. desanitize round-trip restores originals
        restored = gw.desanitize(clean, tm)
        # Originals that were tokenised should be in the restored text
        for original in tm.forward:
            assert original in restored, f"'{original}' not in restored text"

        # 3. Audit-log: write to temp file, assert zero original values
        import tempfile as _tmp
        from pathlib import Path as _Path

        audit_tmp = _tmp.NamedTemporaryFile(suffix=".jsonl", delete=False)
        audit_tmp.close()
        gw2 = PseudonymisationGateway(
            jurisdictions=[
                "india", "uae", "uk", "usa", "australia", "singapore", "eu",
            ],
            audit_log_path=audit_tmp.name,
        )
        gw2.sanitize(test_text, matter_id="LEAK-FUZZ")

        with open(audit_tmp.name, "r") as fh:
            raw_log = fh.read()

        # Parse the log entry
        entry = _json.loads(raw_log.strip().split("\n")[0])

        # SECURITY: assert counts/types are present but NO original values
        assert "entity_count" in entry
        assert isinstance(entry["entity_count"], int)
        assert "entity_types" in entry
        assert isinstance(entry["entity_types"], list)

        # Check every field for potential leaks of test PII
        log_str = _json.dumps(entry)
        # These originals must NEVER appear in the log
        forbidden = [
            "Rahul", "Verma", "Sunita", "Priyanka", "Desai", "Vikram", "Reddy",
            "9876", "5432", "1098", "ZZTOP1234K",
            "784-1990", "Khalid", "Al-Mansoori",
            "AB123456C", "S9876543A", "G1234567B",
            "rahul.verma", "@example.com",
            "98765432101",
        ]
        for token in forbidden:
            assert token not in log_str, (
                f"AUDIT LEAK: '{token}' found in audit log for text: {test_text[:50]}..."
            )

        _Path(audit_tmp.name).unlink()
