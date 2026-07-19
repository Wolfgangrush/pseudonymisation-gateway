"""UAE / Dubai-DIFC-specific PII patterns.

Covers: Emirates ID · UAE IBAN · Trade License (Dubai Economy · DIFC · IFZA · DMCC ·
JAFZA · DAFZA) · DIFC Court case numbers (CFI · CA · SCT) · Cassation case numbers ·
UAE phone (+971) · AED amounts.
"""

from __future__ import annotations

import re

from ._checksums import iban_validate

# Emirates ID — 15 digits structured: 784-YYYY-XXXXXXX-X
# The 784 prefix + fixed grouping is already a strong structural floor (this is
# NOT the "any-N-digits" over-match class), so no extra checksum gate is applied.
EMIRATES_ID_RE = re.compile(r"\b784[-\s]?\d{4}[-\s]?\d{7}[-\s]?\d\b")

# UAE IBAN — AE + 2 check digits + 19 digits (23 chars total).
# mod-97 validated (kills random AE-prefixed digit runs).
UAE_IBAN_RE = re.compile(r"\bAE\d{2}(?:\s?\d){19}\b")

# UAE Trade License — Dubai Economy / DIFC / Free Zones
TRADE_LICENSE_RE = re.compile(
    r"\b(?:CN|DIFC|IFZA|DMCC|JAFZA|DAFZA|DSO|DIC|TECOM)[-\s]?\w{4,12}\b",
    re.IGNORECASE,
)

# UAE phone — +971 prefix or local 050/052/054/055/056/058 mobile
UAE_PHONE_RE = re.compile(
    r"(?:\+?971[-\s]?)?(?:0?5[02456 8])[-\s]?\d{3}[-\s]?\d{4}\b"
)

# AED amounts — AED / د.إ / Dhs / DH, incl. negative and accounting forms
AED_AMOUNT_RE = re.compile(
    r"\(?-?\s?(?:AED|د\.إ|Dhs\.?|DH)\s?-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?",
    re.IGNORECASE,
)

# DIFC Court case numbers — [YYYY] DIFC CFI/CA/SCT NNN
DIFC_CASE_RE = re.compile(
    r"\[?\d{4}\]?\s+DIFC\s+(?:CFI|CA|SCT)\s+\d{1,4}",
    re.IGNORECASE,
)

# UAE Cassation case numbers — "Cassation Petition No. XXX of YYYY"
UAE_CASSATION_RE = re.compile(
    r"Cassation\s+(?:Petition|Appeal|Case)\s+No\.?\s*\d+\s+of\s+\d{4}",
    re.IGNORECASE,
)

# VAT TRN — 15 digits, typically ending 0003. Deliberately strict (caller-context required)
# because bare 15-digit numbers false-positive heavily. Not in default PATTERNS.
VAT_TRN_RE = re.compile(r"\bTRN\s*\d{15}\b", re.IGNORECASE)


PATTERNS: list[tuple[re.Pattern, str]] = [
    (EMIRATES_ID_RE, "EMIRATES_ID"),
    (UAE_IBAN_RE, "UAE_IBAN", iban_validate),
    (TRADE_LICENSE_RE, "TRADE_LICENSE"),
    (DIFC_CASE_RE, "DIFC_CASE"),
    (UAE_CASSATION_RE, "UAE_CASE"),
    (UAE_PHONE_RE, "UAE_PHONE"),
    (AED_AMOUNT_RE, "AED_AMOUNT"),
    (VAT_TRN_RE, "VAT_TRN"),
]
