"""India-specific PII patterns.

Covers: Aadhaar · PAN · GSTIN · IFSC · Indian phone · ₹ amounts · FIR numbers ·
Indian vehicle registration · Indian-court case numbers.

Used standalone for India firms AND as diaspora overlay in non-India firms
(Dubai · Australia · UK · USA · EU · Singapore all have substantial South Asian
diaspora — Indian PII detection remains valuable for Indian-expat client matters).
"""

from __future__ import annotations

import re

# Aadhaar — 12 digits, optionally space-separated as 4-4-4
AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")

# PAN — 5 alphabets + 4 digits + 1 alphabet (e.g. ABCDE1234F)
PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")

# GSTIN — 2-digit state code + PAN + entity number + Z + checksum
GSTIN_RE = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z][A-Z\d]\b")

# Indian phone — +91 prefix optional, 10 digits starting 6-9
INDIA_PHONE_RE = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}\b")

# ₹ amounts (Indian grouping or numeric)
INR_AMOUNT_RE = re.compile(
    r"(?:₹|Rs\.?|INR)\s?\d{1,3}(?:,\d{2,3})*(?:\.\d+)?\b"
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

# Indian vehicle registration — SS-NN-XX-NNNN
INDIA_VEHICLE_RE = re.compile(r"\b[A-Z]{2}[\s-]?\d{1,2}[\s-]?[A-Z]{1,2}[\s-]?\d{4}\b")


PATTERNS: list[tuple[re.Pattern, str]] = [
    (AADHAAR_RE, "AADHAAR"),
    (PAN_RE, "PAN"),
    (GSTIN_RE, "GSTIN"),
    (IFSC_RE, "IFSC"),
    (FIR_RE, "FIR_NO"),
    (INDIA_CASE_RE, "INDIA_CASE"),
    (INDIA_VEHICLE_RE, "INDIA_VEHICLE"),
    (INDIA_PHONE_RE, "INDIA_PHONE"),
    (INR_AMOUNT_RE, "INR_AMOUNT"),
]
