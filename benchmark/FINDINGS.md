# Pseudonymisation-Gateway · Two-Sided Detector Audit — Findings

**Run:** 2026-06-28 IST · on-box (Mac mini `ornith-1.0-9b` + `nomic-embed`) · **zero egress**
**Method:** checksums minted & verified by deterministic code (Verhoeff / GSTIN base-36 / IBAN mod-97 / NRIC weighted / ITIN range) — the local LLM only produced realistic *context* and *decoys*, every one hard-gated by the gateway's own validators so model hallucination cannot corrupt the corpus.
**Corpus:** 273 cases — 226 valid positives (bare + real-world variant + buried in document context) · 47 shaped-but-invalid look-alikes.
**Jurisdictions:** india · usa · eu · uk · australia · singapore · uae + shared.

| Axis | Result |
|---|---|
| **Recall** (valid IDs caught) | **77.9%** (176/226) |
| **Checksum-validator precision** (invalid Aadhaar/GSTIN/IBAN/NRIC/ITIN rejected) | **100% — airtight** |
| **Whole-detector precision on arbitrary digit strings** | weak — see F-4 |

The checksum tier is excellent: **every** invalid Aadhaar, GSTIN, IBAN, NRIC and ITIN was correctly rejected; PAN/GSTIN/ITIN/NRIC/IFSC/INR/vehicle all hit **100% recall**. The misses are not random — they cluster in three real-world formatting variants, and one detector family over-fires.

---

## RECALL findings — variants that slip past *both* the detector and the residue net

### F-1 · Dash-separated Aadhaar — **HIGH** (silent cloud-send risk)
`2345-6789-0123` is a common print/scan form. `AADHAAR_RE = \b[2-9]\d{3}\s?\d{4}\s?\d{4}\b` allows spaces but **not dashes**, so it is not tokenised — and the residue scanner's 12-digit-run rule also misses it (the dashes break the run). Verified: `scan_residue("2345-6789-0123").high == []`. Neither tier catches it → it would be sent to the cloud verbatim.
**Fix:** allow `[\s-]?` between Aadhaar groups in `AADHAAR_RE`; add a dash/space-tolerant 12-digit residue rule.

### F-2 · Spaced/grouped IBAN — **HIGH** (silent cloud-send risk)
The standard printed IBAN form — `GB29 NWBK 6016 1331 9268 19` — is missed by **all** of `UK_IBAN_RE`, `EU_IBAN_RE`, `UAE_IBAN_RE` (each is `\b<CC>\d{2}[A-Z0-9]{n}\b` with no internal whitespace) and by the residue net. Verified: `scan_residue("GB29 NWBK …").high == []`. Plain (unspaced) IBANs are caught at 100%; only the grouped form leaks — but the grouped form is how IBANs actually appear on statements and letterheads.
**Fix:** whitespace-strip a candidate window before applying the IBAN regex + `iban_validate` (the validator already strips spaces internally — only the *regex gate* rejects them).

### F-3 · `+91`-spaced Indian mobile — **MEDIUM**
`+91 98765 43210` is missed — `INDIA_PHONE_RE` expects 10 contiguous digits after the prefix, and the space inside the subscriber number breaks `\d{9}`. Bare `9876543210` is caught.
**Fix:** tolerate internal `[\s-]` in the subscriber group.

---

## PRECISION finding — the phone detectors over-redact

### F-4 · Phone regexes fire on any long digit run — **MEDIUM** (over-redaction)
`US_PHONE_RE = (?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b` makes its separators optional **and has no left word-boundary**, so it matches any 10-of-12 digit substring. Result: bare 12-digit **invoice / order / reference numbers** and even **IBAN fragments** are redacted as phone numbers.

Verified, clean repro:
```
"Invoice number 123456789012 dated 2026-06-28"  ->  (False, ['US_PHONE', 'DATE'])
"987654321098"                                  ->  (False, ['US_PHONE', 'INDIA_PHONE'])
```
18 of 32 adversarial decoys tripped a phone pattern (US/UK/AU/UAE/SG). This is over-redaction, not a leak of real PII — but it erodes trust and corrupts documents that legitimately carry long reference numbers.
**Fix:** anchor the phone regexes with a left `\b`, require at least one real separator (or cap the contiguous-digit run ≤ 11), and reject when the wider token is a known structured ID (IBAN/GSTIN) already validated upstream.

---

## Severity roll-up

| ID | Class | Severity | One-line fix |
|---|---|---|---|
| F-1 | recall (silent send) | **HIGH** | dash-tolerant Aadhaar regex + residue rule |
| F-2 | recall (silent send) | **HIGH** | whitespace-strip before IBAN regex gate |
| F-3 | recall | MEDIUM | tolerate internal space in `+91` phone |
| F-4 | precision (over-redact) | MEDIUM | anchor phone regex; cap digit run; add separator |

## Reproduce
```bash
cd benchmark
python3 gold_generator.py       # deterministic gold (checksum-minted + self-checked)
python3 build_context_mini.py   # mini adds realistic context + decoys (on-box, checksum-gated)
python3 run_benchmark.py        # scores recall + precision -> BENCHMARK_REPORT.md + benchmark_results.json
```

_Note: F-1 and F-2 are the ones to fix first — they are the only findings where sensitive data reaches the cloud **silently** (no residue flag for the practitioner to confirm). F-4 is the opposite failure mode (too eager), lower urgency under the gateway's "surface, never auto-block" stance._
