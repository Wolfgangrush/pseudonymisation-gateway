# 🏗️ Architecture — `pseudonymisation-gateway`

Technical deep-dive on how the library works internally.

---

## 1. Three core concepts

### 1.1 `TokenMap` (in-memory only)

```python
@dataclass
class TokenMap:
    forward: dict[str, str]    # "John Smith" → "[PERSON_1]"
    reverse: dict[str, str]    # "[PERSON_1]" → "John Smith"
    counters: dict[str, int]   # "PERSON" → 5 (next ID will be 6)
```

**Properties:**
- Created per `sanitize()` call · destroyed when garbage-collected
- NEVER serialized · NEVER written to disk · NEVER sent over network
- Deterministic within a session: same original → same placeholder

**Why bidirectional:** `desanitize()` needs reverse lookup to restore originals. The reverse map is the load-bearing data structure for round-trips.

### 1.2 `PseudonymisationGateway` (engine)

Holds:
- `self.patterns: list[tuple[re.Pattern, str]]` — priority-ordered detection rules

Methods:
- `sanitize(text) → (clean_text, TokenMap)` — primary entry point
- `desanitize(text, token_map) → text` — restore originals
- `is_safe_for_cloud(text) → (bool, list[str])` — pre-flight assertion
- `register_pattern(pattern, entity_type)` — runtime extension

### 1.3 Jurisdiction modules

Each module under `pseudonymisation_gateway/patterns/` exposes a single `PATTERNS` list:

```python
# patterns/uae.py
PATTERNS: list[tuple[re.Pattern, str]] = [
    (EMIRATES_ID_RE, "EMIRATES_ID"),
    (UAE_IBAN_RE, "UAE_IBAN"),
    # ...
]
```

Pattern priority within a module: more-specific BEFORE less-specific. Across modules: country-specific BEFORE shared cross-jurisdiction.

---

## 2. The sanitize() algorithm

```python
def sanitize(self, text: str) -> tuple[str, TokenMap]:
    token_map = TokenMap()
    out = text
    for pattern, entity_type in self.patterns:
        matches = list(pattern.finditer(out))
        for m in reversed(matches):  # reverse order preserves offsets
            if entity_type == "PERSON" and m.lastindex:
                # NAME_RE captures the name in group(1), keeping honorific
                name_part = m.group(1)
                placeholder = token_map.add(name_part, entity_type)
                out = out[:m.start(1)] + placeholder + out[m.end(1):]
            else:
                original = m.group(0)
                placeholder = token_map.add(original, entity_type)
                out = out[:m.start()] + placeholder + out[m.end():]
    return out, token_map
```

**Critical details:**

**(a) Reverse-iteration over matches.** When you substitute placeholders into the output string, offsets of subsequent matches shift. Walking matches right-to-left means earlier matches' offsets stay valid.

**(b) Group-1 capture for PERSON patterns.** The `NAME_RE` regex matches `Honorific + Name` (e.g., "Mr. John Smith") but captures only the name part in group 1. This preserves the honorific in the output ("Mr. [PERSON_1]") while pseudonymising the name — which gives the LLM enough context to use the right tone without exposing identity.

**(c) Priority ordering matters.** If `EMIRATES_ID_RE` is listed before any pattern that could match a subset of its digits, Emirates ID detection wins. Reverse order = pattern leakage. The default ordering (country-specific → shared → PERSON last) is intentional.

**(d) Idempotent via TokenMap.add().** If the same entity appears multiple times in input, it gets the same placeholder. `[PERSON_1]` for "John Smith" stays `[PERSON_1]` across 50 mentions.

---

## 3. The desanitize() algorithm

```python
def desanitize(self, text: str, token_map: TokenMap) -> str:
    out = text
    # Sort placeholders by length descending — prevents [PERSON_1] eating [PERSON_10]
    placeholders = sorted(token_map.reverse.keys(), key=len, reverse=True)
    for placeholder in placeholders:
        out = out.replace(placeholder, token_map.reverse[placeholder])
    return out
```

**Why longest-first:** If you replace `[PERSON_1]` before `[PERSON_10]`, the substring `[PERSON_1]` inside `[PERSON_10]` would get replaced incorrectly, then the leftover `0]` would be stranded.

By sorting descending, `[PERSON_10]` (10 chars) gets replaced before `[PERSON_1]` (9 chars). Safe.

---

## 4. Pattern priority order (default)

When `PseudonymisationGateway(jurisdictions=["uae", "india"])` is instantiated, the patterns list is built like this:

```
1. UAE patterns (loaded first)
   ├─ EMIRATES_ID_RE → "EMIRATES_ID"
   ├─ UAE_IBAN_RE → "UAE_IBAN"
   ├─ TRADE_LICENSE_RE → "TRADE_LICENSE"
   └─ ... (all UAE patterns)

2. India patterns (loaded second)
   ├─ AADHAAR_RE → "AADHAAR"
   ├─ PAN_RE → "PAN"
   └─ ... (all India patterns)

3. Shared patterns (loaded last, default-on)
   ├─ EMAIL_RE → "EMAIL"
   ├─ DATE_RE → "DATE"
   └─ NAME_RE → "PERSON"  (final fallback)
```

In practice:
- Specific PII (Emirates ID, Aadhaar) fires first
- Then more general (email, dates)
- Then person names (the broadest pattern, last to avoid eating into specific IDs)

---

## 5. Session scoping (security property)

```python
# Session 1 — Dubai matter
gw1 = PseudonymisationGateway(jurisdictions=["uae", "india"])
clean1, tm1 = gw1.sanitize("Khalid Al-Mansoori (Emirates ID 784-...)")
# tm1: {"Khalid Al-Mansoori": "[PERSON_1]", "784-...": "[EMIRATES_ID_1]"}

# Session 2 — Different Dubai matter, new gateway
gw2 = PseudonymisationGateway(jurisdictions=["uae", "india"])
clean2, tm2 = gw2.sanitize("Different client Ahmed Khan...")
# tm2: {"Ahmed Khan": "[PERSON_1]"}  ← fresh counters, fresh map

# tm1 and tm2 are INDEPENDENT — no cross-session contamination
```

**Why this matters:** If you handle multiple matters in parallel, each gets its own gateway instance. The Khalid Al-Mansoori token map never accidentally restores into Ahmed Khan's session.

**Implementation:** `TokenMap` is a dataclass instantiated fresh per `gw.sanitize()`. No global state. No singleton. No shared dict.

---

## 6. What's NOT in the engine

Deliberate non-features:

- **No persistence** — token maps are session-scoped; persisting them across sessions would leak the pseudonymisation surface
- **No ML / spaCy NER** — pure-regex for v0.1.0. NER (spaCy / HuggingFace) is a future v0.2 optional dependency
- **No telemetry** — the library doesn't phone home, doesn't log, doesn't emit metrics. What stays on the user's machine stays on the user's machine.
- **No async I/O** — synchronous Python. The bottleneck is the cloud LLM API call, not regex compilation.
- **No string-similarity (Levenshtein) fallback** — if a pattern doesn't match exactly, the entity stays in cleartext. Use a stricter regex or `register_pattern()`.

---

## 7. Extension points

### 7.1 Add a custom pattern at runtime

```python
import re
gw = PseudonymisationGateway(jurisdictions=["uk"])

# Add firm-specific matter-ID pattern
gw.register_pattern(re.compile(r"MATTER-\d{6}"), "FIRM_MATTER_ID")

# This goes to the FRONT of the priority list — highest priority
```

### 7.2 Add a new jurisdiction module

Create `pseudonymisation_gateway/patterns/japan.py`:

```python
import re

MY_NUMBER_RE = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
JAPAN_PHONE_RE = re.compile(r"(?:\+81[\s-]?)?0\d{1,3}[\s-]?\d{4}[\s-]?\d{4}\b")

PATTERNS: list[tuple[re.Pattern, str]] = [
    (MY_NUMBER_RE, "JP_MY_NUMBER"),
    (JAPAN_PHONE_RE, "JP_PHONE"),
]
```

Use it:

```python
from pseudonymisation_gateway.patterns import japan
gw = PseudonymisationGateway(jurisdictions=[japan])
```

### 7.3 Disable shared patterns (advanced)

```python
gw = PseudonymisationGateway(jurisdictions=["uae"], include_shared=False)
# Only UAE patterns. No email, no name detection. Useful if you have your own NER layer.
```

---

## 8. Performance characteristics

- **O(N × M)** where N = number of patterns, M = length of text
- For typical legal documents (1-10 KB) with ~30 patterns: sub-millisecond per `sanitize()` call
- Regex compilation is one-time at module import; not paid per call
- Memory: O(K) where K = number of unique entities detected (TokenMap size)
- No threading concerns for stateless use; each session/gateway is independent

Practical benchmark: sanitizing a 5,000-word affidavit takes ~3 ms on M-series Mac with all 7 jurisdictions loaded.

---

## 9. Threat model — what this is NOT

This library is **defense-in-depth**, not a zero-knowledge proof. It will fail against:

1. **An attacker with access to the running Python process** (can read `gw.patterns` and the live `TokenMap`)
2. **Side-channel attacks** — request timing, length, frequency can leak entity counts even if names are scrubbed
3. **Vendor-side OCR/vision** — if you attach a PDF to a cloud LLM call, the PDF goes through unscrubbed
4. **Determined adversary** with access to both sanitized prompt and response — correlation attacks become possible
5. **User error** — copying restored text into another tool that doesn't know about your token map

For matters above a certain sensitivity threshold (privileged-client work, BCI Rule 36 / SRA / LPUL / equivalent professional confidentiality obligations), **always prefer local LLMs** (Ollama · llama.cpp · vLLM on user's machine). Use this library only for cloud calls where the practitioner has weighed and accepted the residual risk.

---

## 10. Testing strategy

- **Per-jurisdiction tests** in `tests/test_jurisdictions.py` — one assertion per pattern
- **Cross-jurisdiction tests** in `tests/test_cross_jurisdiction.py` — diaspora coverage (UAE + India, UK + India, etc.)
- **Round-trip tests** in `tests/test_core.py` — `sanitize() → desanitize()` must restore exact original
- **Idempotency tests** — repeat entity mentions → same placeholder

Synthetic PII fixtures only — no real client data ever in tests. Format-realistic but value-fabricated:
- Aadhaar: `1234 5678 9012`
- Emirates ID: `784-1985-1234567-8`
- NI Number: `AB123456C`
- SSN: `123-45-6789`
- etc.

These all match the production regex but are obvious-fakes for transparency.

---

## 11. Comparison to in-firm pseudonymisation.py (the predecessor)

The 7 country AI Law Firms originally each carried their own copy of `pseudonymisation.py` (inherited from the India template). When jurisdictional gaps surfaced, the duplication was untenable:

- Pattern improvement to one firm → manual sync across 6 others
- Drift between firms → some had Aadhaar coverage, others didn't
- No reusable test suite — each firm re-wrote test fixtures from scratch
- Whitelist for false-positive prevention varied across firms

This library is the **extraction** — single source of truth, jurisdiction-loadable, MIT-licensed, fully tested. Each AI Law Firm now imports from here:

```python
from pseudonymisation_gateway import PseudonymisationGateway
from pseudonymisation_gateway.patterns import uae

# Replace the in-firm pseudonymisation.py with this 3-line module
gw = PseudonymisationGateway(jurisdictions=[uae, "india"])
```

---

## See also

- [README.md](README.md) — quick start + integration examples
- [JURISDICTIONS.md](JURISDICTIONS.md) — per-country pattern catalog
- [COMPARISON.md](COMPARISON.md) — honest comparison vs Presidio / cloud DLP / differential privacy
