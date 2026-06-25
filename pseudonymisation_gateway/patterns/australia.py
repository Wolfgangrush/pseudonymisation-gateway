"""Australia-specific PII patterns.

Covers: TFN · Medicare · ABN · ACN · BSB · AU phone (+61) · AUD amounts ·
HCA/FCA/FCAFC/state Supreme Court case numbers.

Note: patterns require explicit keyword context (TFN: / ABN: / Medicare:)
because bare 8-11 digit numbers false-positive heavily (especially against
Indian Aadhaar diaspora detection).
"""

from __future__ import annotations

import re

# TFN (Tax File Number) — 9 digits, keyword-prefixed to avoid clobbering other 9-digit patterns
TFN_RE = re.compile(r"\bTFN[\s:]+\d{3}\s?\d{3}\s?\d{3}\b", re.IGNORECASE)

# Medicare — 10 digits, keyword-prefixed
MEDICARE_RE = re.compile(r"\bMedicare[\s:#]*\d{4}\s?\d{5}\s?\d\b", re.IGNORECASE)

# ABN (Australian Business Number) — 11 digits, keyword-prefixed
ABN_RE = re.compile(r"\bABN[\s:]+\d{2}\s?\d{3}\s?\d{3}\s?\d{3}\b", re.IGNORECASE)

# ACN (Australian Company Number) — 9 digits, keyword-prefixed
ACN_RE = re.compile(r"\bACN[\s:]+\d{3}\s?\d{3}\s?\d{3}\b", re.IGNORECASE)

# BSB (Bank-State-Branch routing code) — 6 digits in XXX-XXX format
AU_BSB_RE = re.compile(r"\bBSB[\s:]*\d{3}[-\s]?\d{3}\b", re.IGNORECASE)

# Australian phone — +61 prefix REQUIRED or 0-prefix mobile/landline
AU_PHONE_RE = re.compile(
    r"(?:\+61[\s-]?|0)(?:4\d{2}|[23478])[\s-]?\d{3,4}[\s-]?\d{3,4}\b"
)

# AUD amounts — A$ or AUD, incl. negative and accounting forms (-A$500, (A$500))
AUD_AMOUNT_RE = re.compile(
    r"\(?-?\s?(?:A\$|AUD?)\s?-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?",
    re.IGNORECASE,
)

# Australian case numbers — HCA · FCA · FCAFC · FCFCOA · state Supreme Courts
AU_CASE_RE = re.compile(
    r"\[?\d{4}\]?\s+(?:HCA|FCA|FCAFC|FCFCOA|VSC|NSWSC|QSC|WASC|SASC|TASSC|ACTSC|NTSC)\s+\d{1,4}",
    re.IGNORECASE,
)


PATTERNS: list[tuple[re.Pattern, str]] = [
    (TFN_RE, "TFN"),
    (MEDICARE_RE, "MEDICARE"),
    (ABN_RE, "ABN"),
    (ACN_RE, "ACN"),
    (AU_BSB_RE, "AU_BSB"),
    (AU_CASE_RE, "AU_CASE"),
    (AU_PHONE_RE, "AU_PHONE"),
    (AUD_AMOUNT_RE, "AUD_AMOUNT"),
]
