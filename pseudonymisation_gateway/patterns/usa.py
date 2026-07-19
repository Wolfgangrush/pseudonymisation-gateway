"""USA-specific PII patterns.

Covers: SSN · ITIN · EIN · US phone (+1) · USD amounts · Driver License (state-agnostic
with keyword context) · US Federal court docket numbers.

Note: state-specific identifiers (driver license formats per state, state-court case
formats) are scoped for v0.2. The current driver-license pattern requires keyword
context (DL/DLN/License) to avoid false positives.
"""

from __future__ import annotations

import re

from ._checksums import itin_validate

# SSN — XXX-XX-XXXX (with the SSA-issued exclusions: 000, 666, 9XX area numbers reserved)
SSN_RE = re.compile(r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b")

# ITIN — 9XX-XX-XXXX (starts with 9; group number 70-88, 90-92, 94-99).
# Group-range validated via itin_validate.
ITIN_RE = re.compile(r"\b9\d{2}-\d{2}-\d{4}\b")

# EIN (Employer Identification Number) — XX-XXXXXXX, keyword-prefixed
EIN_RE = re.compile(r"\bEIN[\s:#]*\d{2}-\d{7}\b", re.IGNORECASE)

# US phone — +1 prefix or 10-digit format with various separators
US_PHONE_RE = re.compile(r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")

# USD amounts — US$ or USD (avoid raw $ which conflicts with AUD/SGD/etc.),
# incl. negative and accounting forms (-US$500, (USD 500))
USD_AMOUNT_RE = re.compile(
    r"\(?-?\s?(?:US\$|USD)\s?-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?",
    re.IGNORECASE,
)

# Driver License — state-agnostic, keyword-prefixed
US_DL_RE = re.compile(
    r"\b(?:DL|DLN|License)[\s:#]*[A-Z0-9]{6,12}\b",
    re.IGNORECASE,
)

# US Federal court docket — X:XX-cv/cr/md/mc-XXXXX
US_DOCKET_RE = re.compile(
    r"\b\d{1,2}:\d{2}-(?:cv|cr|md|mc)-\d{4,6}\b",
    re.IGNORECASE,
)

# US ZIP — 5 digits or 5+4
US_ZIP_RE = re.compile(r"\b\d{5}(?:-\d{4})?\b")


PATTERNS: list[tuple[re.Pattern, str]] = [
    (SSN_RE, "SSN"),
    (ITIN_RE, "ITIN", itin_validate),
    (EIN_RE, "EIN"),
    (US_DL_RE, "US_DL"),
    (US_DOCKET_RE, "US_DOCKET"),
    (US_PHONE_RE, "US_PHONE"),
    (USD_AMOUNT_RE, "USD_AMOUNT"),
    # ZIP deliberately omitted from default PATTERNS — 5-digit pattern false-positives
    # heavily on case numbers, year, etc. Caller register_pattern() if needed.
]
