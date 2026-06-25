"""Singapore-specific PII patterns.

Covers: NRIC · FIN · UEN · CPF · SG phone (+65) · SGD amounts · SGCA / SGHC / SGDC
case numbers.
"""

from __future__ import annotations

import re

from ._checksums import nric_validate

# NRIC — S/T prefix + 7 digits + weighted check letter (citizens/PR)
NRIC_RE = re.compile(r"\b[ST]\d{7}[A-Z]\b")

# FIN — F/G/M prefix + 7 digits + weighted check letter (foreign workers/PR applicants)
FIN_RE = re.compile(r"\b[FGM]\d{7}[A-Z]\b")

# UEN (Unique Entity Number) — 8 digits + letter OR 9-10 digits + letter
# Strict to avoid false-positives on case numbers etc.
UEN_RE = re.compile(r"\bUEN[\s:#]*\d{8,10}[A-Z]\b", re.IGNORECASE)

# CPF (Central Provident Fund) — keyword-prefixed CPF account refs
CPF_RE = re.compile(r"\bCPF[\s:#]*\d{4}[\s-]?\d{4}\b", re.IGNORECASE)

# Singapore phone — +65 prefix or 8/9-digit format
SG_PHONE_RE = re.compile(
    r"(?:\+?65[\s-]?)?[89]\d{3}[\s-]?\d{4}\b"
)

# SGD amounts — S$, incl. negative and accounting forms (-S$500, (S$500))
SGD_AMOUNT_RE = re.compile(
    r"\(?-?\s?S\$\s?-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?"
)

# Singapore case numbers — [YYYY] SGCA/SGHC/SGDC/SGMC/SGFC/SICC NNN
SG_CASE_RE = re.compile(
    r"\[?\d{4}\]?\s+(?:SGCA|SGHC|SGDC|SGMC|SGFC|SICC)\s+\d{1,4}",
    re.IGNORECASE,
)


PATTERNS: list[tuple[re.Pattern, str]] = [
    (NRIC_RE, "NRIC", nric_validate),
    (FIN_RE, "FIN", nric_validate),
    (UEN_RE, "UEN"),
    (CPF_RE, "CPF"),
    (SG_CASE_RE, "SG_CASE"),
    (SG_PHONE_RE, "SG_PHONE"),
    (SGD_AMOUNT_RE, "SGD_AMOUNT"),
]
