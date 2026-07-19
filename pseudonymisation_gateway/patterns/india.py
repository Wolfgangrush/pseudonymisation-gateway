"""India-specific PII patterns.

Covers: Aadhaar · PAN · GSTIN · IFSC · Indian phone · ₹ amounts · FIR numbers ·
Indian vehicle registration (state-series + Bharat/BH-series) · Indian-court
case numbers.

Used standalone for India firms AND as diaspora overlay in non-India firms
(Dubai · Australia · UK · USA · EU · Singapore all have substantial South Asian
diaspora — Indian PII detection remains valuable for Indian-expat client matters).

Detector precision
------------------
Some Indian identifiers carry a checksum or a fixed internal structure. A bare
"right shape" regex over-fires badly: *any* 12-digit run (invoice numbers,
timestamps, barcodes, UPI references) looks like an Aadhaar. To redact with
precision we attach an optional ``validator`` to a pattern (third tuple element);
the core engine only tokenises a match when the validator returns ``True``.

This is the *detector* (precision) tier. Recall is preserved separately by the
residue scanner (``core.scan_residue``), which still surfaces *any* 12-digit run
for human review — so a mistyped / OCR'd Aadhaar that fails its checksum is never
silently sent to the cloud; it is flagged for the practitioner to confirm.
"""

from __future__ import annotations

import re

# ── Checksum / structural validators ─────────────────────────────────────

# Verhoeff dihedral-group tables (used by UIDAI for the Aadhaar check digit).
_VERHOEFF_D = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
    (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
    (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
    (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0),
)
_VERHOEFF_P = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 9, 1, 4, 3, 7, 6, 2),
    (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
    (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
    (7, 0, 4, 6, 9, 1, 3, 2, 5, 8),
)


def _verhoeff_ok(digits: str) -> bool:
    """True iff ``digits`` (incl. trailing check digit) passes Verhoeff."""
    c = 0
    for i, ch in enumerate(reversed(digits)):
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][int(ch)]]
    return c == 0


def aadhaar_validate(s: str) -> bool:
    """Validate an Aadhaar candidate.

    Rejects the dominant false positives (invoice numbers, timestamps, barcodes,
    UPI reference numbers) by requiring:
    - exactly 12 digits (spaces stripped),
    - a first digit in 2-9 (UIDAI never issues numbers starting 0 or 1),
    - a valid Verhoeff check digit.
    """
    digits = re.sub(r"\D", "", s)
    if len(digits) != 12:
        return False
    if digits[0] in "01":
        return False
    return _verhoeff_ok(digits)


# GSTIN check digit — base-36 weighted scheme published by GSTN.
_GSTIN_CODEPOINTS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Valid GST state codes: 01-38 (states/UTs), plus 97 (Other Territory) and
# 99 (Centre Jurisdiction).
_GSTIN_STATE_CODES = set(range(1, 39)) | {97, 99}


def _gstin_check_digit(first14: str) -> str:
    """Compute the GSTIN check character for the first 14 characters."""
    factor = 2
    total = 0
    mod = len(_GSTIN_CODEPOINTS)
    for ch in reversed(first14):
        cp = _GSTIN_CODEPOINTS.index(ch)
        prod = factor * cp
        factor = 1 if factor == 2 else 2
        total += prod // mod + prod % mod
    return _GSTIN_CODEPOINTS[(mod - (total % mod)) % mod]


def gstin_validate(s: str) -> bool:
    """Validate a GSTIN candidate: 15 chars, real state code, valid check digit.

    The first two digits must be a recognised GST state code; characters 3-12 are
    the holder's PAN; the 15th character is a base-36 checksum over the first 14.
    A random GSTIN-shaped string (e.g. ``27ABCDE1234F1Z5``) fails the checksum.
    """
    s = s.strip().upper()
    if len(s) != 15 or not s[:2].isdigit():
        return False
    if int(s[:2]) not in _GSTIN_STATE_CODES:
        return False
    return _gstin_check_digit(s[:14]) == s[14]


# ── Patterns ─────────────────────────────────────────────────────────────

# Aadhaar — 12 digits (optionally 4-4-4 spaced), first digit 2-9.
# Checksum-validated via aadhaar_validate (kills 12-digit invoice/timestamp/UPI
# false positives).
AADHAAR_RE = re.compile(r"\b[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}\b")

# PAN — 5 letters + 4 digits + 1 letter. The 4th letter is the holder-type code
# (P individual · C company · H HUF · F firm/LLP · A AOP · T trust · B BOI ·
# L local authority · J artificial juridical person · G government), so it is
# constrained to that set rather than any A-Z.
PAN_RE = re.compile(r"\b[A-Z]{3}[ABCFGHJLPT][A-Z]\d{4}[A-Z]\b")

# GSTIN — 2-digit state code + PAN (10) + entity code (1) + 'Z' + checksum (1).
# Checksum-validated via gstin_validate.
GSTIN_RE = re.compile(r"\b\d{2}[A-Z]{3}[ABCFGHJLPT][A-Z]\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b")

# Indian phone — +91 prefix optional, 10 digits starting 6-9
INDIA_PHONE_RE = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}\b")

# ₹ amounts (Indian grouping or numeric), including negative and accounting
# (parenthesised) forms: -₹5,000 · ₹-5,000 · (₹5,000) · Rs. -5,000
INR_AMOUNT_RE = re.compile(
    r"\(?-?\s?(?:₹|Rs\.?|INR)\s?-?\d{1,3}(?:,\d{2,3})*(?:\.\d+)?\)?"
)

# Indian case numbers — Bombay HC / SC / generic
INDIA_CASE_RE = re.compile(
    r"(?:(?:Civil|Criminal|Writ|Special Leave|SLP|WP|CRL|MAT)\s+"
    r"(?:Appeal|Petition|Application)?\s*No\.?\s*\d+\s+of\s+\d{4})",
    re.IGNORECASE,
)

# FIR numbers — "FIR No. 123/2024"
FIR_RE = re.compile(r"\bFIR\s+No\.?\s*\d+/\d{2,4}\b", re.IGNORECASE)

# IFSC — 4 letters + 0 + 6 alphanumerics
IFSC_RE = re.compile(r"\b[A-Z]{4}0[A-Z\d]{6}\b")

# Indian vehicle registration (state series) — SS-NN-XX-NNNN
INDIA_VEHICLE_RE = re.compile(r"\b[A-Z]{2}[\s-]?\d{1,2}[\s-]?[A-Z]{1,2}[\s-]?\d{4}\b")

# Bharat (BH) series — YY BH NNNN XX (e.g. "22 BH 1234 AB"). The plate leads
# with the 2-digit registration year, so the state-series pattern above can
# never match it.
INDIA_BH_VEHICLE_RE = re.compile(r"\b\d{2}[\s-]?BH[\s-]?\d{4}[\s-]?[A-Z]{1,2}\b")


# PATTERNS entries are ``(pattern, entity_type)`` or, where a checksum /
# structural validator applies, ``(pattern, entity_type, validator)``. The core
# engine tokenises a validated match only when ``validator(match) is True``.
PATTERNS: list[tuple] = [
    (AADHAAR_RE, "AADHAAR", aadhaar_validate),
    (PAN_RE, "PAN"),
    (GSTIN_RE, "GSTIN", gstin_validate),
    (IFSC_RE, "IFSC"),
    (FIR_RE, "FIR_NO"),
    (INDIA_CASE_RE, "INDIA_CASE"),
    (INDIA_VEHICLE_RE, "INDIA_VEHICLE"),
    (INDIA_BH_VEHICLE_RE, "INDIA_VEHICLE"),
    (INDIA_PHONE_RE, "INDIA_PHONE"),
    (INR_AMOUNT_RE, "INR_AMOUNT"),
]
