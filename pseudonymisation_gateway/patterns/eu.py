"""EU-specific PII patterns.

Covers: IBAN (all 27 EU member states) · EU VAT · EORI · selected national IDs
(German Steuer-ID · French INSEE · Italian Codice Fiscale) · CJEU case numbers ·
EUR amounts.

Note: per-member-state national-ID variants are extensive (27 countries with
different formats). v0.1.0 ships with three high-coverage variants (DE / FR / IT).
v0.2 will add ES · NL · BE · PL · AT · others on request — see JURISDICTIONS.md.
"""

from __future__ import annotations

import re

from ._checksums import iban_validate

# EU member-state country prefix group (used in IBAN + VAT + EORI patterns)
EU_COUNTRY_PREFIX = (
    "AT|BE|BG|CY|CZ|DE|DK|EE|ES|FI|FR|GR|HR|HU|IE|IT|LT|LU|LV|MT|NL|PL|PT|RO|SE|SI|SK"
)

# EU IBAN — country prefix + 2 check digits + 11-30 alphanumeric (varies per member state)
EU_IBAN_RE = re.compile(
    rf"\b(?:{EU_COUNTRY_PREFIX})\d{{2}}[A-Z0-9]{{11,30}}\b"
)

# EU VAT — country prefix + 8-12 alphanumeric
EU_VAT_RE = re.compile(
    rf"\b(?:{EU_COUNTRY_PREFIX})[\sU]?[A-Z0-9]{{8,12}}\b"
)

# EU EORI (Economic Operator) — country prefix + 15 alphanumeric
EU_EORI_RE = re.compile(
    rf"\b(?:{EU_COUNTRY_PREFIX})\d{{15}}\b"
)

# German Steuer-ID — 11 digits, keyword-prefixed (Steuer-ID or Steueridentifikationsnummer)
GERMAN_TAX_ID_RE = re.compile(
    r"\bSteuer-?(?:ID|nummer)[\s:#]*\d{11}\b",
    re.IGNORECASE,
)

# French INSEE — 15 digits, keyword-prefixed
FRENCH_INSEE_RE = re.compile(
    r"\bINSEE[\s:#]*\d{15}\b",
    re.IGNORECASE,
)

# Italian Codice Fiscale — 6 letters + 2 digits + 1 letter + 2 digits + 1 letter + 3 digits + 1 letter
ITALIAN_CF_RE = re.compile(
    r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b"
)

# CJEU case numbers — C-XXX/YY (court) or T-XXX/YY (general court)
CJEU_CASE_RE = re.compile(r"\b(?:C|T)-\d{1,4}/\d{2}\b")

# EUR amounts — € (European grouping), incl. negative and accounting forms
EUR_AMOUNT_RE = re.compile(
    r"\(?-?\s?€\s?-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\)?"
)


PATTERNS: list[tuple[re.Pattern, str]] = [
    (EU_IBAN_RE, "EU_IBAN", iban_validate),
    (EU_VAT_RE, "EU_VAT"),
    (EU_EORI_RE, "EU_EORI"),
    (GERMAN_TAX_ID_RE, "DE_TAX_ID"),
    (FRENCH_INSEE_RE, "FR_INSEE"),
    (ITALIAN_CF_RE, "IT_CF"),
    (CJEU_CASE_RE, "CJEU_CASE"),
    (EUR_AMOUNT_RE, "EUR_AMOUNT"),
]
