# SELF-AUDIT-REPORT — pseudonymisation-gateway v0.3.0

**Builder:** DeepSeek (claude-deep)
**Date:** 2026-06-17
**Spec:** BMAD-SPEC-v0.3.md (APPROVED for build, RSH 2026-06-17)

---

## Files Changed

### New files (7)

| File | Feature | Description |
|---|---|---|
| `pseudonymisation_gateway/dictionary.py` | F1 (P0) | Per-matter parties.json dictionary — jurisdiction-scoped, case-insensitive whole-word matching, longest-match-first |
| `pseudonymisation_gateway/ner.py` | F1 (P1) | Optional spaCy NER pass — lazy import, degrade-to-warning when absent |
| `pseudonymisation_gateway/audit.py` | F3 | Append-only JSONL audit log — COUNTS ONLY, never values |
| `tests/test_dictionary.py` | F1 | Tests for bare-name catch, jurisdiction-scoped load, longest-match priority, gateway integration |
| `tests/test_residue.py` | F2 | Tests for HIGH/LOW residue surfacing, jurisdiction shapes, false-positive exclusion |
| `tests/test_audit.py` | F3 | Tests asserting zero original values in audit log, counts/types/timestamps present, leak-fuzz |
| `tests/test_ner_optional.py` | F1 (P1) | Tests for spaCy-absent → warning + pipeline still runs; release gate passes without spaCy |

### Modified files (4)

| File | Change |
|---|---|
| `pseudonymisation_gateway/core.py` | Added `ResidueReport` dataclass, dictionary pass in `sanitize()`, `scan_residue()` method, audit-log wiring, jurisdiction-aware residue rules. Backwards-compatible keyword-only params. |
| `pseudonymisation_gateway/__init__.py` | Bumped `__version__` to `"0.3.0"`; exported `ResidueReport` |
| `pyproject.toml` | Version `0.1.0 → 0.3.0`; added `[project.optional-dependencies] ner = ["spacy>=3.7"]`; core `dependencies = []` unchanged |
| `CHANGELOG.md` | Moved 3 roadmap items from `[Unreleased]` into a real `[0.3.0]` released section with full detail |

---

## Loop 1 — Leak Trace

### (a) Cloud-bound text

**Data flow through `sanitize()`:**

1. `text` (raw input) → `out = text`
2. **Pass 1 — Regex:** Each matched original value passes through `token_map.add(original, entity_type)` which stores the mapping in RAM. The placeholder `[ENTITY_N]` replaces the original in `out`.
3. **Pass 2 — Dictionary:** Each matched original passes through `token_map.add(m.group(0), entity_type)`. The placeholder replaces the original in `out`.
4. `return out, token_map` — `out` contains only placeholders + unmatched text.

**Verdict: NO original value reaches the cloud-bound `out` string.** ✅

### (b) Disk

The library writes to disk in exactly ONE place: `audit.py:AuditLogger.log()`.

**What goes into the log file:**

| Field | Type | Contains originals? |
|---|---|---|
| `matter_id` | `str \| None` | Caller-supplied matter identifier (pre-existing metadata, not detected PII) |
| `jurisdiction` | `list[str]` | Slugs like `["india", "uae"]` — never values |
| `entity_count` | `int` | `len(token_map.forward)` — integer count |
| `entity_types` | `list[str]` | `sorted(token_map.counters.keys())` — type labels like `["PERSON", "PAN"]` |
| `residue_result` | `dict` | `{"high_n": len(...), "low_n": len(...)}` — integer counts only |
| `model` | `str \| None` | Caller-supplied model name |
| `timestamp` | `str` | ISO-8601 string |

**No other disk writes exist:**
- `dictionary.py`: Reads FROM disk (caller's JSON), NEVER writes.
- `TokenMap`: In-RAM only; `forward`, `reverse`, `counters` dicts never serialized.
- `NER`: In-RAM only; spaCy model loaded into memory, never saved.

**Verdict: NO original entity value reaches disk through the library.** ✅

### (c) Audit log

Same as (b). The audit log IS the disk write. Entities are counted (`entity_count`), typed (`entity_types`), never valued. Residue is counted (`high_n`, `low_n`), never described.

**Verdict: NO original value in the audit log.** ✅

### ResidueReport surface (in-RAM, not persisted)

`scan_residue()` returns a `ResidueReport` with `high` and `low` lists containing DESCRIPTIONS like `"12-digit run possibly Aadhaar (india)"` and `"Capitalised bigram 'Rahul Verma' not in TokenMap"`. These descriptions DO mention what was found — this is necessary for the practitioner to make an informed decision (spec requirement: "surfaces, never auto-blocks"). However, this is an **in-RAM return value**, never written to disk. The audit log only receives `high_n` and `low_n` (integer counts). **No leak path.** ✅

---

## Loop 2 — Pytest + Leak-Fuzz

### Full test suite (`pytest -q`)

```
........................................................................ [ 80%]
..................                                                       [100%]
90 passed in 0.05s
```

### Test breakdown

| Test file | Count | Status |
|---|---|---|
| `tests/test_core.py` | 9 | All pass |
| `tests/test_jurisdictions.py` | 26 | All pass |
| `tests/test_cross_jurisdiction.py` | 6 | All pass |
| `tests/test_dictionary.py` | 13 | All pass |
| `tests/test_residue.py` | 16 | All pass |
| `tests/test_audit.py` | 13 (incl. leak-fuzz) | All pass |
| `tests/test_ner_optional.py` | 7 | All pass |
| **Total** | **90** | **All pass** |

### Leak-fuzz test (`test_leak_fuzz_bare_names_and_pii`)

Feeds 11 diverse PII strings through the full pipeline:
- Bare names (no honorific): "Rahul Verma", "Sunita Rao.", "Priyanka Desai", "Vikram Reddy"
- India PII: Aadhaar, PAN, GSTIN, IFSC
- UAE PII: Emirates ID
- UK PII: NI Number, NHS Number
- USA PII: SSN, Driver License
- Australia PII: TFN, Medicare
- Singapore PII: NRIC, FIN
- EU PII: Steuer-ID, IBAN
- Cross-cutting: Email, Phone, Date

**Assertions:**
1. ✅ Every original value tokenised → placeholders in sanitised output
2. ✅ `desanitize()` round-trip restores ALL originals
3. ✅ Audit log contains ZERO original values (24 forbidden tokens checked per iteration)
4. ✅ Audit log contains integer `entity_count` and `entity_types` list (type labels only)

### spaCy-absent verification

```
$ python3 -c "import spacy" → ModuleNotFoundError: No module named 'spacy'
```

All 90 tests pass WITHOUT spaCy installed. The release gate requirement is satisfied. ✅

---

## Spec Checklist

| Requirement | Status |
|---|---|
| F1 (P0): `dictionary.py` — per-matter parties.json, jurisdiction-scoped, longest-match-first | ✅ |
| F1 (P1): `ner.py` — optional spaCy, degrade-to-warning, not a hard dep | ✅ |
| F2: `scan_residue()` → `ResidueReport` — HIGH/LOW tiered, jurisdiction-aware, never auto-blocks | ✅ |
| F3: `audit.py` — append-only JSONL, COUNTS ONLY, never values | ✅ |
| `pyproject.toml` bumped to 0.3.0; `ner` optional-extra added; core `dependencies = []` | ✅ |
| `CHANGELOG.md` — roadmap items moved to `[0.3.0]` released section | ✅ |
| Backwards compatible: existing `sanitize()`, `desanitize()`, `is_safe_for_cloud()` unchanged | ✅ |
| In-RAM only for TokenMap + parties dictionary | ✅ |
| No network calls, no telemetry | ✅ |
| All tests pass WITHOUT spaCy installed | ✅ |
| NO git push performed | ✅ |

---

## Spec items NOT completed

None. All 3 features (F1, F2, F3) are fully implemented per the spec. All release-gate items are satisfied.

---

**NO git push performed.**
