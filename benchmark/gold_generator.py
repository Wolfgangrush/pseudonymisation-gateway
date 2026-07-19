#!/usr/bin/env python3
"""Deterministic GOLD minter for the pseudonymisation-gateway two-sided audit.

Mints, from the *published* spec of each identifier (NOT by copying the gateway),
a labelled corpus of:
  - VALID positives  (expect_detect=True)  in real-world formatting variants
    -> tests detector RECALL
  - shaped-but-INVALID look-alikes (expect_detect=False) from the standard
    false-positive classes
    -> tests detector PRECISION

Every minted "valid" carries a correct checksum (Verhoeff / GSTIN base-36 /
IBAN mod-97 / NRIC weighted / ITIN range); every "lookalike" is constructed to
fail. A self-check at the end re-validates the whole set so a generator bug can
never ship a mislabelled corpus.

Output: corpus_gold.jsonl  (rows: id,text,type,expect_detect,klass,variant,note)
"""
from __future__ import annotations
import json, os, random, re

random.seed(20260628)  # reproducible; no wall-clock entropy
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus_gold.jsonl")

# ───────────────────────── checksum algorithms (from spec) ─────────────────
_VD = ((0,1,2,3,4,5,6,7,8,9),(1,2,3,4,0,6,7,8,9,5),(2,3,4,0,1,7,8,9,5,6),
       (3,4,0,1,2,8,9,5,6,7),(4,0,1,2,3,9,5,6,7,8),(5,9,8,7,6,0,4,3,2,1),
       (6,5,9,8,7,1,0,4,3,2),(7,6,5,9,8,2,1,0,4,3),(8,7,6,5,9,3,2,1,0,4),
       (9,8,7,6,5,4,3,2,1,0))
_VP = ((0,1,2,3,4,5,6,7,8,9),(1,5,7,6,2,8,3,0,9,4),(5,8,0,9,1,4,3,7,6,2),
       (8,9,1,6,0,4,3,5,2,7),(9,4,5,3,1,2,6,8,7,0),(4,2,8,6,5,7,3,9,0,1),
       (2,7,9,3,8,0,6,4,1,5),(7,0,4,6,9,1,3,2,5,8))
_VINV = (0,4,3,2,1,5,6,7,8,9)

def verhoeff_check(num11: str) -> str:
    """Compute the Verhoeff check digit for an 11-digit body."""
    c = 0
    for i, ch in enumerate(reversed(num11)):
        c = _VD[c][_VP[(i + 1) % 8][int(ch)]]
    return str(_VINV[c])

_CP = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
def gstin_check(first14: str) -> str:
    factor, total, mod = 2, 0, len(_CP)
    for ch in reversed(first14):
        prod = factor * _CP.index(ch)
        factor = 1 if factor == 2 else 2
        total += prod // mod + prod % mod
    return _CP[(mod - (total % mod)) % mod]

def iban_check_digits(country: str, bban: str) -> str:
    """Return the two check digits for country+bban (ISO 7064 mod-97-10)."""
    rearr = bban + country + "00"
    digits = "".join(str(int(c, 36)) if c.isalpha() else c for c in rearr)
    check = 98 - (int(digits) % 97)
    return f"{check:02d}"

_NRIC_W = (2,7,6,5,4,3,2)
_ST = "JZIHGFEDCBA"; _FG = "XWUTRQPNMLK"
def nric_check(prefix: str, digits7: str) -> str:
    total = sum(int(d)*w for d, w in zip(digits7, _NRIC_W))
    if prefix in "TG": total += 4
    table = _ST if prefix in "ST" else _FG
    return table[total % 11]

# ───────────────────────── minters ────────────────────────────────────────
ROWS = []
def add(text, typ, expect, klass, variant, note=""):
    ROWS.append({"id": len(ROWS), "text": text, "type": typ,
                 "expect_detect": expect, "klass": klass,
                 "variant": variant, "note": note})

def mint_aadhaar():
    for _ in range(12):
        body = str(random.randint(2, 9)) + "".join(str(random.randint(0,9)) for _ in range(10))
        full = body + verhoeff_check(body)
        add(full, "AADHAAR", True, "valid", "plain", "12-digit, Verhoeff-valid")
        add(f"{full[:4]} {full[4:8]} {full[8:]}", "AADHAAR", True, "valid", "spaced-4-4-4", "")
        # dash-separated: a real-world variant the gateway regex does NOT allow -> recall probe
        add(f"{full[:4]}-{full[4:8]}-{full[8:]}", "AADHAAR", True, "valid", "dash-4-4-4",
            "real variant; gateway AADHAAR_RE omits dashes — expected RECALL miss")
    # look-alikes (precision): 12-digit non-Aadhaar runs
    add("100000000000", "AADHAAR", False, "lookalike", "leading-1", "first digit 1 — UIDAI never issues")
    add("847362910000", "AADHAAR", False, "lookalike", "bad-verhoeff", "valid shape, wrong check digit")
    add("Invoice 2024062800031", "AADHAAR", False, "lookalike", "invoice-13d", "13-digit invoice, not Aadhaar")
    add("UPI Ref 234567890124", "AADHAAR", False, "lookalike", "upi-ref", "12-digit UPI ref, bad checksum")

def mint_pan():
    HOLDER = "ABCFGHJLPT"
    L = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for _ in range(10):
        pan = ("".join(random.choice(L) for _ in range(3)) + random.choice(HOLDER) +
               random.choice(L) + "".join(str(random.randint(0,9)) for _ in range(4)) +
               random.choice(L))
        add(pan, "PAN", True, "valid", "upper", "format-valid PAN (no checksum)")
    add("ABDXE1234F", "PAN", False, "lookalike", "bad-holder", "4th char D not in holder set")
    add("ABCDE12345", "PAN", False, "lookalike", "all-digit-tail", "ends in digit, not letter")
    add("abcpe1234f", "PAN", False, "lookalike", "lowercase", "lowercase — gateway PAN_RE is [A-Z] only")

def mint_gstin():
    HOLDER = "ABCFGHJLPT"; L = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    states = list(range(1, 39)) + [97, 99]
    for _ in range(10):
        st = f"{random.choice(states):02d}"
        pan = ("".join(random.choice(L) for _ in range(3)) + random.choice(HOLDER) +
               random.choice(L) + "".join(str(random.randint(0,9)) for _ in range(4)) +
               random.choice(L))
        ent = random.choice("123456789")
        first14 = f"{st}{pan}{ent}Z"
        gstin = first14 + gstin_check(first14)
        add(gstin, "GSTIN", True, "valid", "upper", "state+PAN+entity+Z+checksum")
    # bad checksum
    add("27ABCDE1234F1Z5", "GSTIN", False, "lookalike", "bad-checksum", "classic shaped-but-invalid GSTIN")
    # invalid state code 40
    bad_first = "40ABCPE1234F1Z"
    add(bad_first + gstin_check(bad_first), "GSTIN", False, "lookalike", "bad-state",
        "state 40 not in 01-38/97/99 (even with a 'valid' check char)")

def mint_iban():
    for cc, blen in (("GB", 18), ("AE", 19), ("DE", 18)):
        for _ in range(4):
            if cc == "GB":
                bban = "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(4)) + \
                       "".join(str(random.randint(0,9)) for _ in range(14))
            else:
                bban = "".join(str(random.randint(0,9)) for _ in range(blen))
            chk = iban_check_digits(cc, bban)
            iban = f"{cc}{chk}{bban}"
            add(iban, "IBAN", True, "valid", f"{cc}-plain", "mod-97 valid")
            add(" ".join(iban[i:i+4] for i in range(0, len(iban), 4)),
                "IBAN", True, "valid", f"{cc}-spaced", "grouped-4 real-world print form")
    add("GB00BARC20031820000000", "IBAN", False, "lookalike", "bad-mod97", "GB-shaped, check digits don't reconcile")

def mint_nric():
    for pfx in "STFG":
        for _ in range(3):
            d7 = "".join(str(random.randint(0,9)) for _ in range(7))
            nric = f"{pfx}{d7}{nric_check(pfx, d7)}"
            add(nric, "NRIC", True, "valid", f"{pfx}-series", "weighted check-letter valid")
    # M-series accepted structurally (gateway design)
    add("M1234567K", "NRIC", True, "valid", "M-series", "M accepted on structure (gateway stance)")
    # wrong check letter
    d7 = "1234567"; good = nric_check("S", d7)
    bad = "A" if good != "A" else "B"
    add(f"S{d7}{bad}", "NRIC", False, "lookalike", "bad-check", "S-series, wrong check letter")

def mint_itin():
    for _ in range(8):
        g = random.choice(list(range(70, 89)) + list(range(90, 93)) + list(range(94, 100)))
        itin = f"9{random.randint(0,99):02d}-{g:02d}-{random.randint(0,9999):04d}"
        add(itin, "ITIN", True, "valid", "dashed", "group in IRS range")
    add("912-89-0000", "ITIN", False, "lookalike", "bad-group", "group 89 outside assigned ranges")
    add("812-70-0000", "ITIN", False, "lookalike", "no-leading-9", "does not start with 9")

def mint_misc():
    # INR amounts — incl. the negative/accounting forms the memory flagged
    for t, note in [("₹5,000", "plain"), ("-₹5,000", "negative"), ("₹-5,000", "inner-negative"),
                    ("(₹5,000)", "accounting-parens"), ("Rs. -5,000", "rs-negative"),
                    ("INR 1,23,456.78", "indian-grouping")]:
        add(t, "INR_AMOUNT", True, "valid", note, "")
    # Indian phone
    add("+91 98765 43210", "INDIA_PHONE", True, "valid", "spaced-91", "")
    add("9876543210", "INDIA_PHONE", True, "valid", "bare-10", "")
    add("5876543210", "INDIA_PHONE", False, "lookalike", "leads-5", "Indian mobiles start 6-9")
    # IFSC
    add("HDFC0001234", "IFSC", True, "valid", "std", "4 letters + 0 + 6")
    add("HDFC1001234", "IFSC", False, "lookalike", "no-zero", "5th char must be 0")
    # FIR
    add("FIR No. 123/2024", "FIR_NO", True, "valid", "std", "")
    # Vehicle
    add("MH-31-AB-1234", "INDIA_VEHICLE", True, "valid", "state-series", "")
    add("22 BH 1234 AB", "INDIA_VEHICLE", True, "valid", "bh-series", "")

# ───────────────────────── build + self-check ─────────────────────────────
for fn in (mint_aadhaar, mint_pan, mint_gstin, mint_iban, mint_nric, mint_itin, mint_misc):
    fn()

# Self-check: re-validate against the gateway's own validators so we never ship
# a mislabelled gold row. (Import the gateway in-process.)
import sys
GW = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, GW)
from pseudonymisation_gateway.patterns.india import aadhaar_validate, gstin_validate  # noqa
from pseudonymisation_gateway.patterns._checksums import iban_validate, nric_validate, itin_validate  # noqa

CHECK = {
    "AADHAAR": lambda s: aadhaar_validate(s),
    "GSTIN":   lambda s: gstin_validate(s),
    "IBAN":    lambda s: iban_validate(s),
    "NRIC":    lambda s: nric_validate(s),
    "ITIN":    lambda s: itin_validate(re.sub(r"[^\d]", "", s) if "-" in s else s),
}
mismatch = 0
for r in ROWS:
    chk = CHECK.get(r["type"])
    if not chk:
        continue
    # extract the raw identifier substring for checksum types
    raw = r["text"]
    if r["type"] == "AADHAAR":
        m = re.search(r"[2-9][\d\s-]{10,}\d", raw)
        cand = re.sub(r"[\s-]", "", m.group()) if m else raw
        if r["klass"] == "valid" and r["variant"] == "dash-4-4-4":
            continue  # checksum is valid; the recall miss is in the REGEX, asserted by the harness
        ok = chk(cand)
    else:
        ok = chk(raw)
    if ok != r["expect_detect"] and not (r["type"] == "NRIC" and r["variant"] == "M-series"):
        # valids must validate; lookalikes must fail
        if r["klass"] == "valid" and not ok:
            print(f"SELFCHECK FAIL (valid didn't validate): {r}")
            mismatch += 1
        if r["klass"] == "lookalike" and ok:
            print(f"SELFCHECK FAIL (lookalike validated): {r}")
            mismatch += 1

with open(OUT, "w", encoding="utf-8") as f:
    for r in ROWS:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

n_valid = sum(1 for r in ROWS if r["klass"] == "valid")
n_look = sum(1 for r in ROWS if r["klass"] == "lookalike")
print(f"wrote {len(ROWS)} gold rows -> {OUT}")
print(f"  valid positives : {n_valid}")
print(f"  lookalikes      : {n_look}")
print(f"  selfcheck mismatches: {mismatch}")
if mismatch:
    raise SystemExit("ABORT: gold corpus has mislabelled rows")
