"""Shared cross-jurisdiction patterns — email · honorific-driven names · ISO dates.

These patterns apply across all jurisdictions and are loaded by default unless
`include_shared=False` is passed to PseudonymisationGateway.
"""

from __future__ import annotations

import re

# Email — RFC-ish (covers practical cases; not full RFC 5322)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# ISO + common-Western date formats: YYYY-MM-DD · DD/MM/YYYY · DD Month YYYY · DD-MMM-YYYY
DATE_RE = re.compile(
    r"\b\d{4}-\d{1,2}-\d{1,2}\b"  # ISO
    r"|\b\d{1,2}[\s\-./](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
    r"|January|February|March|April|June|July|August|September|October|November|December"
    r"|\d{1,2})[\s\-./]\d{2,4}\b",
    re.IGNORECASE,
)

# Honorifics — multi-jurisdiction (English + Arabic-context + South Asian-context + EU)
HONORIFICS = {
    "Mr",
    "Mrs",
    "Ms",
    "Miss",
    "Mx",
    "Dr",
    "Prof",
    "Professor",
    "Hon",
    "Honorable",
    "Honourable",
    "Justice",
    "Judge",
    "Adv",
    "Advocate",
    "Atty",
    "Attorney",
    "Sir",
    "Madam",
    "Madame",
    # Arabic / Gulf context
    "Sheikh",
    "Sayed",
    "Sayyid",
    "Hajj",
    "Hajja",
    # South Asian context
    "Shri",
    "Smt",
    "Sri",
    "Md",
    "Mohd",
    "Mohammed",
    # European context
    "Herr",
    "Frau",
    "Monsieur",
    "Madame",
    "Signor",
    "Signora",
    "Don",
    "Doña",
    "Senhor",
    "Senhora",
}

# Heuristic name pattern: Honorific + (1-3 capitalized words) — captures name in group 1
NAME_RE = re.compile(
    r"\b(?:" + "|".join(HONORIFICS) + r")\.?\s+([A-Z][a-z]+(?:[\s-][A-Z][a-z]+){0,3})\b"
)

# Generic case number — "Civil Appeal No. 1234 of 2024" style (cross-jurisdiction common-law)
GENERIC_CASE_RE = re.compile(
    r"(?:Civil|Criminal|Writ|Special\s+Leave|Application|Petition|Appeal)\s+"
    r"(?:Appeal|Petition|Application|Suit)?\s*No\.?\s*\d+\s+of\s+\d{4}",
    re.IGNORECASE,
)

# Bank account heuristic — "Account No. 9-18 digits"
BANK_ACCT_RE = re.compile(
    r"\b(?:A/C|Account|Acct)\.?\s*(?:No\.?|Number)?\s*\d{9,18}\b",
    re.IGNORECASE,
)

# Patterns are loaded LAST (after country patterns) so country-specific match first
PATTERNS: list[tuple[re.Pattern, str]] = [
    (EMAIL_RE, "EMAIL"),
    (BANK_ACCT_RE, "BANK_ACCT"),
    (GENERIC_CASE_RE, "CASE_NO"),
    (DATE_RE, "DATE"),
    (NAME_RE, "PERSON"),  # MUST be last — captures everything else first
]
