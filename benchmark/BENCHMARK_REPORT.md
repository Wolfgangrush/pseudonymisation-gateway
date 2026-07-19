# Pseudonymisation-Gateway — Two-Sided Detector Benchmark

_Generated on-box (Mac mini ornith-9b + nomic) · zero egress · checksums minted & verified by deterministic code, not the LLM._

**Jurisdictions loaded:** india, usa, eu, uk, australia, singapore, uae  ·  **shared patterns:** on

**Corpus:** 273 rows — 226 valid positives, 47 look-alike negatives


## Headline

| Axis | Score | |
|---|---|---|
| **Recall** (valid IDs caught) | **99.1%** | 224/226 |
| **Precision** (look-alikes ignored) | **61.7%** | 29/47 |
| Residue net caught of the recall misses | 0/2 | safety tier |

## Recall by identifier type

| Type | Recall | Caught/Total |
|---|---|---|
| AADHAAR | 100% | 72/72 |
| FIR_NO | 100% | 2/2 |
| GSTIN | 100% | 20/20 |
| IBAN | 100% | 48/48 |
| IFSC | 100% | 2/2 |
| INDIA_PHONE | 50% | 2/4 |
| INDIA_VEHICLE | 100% | 4/4 |
| INR_AMOUNT | 100% | 12/12 |
| ITIN | 100% | 16/16 |
| NRIC | 100% | 26/26 |
| PAN | 100% | 20/20 |

## Recall misses (detector regex did NOT fire)

| Type | Variant | Caught by residue net? | Sample |
|---|---|---|---|
| INDIA_PHONE | spaced-91 | ❌ NO — silent send risk | `+91 98765 43210` |
| INDIA_PHONE |  | ❌ NO — silent send risk | `Court filing line 12 cites defendant +91 98765 4` |

## Precision leaks (detector fired on a look-alike)

| Type | Variant | Detected as | Sample |
|---|---|---|---|
| LOOKALIKE_MIXED |  | ['US_PHONE'] | `123456789012` |
| LOOKALIKE_MIXED |  | ['US_PHONE'] | `IN29ICIC123456789012` |
| LOOKALIKE_MIXED |  | ['INDIA_PHONE', 'US_PHONE'] | `987654321098` |
| LOOKALIKE_MIXED |  | ['US_PHONE'] | `112233445566` |
| LOOKALIKE_MIXED |  | ['US_PHONE', 'UK_PHONE'] | `IT60X05428111010012345678` |
| LOOKALIKE_MIXED |  | ['US_PHONE', 'UAE_PHONE'] | `445566778899` |
| LOOKALIKE_MIXED |  | ['US_PHONE'] | `334455667788` |
| LOOKALIKE_MIXED |  | ['US_PHONE', 'SG_PHONE'] | `CH56048330210598765432` |
| LOOKALIKE_MIXED |  | ['INDIA_PHONE', 'US_PHONE'] | `556677889900` |
| LOOKALIKE_MIXED |  | ['US_PHONE'] | `123456789012` |
| LOOKALIKE_MIXED |  | ['US_PHONE', 'UK_PHONE'] | `270012345678901` |
| LOOKALIKE_MIXED |  | ['AU_PHONE'] | `FR14 2004 1010 0123 4567 8901 90` |
| LOOKALIKE_MIXED |  | ['INDIA_PHONE', 'US_PHONE'] | `987654321098` |
| LOOKALIKE_MIXED |  | ['INDIA_PHONE', 'US_PHONE'] | `290098765432109` |
| LOOKALIKE_MIXED |  | ['AU_PHONE'] | `FR14 2004 1010 0123 4567 8901 90` |
| LOOKALIKE_MIXED |  | ['US_PHONE', 'UK_PHONE'] | `270012345678901` |
| LOOKALIKE_MIXED |  | ['US_PHONE'] | `123456789012` |
| LOOKALIKE_MIXED |  | ['AU_PHONE'] | `FR14 2004 1010 0123 4567 8901 90` |

## How to reproduce

```bash
python3 gold_generator.py        # deterministic gold (checksums)
python3 build_context_mini.py    # mini adds realistic context (on-box)
python3 run_benchmark.py         # this report
```
