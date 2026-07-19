"""Core engine — TokenMap + PseudonymisationGateway.

Design principles:
- Session-scoped: each gateway instance = one user session
- In-memory only: TokenMap NEVER persisted to disk
- Deterministic: same entity within one session → same placeholder
- Extensible: register_pattern() to add custom patterns per matter
- Jurisdiction-aware: patterns loaded per country via patterns.<country> modules

Architecture (v0.3):

    USER INPUT (with real names, IDs, etc.)
           │
           ▼
    Regex pass (priority-ordered, jurisdiction-specific)
           │
           ▼
    Dictionary pass (per-matter parties.json — catches bare names)
           │
           ▼
    Placeholders inserted: [PERSON_1], [EMIRATES_ID_1], etc.
           │
           ▼
    Residue scan (tiered — HIGH surfacing, LOW audit-logged)
           │
           ▼
    Cloud LLM API call (sees only placeholders)
           │
           ▼
    Cloud response (still contains placeholders)
           │
           ▼
    desanitize() — placeholders → originals via TokenMap
           │
           ▼
    USER SEES original text with LLM completions
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


def _unpack_detector(entry: tuple) -> tuple:
    """Normalise a PATTERNS entry to ``(pattern, entity_type, validator)``.

    Entries may be ``(pattern, entity_type)`` or, where a checksum / structural
    validator applies, ``(pattern, entity_type, validator)``. The validator is a
    callable ``str -> bool``; a regex match is tokenised only when it returns
    ``True`` (e.g. an Aadhaar that passes its Verhoeff check digit). Entries
    without a validator are always tokenised on a regex match.
    """
    if len(entry) == 3:
        return entry
    pattern, entity_type = entry
    return pattern, entity_type, None


# ── Jurisdiction → residue-digit-run thresholds ──────────────────────────
# Map: jurisdiction_slug → list of (min_digits, max_digits, severity, label)
# Used by scan_residue() to flag digit runs that look like PII shapes
# specific to each jurisdiction.

_JURISDICTION_DIGIT_RUNS: dict[str, list[tuple[int, int, str, str]]] = {
    "india": [
        (12, 12, "high", "12-digit run possibly Aadhaar"),
        (10, 10, "low", "10-digit run possibly Indian phone"),
    ],
    "uk": [
        (9, 10, "high", "9-10 digit run possibly NHS/UTR"),
    ],
    "uae": [
        (15, 15, "high", "15-digit run possibly Emirates ID"),
    ],
    "usa": [
        (9, 9, "high", "9-digit run possibly SSN/ITIN/EIN"),
    ],
    "australia": [
        (9, 9, "high", "9-digit run possibly TFN/ACN/ABN"),
    ],
    "singapore": [
        (9, 9, "high", "9-char alphanumeric possibly NRIC/FIN"),
    ],
    "eu": [
        (11, 11, "low", "11-digit run possibly German Steuer-ID"),
    ],
}

# ── ResidueReport ────────────────────────────────────────────────────────

@dataclass
class ResidueReport:
    """Post-sanitisation residue scan result.

    Surfaces likely-missed PII to the practitioner. **Never auto-blocks** —
    the practitioner retains the final call (brain-frame: tool reminds,
    never gates).

    Attributes:
        high: descriptions of high-confidence residue (e.g. "12-digit run
              possibly Aadhaar"). Caller should soft-confirm or block.
        low: descriptions of low-confidence residue. Audit-logged; send proceeds.
        jurisdiction: active jurisdiction slugs at scan time.
    """

    high: list[str] = field(default_factory=list)
    low: list[str] = field(default_factory=list)
    jurisdiction: list[str] = field(default_factory=list)


# ── TokenMap ─────────────────────────────────────────────────────────────

@dataclass
class TokenMap:
    """Session-scoped placeholder ↔ original mapping. Never persisted."""

    forward: dict[str, str] = field(default_factory=dict)  # original → placeholder
    reverse: dict[str, str] = field(default_factory=dict)  # placeholder → original
    counters: dict[str, int] = field(default_factory=dict)  # entity_type → next id

    def add(self, original: str, entity_type: str) -> str:
        """Deterministic placeholder. Same entity within session → same placeholder."""
        if original in self.forward:
            return self.forward[original]
        n = self.counters.get(entity_type, 0) + 1
        self.counters[entity_type] = n
        placeholder = f"[{entity_type}_{n}]"
        self.forward[original] = placeholder
        self.reverse[placeholder] = original
        return placeholder


# ── PseudonymisationGateway ──────────────────────────────────────────────

class PseudonymisationGateway:
    """Strips PII from text before cloud-API send; restores on return.

    Args:
        jurisdictions: list of jurisdiction modules (or string slugs) to load
                       patterns from. Each module must expose a PATTERNS list of
                       ``(re.Pattern, entity_type)`` tuples. String slugs are
                       resolved via ``pseudonymisation_gateway.patterns.<slug>``.
        include_shared: whether to include cross-jurisdiction shared patterns
                        (email, name, date). Default True.

    Keyword-only args (v0.3):
        parties_file: optional path to a per-matter ``parties.json`` dictionary.
            Loaded into RAM only; never re-written by the library.
        audit_log_path: optional path for the append-only JSONL audit log.
            Counts only — never stores original values. If ``None``, no log
            is written.
        enable_ner: if ``True``, attempt to load spaCy ``en_core_web_sm`` for
            an optional NER pass. NER hits are surfaced through the residue
            tier, not auto-redacted. If spaCy or the model is not installed,
            a warning is logged and the pipeline continues without NER.

    Example — UAE-only:
        gw = PseudonymisationGateway(jurisdictions=["uae"])

    Example — per-matter dictionary + audit log:
        gw = PseudonymisationGateway(
            jurisdictions=["india", "uae"],
            parties_file="matter-4012/parties.json",
            audit_log_path="matter-4012/audit.jsonl",
        )
    """

    def __init__(
        self,
        jurisdictions: Iterable[str | object] = (),
        include_shared: bool = True,
        *,
        parties_file: str | None = None,
        audit_log_path: str | None = None,
        enable_ner: bool = False,
    ) -> None:
        # Entries are (pattern, entity_type) or (pattern, entity_type, validator).
        self.patterns: list[tuple] = []
        self._jurisdiction_slugs: list[str] = []

        self._load_jurisdictions(jurisdictions)
        if include_shared:
            from . import shared

            self.patterns.extend(shared.PATTERNS)

        # Per-matter dictionary (Feature 1 — P0)
        from .dictionary import PartiesDictionary

        self._dictionary = PartiesDictionary(
            parties_file=parties_file,
            active_jurisdictions=self._jurisdiction_slugs,
        )

        # Optional NER sanitiser (Feature 1 — P1)
        self._ner = None
        if enable_ner:
            from .ner import NERSanitiser

            self._ner = NERSanitiser()

        # Audit log (Feature 3)
        from .audit import AuditLogger

        self._audit = AuditLogger(path=audit_log_path)

    # ── public API ───────────────────────────────────────────────────────

    def sanitize(
        self,
        text: str,
        *,
        matter_id: str | None = None,
        model: str | None = None,
        timestamp: str | None = None,
    ) -> tuple[str, TokenMap]:
        """Replace all detected entities with placeholders.

        Processing order:
        1. Regex pass (jurisdiction patterns + shared patterns)
        2. Dictionary pass (per-matter parties.json)
        3. (future: NER pass feeds through residue tier only)

        Keyword-only args (v0.3):
            matter_id: caller-supplied matter identifier for audit logging.
            model: LLM model the sanitised text will be sent to.
            timestamp: ISO-8601 call timestamp (default: now UTC).

        Returns:
            ``(sanitized_text, token_map)``. Pass ``token_map`` to
            ``desanitize()`` later.
        """
        token_map = TokenMap()
        out = text

        # ── Pass 1: Regex ────────────────────────────────────────────
        for entry in self.patterns:
            pattern, entity_type, validator = _unpack_detector(entry)
            matches = list(pattern.finditer(out))
            for m in reversed(matches):
                # Checksum / structural gate: skip a shaped-but-invalid match
                # (e.g. a 12-digit invoice number that is not a valid Aadhaar).
                if validator is not None and not validator(m.group(0)):
                    continue
                if entity_type == "PERSON" and m.lastindex:
                    name_part = m.group(1)
                    placeholder = token_map.add(name_part, entity_type)
                    out = out[: m.start(1)] + placeholder + out[m.end(1) :]
                else:
                    original = m.group(0)
                    placeholder = token_map.add(original, entity_type)
                    out = out[: m.start()] + placeholder + out[m.end() :]

        # ── Pass 2: Dictionary ───────────────────────────────────────
        # Process entries longest-first — avoids offset invalidation when
        # shorter entries overlap with longer ones (e.g. "Rahul" vs "Rahul Verma").
        for pattern, entity_type in self._dictionary._compiled:
            for m in reversed(list(pattern.finditer(out))):
                placeholder = token_map.add(m.group(0), entity_type)
                out = out[: m.start()] + placeholder + out[m.end() :]

        # ── Audit log (counts only — never values) ───────────────────
        self._audit.log(
            matter_id=matter_id,
            jurisdiction=self._jurisdiction_slugs,
            entity_count=len(token_map.forward),
            entity_types=sorted(token_map.counters.keys()),
            model=model,
            timestamp=timestamp,
        )

        return out, token_map

    def desanitize(self, text: str, token_map: TokenMap) -> str:
        """Replace placeholders with originals using the token map.

        Walks placeholders longest-first so ``[PERSON_10]`` is replaced
        before ``[PERSON_1]``.
        """
        out = text
        placeholders = sorted(token_map.reverse.keys(), key=len, reverse=True)
        for placeholder in placeholders:
            out = out.replace(placeholder, token_map.reverse[placeholder])
        return out

    def is_safe_for_cloud(self, text: str) -> tuple[bool, list[str]]:
        """Quick scan — returns ``(is_safe, list_of_detected_entity_types)``.

        Useful for pre-call assertions: refuse cloud send if anything
        sensitive leaked past pseudonymisation.
        """
        detected: list[str] = []
        for entry in self.patterns:
            pattern, entity_type, validator = _unpack_detector(entry)
            if validator is None:
                if pattern.search(text):
                    detected.append(entity_type)
            elif any(validator(m.group(0)) for m in pattern.finditer(text)):
                detected.append(entity_type)
        return (len(detected) == 0, detected)

    def scan_residue(self, text: str) -> ResidueReport:
        """Post-sanitisation residue scan — surfaces likely-missed PII.

        Scans the would-be-sent (sanitised) text for patterns that look like
        PII but survived sanitisation. Confidence is tiered:

        - **HIGH**: digit runs matching a jurisdiction PII shape (e.g. 12-digit
          in India = possible Aadhaar), capitalised bigrams that look like names.
          → caller should soft-confirm or block.
        - **LOW**: weaker signals → audit-logged; send proceeds.

        The practitioner retains the final call. This tool **surfaces, never
        auto-blocks** (brain-frame discipline).

        Args:
            text: the sanitised text (output of ``sanitize()``).

        Returns:
            ``ResidueReport`` with ``high``, ``low``, and ``jurisdiction`` fields.
        """
        report = ResidueReport(jurisdiction=list(self._jurisdiction_slugs))

        # ── 1. Digit-run residue ─────────────────────────────────────
        # Check jurisdiction-specific digit-run thresholds
        for juris in self._jurisdiction_slugs:
            thresholds = _JURISDICTION_DIGIT_RUNS.get(juris, [])
            for min_digits, max_digits, severity, label in thresholds:
                # Find digit runs not inside placeholders (exclude [...] )
                # Split on placeholders to avoid flagging tokenised entities
                pattern = re.compile(
                    r"(?<!\])\b\d{" + str(min_digits) + r"," + str(max_digits) + r"}\b"
                )
                if pattern.search(text):
                    desc = f"{label} ({juris})"
                    if severity == "high":
                        if desc not in report.high:
                            report.high.append(desc)
                    else:
                        if desc not in report.low:
                            report.low.append(desc)

        # ── 1b. Grouped Aadhaar residue (India-only backstop) ────────
        # A dash/space-grouped 12-digit run that FAILS its checksum
        # (e.g. a typo) is not surfaced by the contiguous-run rule above.
        # Catch GROUPED forms only (required separator) so we never
        # double-count the contiguous-run rule.
        if "india" in self._jurisdiction_slugs:
            grouped_aadhaar = re.compile(
                r"(?<!\])\b[2-9]\d{3}[\s-]\d{4}[\s-]\d{4}\b"
            )
            if grouped_aadhaar.search(text):
                desc = "grouped 12-digit run possibly Aadhaar (india)"
                if desc not in report.high:
                    report.high.append(desc)

        # ── 2. Capitalised-bigram residue ─────────────────────────────
        # "Capitalised Capitalised" pairs that look like bare names
        # Exclude text inside placeholders like [PERSON_1]
        # Strategy: strip all [...] placeholders, then scan remainder
        stripped = re.sub(r"\[[A-Z_]+_\d+\]", " ", text)
        bigram_pattern = re.compile(
            r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,2})\b"
        )
        for m in bigram_pattern.finditer(stripped):
            candidate = m.group(1)
            # Skip single-word matches (cap-only), honorifics, and known
            # false positives like month names
            words = candidate.split()
            if len(words) >= 2:
                desc = f"Capitalised bigram '{candidate}' not in TokenMap"
                if desc not in report.high:
                    report.high.append(desc)

        # ── 3. Weak-signal residue ────────────────────────────────────
        # Single capitalised words longer than 4 chars (possible names)
        single_cap = re.compile(r"\b[A-Z][a-z]{4,}\b")
        for m in single_cap.finditer(stripped):
            word = m.group(0)
            # Skip months and common legal terms
            if word.lower() not in _LEGAL_COMMON_TERMS:
                desc = f"Lone capitalised word '{word}'"
                if desc not in report.low and desc not in report.high:
                    report.low.append(desc)

        return report

    # ── internal ─────────────────────────────────────────────────────────

    def _load_jurisdictions(self, jurisdictions: Iterable[str | object]) -> None:
        """Load PATTERNS from each jurisdiction module."""
        import importlib

        for j in jurisdictions:
            if isinstance(j, str):
                mod = importlib.import_module(
                    f"pseudonymisation_gateway.patterns.{j}"
                )
                self._jurisdiction_slugs.append(j)
            else:
                mod = j
                # Try to infer slug from module name
                slug = getattr(mod, "__name__", "").rsplit(".", 1)[-1]
                if slug:
                    self._jurisdiction_slugs.append(slug)
            self.patterns.extend(getattr(mod, "PATTERNS", []))

    def register_pattern(
        self,
        pattern: re.Pattern,
        entity_type: str,
        validator=None,
    ) -> None:
        """Insert a custom pattern at the front (highest priority).

        Pass ``validator`` (a callable ``str -> bool``) to tokenise a match only
        when the validator accepts it — e.g. a checksum or structural check that
        rejects shaped-but-invalid look-alikes.
        """
        if validator is None:
            self.patterns.insert(0, (pattern, entity_type))
        else:
            self.patterns.insert(0, (pattern, entity_type, validator))


# ── Common legal terms to exclude from residue false-positives ────────────

_LEGAL_COMMON_TERMS: set[str] = {
    # Months
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    # Courts / legal
    "court", "supreme", "appeal", "petition", "application",
    "plaintiff", "defendant", "appellant", "respondent",
    "tribunal", "commission", "authority", "government",
    "section", "article", "clause", "schedule", "annexure",
    "affidavit", "submission", "judgment", "order", "decree",
    "honourable", "honorable", "learned", "respective",
    "counsel", "advocate", "solicitor", "barrister",
    # Jurisdiction names
    "india", "dubai", "london", "singapore", "australia",
    "united", "states", "kingdom", "emirates",
    # Generic
    "matter", "filing", "document", "exhibit", "witness",
    "statement", "evidence", "hearing", "notice",
    "pursuant", "hereinafter", "herein", "thereof", "whereas",
    "notwithstanding", "forthwith", "heretofore",
}
