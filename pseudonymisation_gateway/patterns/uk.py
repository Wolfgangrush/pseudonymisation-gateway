"""UK-specific PII patterns.

Covers: NI Number · NHS Number · UTR · UK VAT · UK IBAN · UK phone (+44) ·
GBP amounts · EWHC / EWCA / UKSC case numbers.
"""

from __future__ import annotations

import re

from ._checksums import iban_validate

# NI Number — 2 letters + 6 digits + 1 letter (e.g. AB123456C). Strict per HMRC spec.
NI_NUMBER_RE = re.compile(r"\b[A-CEGHJ-PR-TW-Z]{1}[A-CEGHJ-NPR-TW-Z]{1}\d{6}[A-D]{1}\b")

# NHS Number — 10 digits in 3-3-4 format, keyword-prefixed
NHS_NUMBER_RE = re.compile(
    r"\bNHS[\s:#]*\d{3}\s?\d{3}\s?\d{4}\b",
    re.IGNORECASE,
)

# UTR (Unique Taxpayer Reference) — 10 digits, keyword-prefixed
UTR_RE = re.compile(r"\bUTR[\s:#]*\d{10}\b", re.IGNORECASE)

# UK VAT — GB + 9 or 12 digits
UK_VAT_RE = re.compile(r"\bGB\d{9}(?:\d{3})?\b")

# UK IBAN — GB + 2 check + 18 alphanumeric. mod-97 validated.
UK_IBAN_RE = re.compile(r"\bGB\d{2}(?:\s?[A-Z0-9]){18}\b")

# UK phone — +44 prefix or 07/01/02 formats
UK_PHONE_RE = re.compile(
    r"(?:\+?44[\s-]?|0)(?:7\d{3}|[12]\d{3})[\s-]?\d{3}[\s-]?\d{3,4}\b"
)

# GBP amounts — £, incl. negative and accounting forms (-£500, (£500))
GBP_AMOUNT_RE = re.compile(r"\(?-?\s?£\s?-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?")

# UK case numbers — [YYYY] EWHC/EWCA/UKSC + division
UK_CASE_RE = re.compile(
    r"\[?\d{4}\]?\s+(?:EWHC|EWCA|UKSC|UKHL)(?:\s+(?:Civ|Crim|Comm|Admin|Fam|TCC|Ch|QB|KB))?\s+\d{1,4}",
    re.IGNORECASE,
)


PATTERNS: list[tuple[re.Pattern, str]] = [
    (NI_NUMBER_RE, "NI_NUMBER"),
    (NHS_NUMBER_RE, "NHS_NUMBER"),
    (UTR_RE, "UTR"),
    (UK_VAT_RE, "UK_VAT"),
    (UK_IBAN_RE, "UK_IBAN", iban_validate),
    (UK_CASE_RE, "UK_CASE"),
    (UK_PHONE_RE, "UK_PHONE"),
    (GBP_AMOUNT_RE, "GBP_AMOUNT"),
]
