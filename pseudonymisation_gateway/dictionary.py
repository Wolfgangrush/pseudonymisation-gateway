"""Per-matter parties.json dictionary — catches bare names the regex pass misses.

Design principles:
- In-RAM only: dictionary contents are loaded from a JSON file but NEVER re-written
  to disk by the library. The JSON is caller-supplied (typically case-file scoped).
- Jurisdiction-aware: the JSON may scope entries by jurisdiction key. If scoped,
  only entries for the gateway's active jurisdictions + a shared ``"*"`` bucket are
  loaded. If unscoped (flat entity-type keys), all entries load.
- Longest-match-first: ``"Rahul Verma"`` tokenises before ``"Rahul"``.
- Exact + case-insensitive + whole-word (word-boundary) matching.
- Reuses the existing ``TokenMap.add(original, entity_type)`` scheme so placeholder
  numbering stays consistent with regex hits.

JSON format (flat — loaded regardless of jurisdiction)::

    {
      "PERSON": ["Rahul Verma", "Sunita Rao"],
      "ORG": ["Acme Foods Pvt Ltd"]
    }

JSON format (jurisdiction-scoped — only active jurisdictions + "*" loaded)::

    {
      "india": {
        "PERSON": ["Rahul Verma"],
        "ORG": ["Acme Foods Pvt Ltd"]
      },
      "uk": {
        "PERSON": ["John Smith"]
      },
      "*": {
        "ORG": ["Cross-border Corp"]
      }
    }
"""

from __future__ import annotations

import json
import re
from typing import Iterable


class PartiesDictionary:
    """In-RAM dictionary of known entities for a single matter.

    Args:
        parties_file: path to a JSON file (see module docstring for format).
        active_jurisdictions: if the JSON is jurisdiction-scoped, only entries
            under these jurisdiction keys (plus ``"*"``) are loaded.
    """

    def __init__(
        self,
        parties_file: str | None = None,
        active_jurisdictions: Iterable[str] = (),
    ) -> None:
        # entries: list of (original, entity_type) sorted longest-original-first
        self.entries: list[tuple[str, str]] = []
        # _compiled: list of (re.Pattern, entity_type) — one per entry for
        #            case-insensitive whole-word matching
        self._compiled: list[tuple[re.Pattern, str]] = []
        if parties_file is not None:
            self._load(parties_file, active_jurisdictions)

    # ── public API ───────────────────────────────────────────────────────

    def match(self, text: str) -> list[tuple[str, str, int, int]]:
        """Find all dictionary entries in *text*.

        Returns:
            list of ``(original, entity_type, start, end)``, longest-match-first
            so callers can substitute in order without partial-overlap issues.
            Entries already replaced with placeholders in a prior pass won't
            appear because the original text has changed.
        """
        matches: list[tuple[str, str, int, int]] = []
        for pattern, entity_type in self._compiled:
            for m in pattern.finditer(text):
                matches.append((m.group(0), entity_type, m.start(), m.end()))
        # Sort longest-match-first (by match length descending)
        matches.sort(key=lambda x: x[3] - x[2], reverse=True)
        return matches

    # ── internal ─────────────────────────────────────────────────────────

    def _load(
        self,
        path: str,
        active_jurisdictions: Iterable[str],
    ) -> None:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)

        entries: list[tuple[str, str]] = []
        jurisdictions = set(active_jurisdictions)
        jurisdictions.add("*")  # shared bucket always loaded

        # Detect: jurisdiction-scoped vs flat
        first_val = next(iter(raw.values()), None)
        if isinstance(first_val, dict):
            # Jurisdiction-scoped
            for juris_key, entity_map in raw.items():
                if juris_key in jurisdictions:
                    for entity_type, names in entity_map.items():
                        for name in names:
                            entries.append((str(name), str(entity_type)))
        else:
            # Flat — load everything
            for entity_type, names in raw.items():
                for name in names:
                    entries.append((str(name), str(entity_type)))

        # Deduplicate while preserving order (first occurrence wins)
        seen: set[tuple[str, str]] = set()
        deduped: list[tuple[str, str]] = []
        for orig, etype in entries:
            key = (orig.lower(), etype)
            if key not in seen:
                seen.add(key)
                deduped.append((orig, etype))

        # Sort longest-original-first so "Rahul Verma" before "Rahul"
        deduped.sort(key=lambda x: len(x[0]), reverse=True)
        self.entries = deduped

        # Compile one regex per entry — whole-word, case-insensitive
        self._compiled = []
        for original, entity_type in self.entries:
            pattern = re.compile(
                r"\b" + re.escape(original) + r"\b",
                re.IGNORECASE,
            )
            self._compiled.append((pattern, entity_type))
