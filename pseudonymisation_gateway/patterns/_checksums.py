"""Cross-jurisdiction checksum / structural validators.

These back the optional ``validator`` third element of a PATTERNS entry (see
``core._unpack_detector``). A validator is a callable ``str -> bool``; the engine
tokenises a regex match only when the validator accepts it. The goal is detector
*precision* — rejecting shaped-but-invalid look-alikes (a random IBAN-shaped run,
an NRIC with the wrong check letter) — without weakening recall, which the residue
scanner preserves separately.

Privacy-tool stance: a validator must only reject things that are *definitely not*
the identifier. Where an algorithm is not pinned with confidence (e.g. the newer
Singapore M-series FIN check), the validator accepts the structurally-valid value
rather than risk a false negative (a real ID silently sent to the cloud).
"""

from __future__ import annotations

import re


# ── IBAN (ISO 13616) — mod-97 check ──────────────────────────────────────
# Used by UAE (AE), UK (GB), and EU member-state IBANs.


def iban_validate(s: str) -> bool:
    """True iff ``s`` is a structurally valid IBAN (ISO 7064 mod-97-10).

    Rejects the dominant false positive: a country-prefixed alphanumeric run of
    the right length whose check digits do not reconcile.
    """
    iban = re.sub(r"\s", "", s).upper()
    if not (5 <= len(iban) <= 34):
        return False
    if not (iban[:2].isalpha() and iban[2:4].isdigit()):
        return False
    if not iban[4:].isalnum():
        return False
    # Move the four initial characters to the end, then map letters A=10..Z=35.
    rearranged = iban[4:] + iban[:4]
    digits = "".join(str(int(ch, 36)) if ch.isalpha() else ch for ch in rearranged)
    return int(digits) % 97 == 1


# ── Singapore NRIC / FIN — weighted check letter ─────────────────────────

_NRIC_WEIGHTS = (2, 7, 6, 5, 4, 3, 2)
_NRIC_ST_LETTERS = "JZIHGFEDCBA"  # S / T citizens & PRs
_NRIC_FG_LETTERS = "XWUTRQPNMLK"  # F / G foreigners


def nric_validate(s: str) -> bool:
    """Validate a Singapore NRIC/FIN: prefix + 7 digits + weighted check letter.

    S/T (citizens, PRs) and F/G (foreigners) check letters are validated against
    the published weighting (2 7 6 5 4 3 2; +4 offset for T and G). The newer
    M-series (FIN issued from 2022) uses a different scheme that is not pinned
    here — M values are accepted on structure alone to avoid false negatives.
    """
    s = s.strip().upper()
    if len(s) != 9:
        return False
    prefix, digits, check = s[0], s[1:8], s[8]
    if not digits.isdigit() or not check.isalpha():
        return False
    if prefix == "M":
        return True  # structural accept — M-series checksum not pinned
    if prefix not in "STFG":
        return False
    total = sum(int(d) * w for d, w in zip(digits, _NRIC_WEIGHTS))
    if prefix in "TG":
        total += 4
    table = _NRIC_ST_LETTERS if prefix in "ST" else _NRIC_FG_LETTERS
    return table[total % 11] == check


# ── USA ITIN — group-number range ────────────────────────────────────────


def itin_validate(s: str) -> bool:
    """Validate a US ITIN: starts with 9, with a group number (4th-5th digits)
    in the IRS-assigned ranges 70-88, 90-92, 94-99."""
    digits = s.replace("-", "")
    if len(digits) != 9 or not digits.isdigit() or digits[0] != "9":
        return False
    group = int(digits[3:5])
    return 70 <= group <= 88 or 90 <= group <= 92 or 94 <= group <= 99
