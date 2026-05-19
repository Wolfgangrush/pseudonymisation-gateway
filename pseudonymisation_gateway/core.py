"""Core engine — TokenMap + PseudonymisationGateway.

Design principles:
- Session-scoped: each gateway instance = one user session
- In-memory only: TokenMap NEVER persisted to disk
- Deterministic: same entity within one session → same placeholder
- Extensible: register_pattern() to add custom patterns per matter
- Jurisdiction-aware: patterns loaded per country via patterns.<country> modules

Architecture:

    USER INPUT (with real names, IDs, etc.)
           │
           ▼
    Regex pass (priority-ordered)
           │
           ▼
    Placeholders inserted: [PERSON_1], [EMIRATES_ID_1], etc.
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


class PseudonymisationGateway:
    """Strips PII from text before cloud-API send; restores on return.

    Args:
        jurisdictions: list of jurisdiction modules (or string slugs) to load patterns from.
                       Each module must expose a PATTERNS list of (re.Pattern, entity_type) tuples.
                       String slugs are resolved via `pseudonymisation_gateway.patterns.<slug>`.
        include_shared: whether to include cross-jurisdiction shared patterns (email, name,
                        date). Default True.

    Example — UAE-only:
        from pseudonymisation_gateway import PseudonymisationGateway
        gw = PseudonymisationGateway(jurisdictions=["uae"])

    Example — UAE + Indian diaspora:
        gw = PseudonymisationGateway(jurisdictions=["uae", "india"])

    Example — custom pattern at runtime:
        import re
        gw.register_pattern(re.compile(r"DRC-\\d{6}"), "DUBAI_REAL_ESTATE_CASE")
    """

    def __init__(
        self,
        jurisdictions: Iterable[str | object] = (),
        include_shared: bool = True,
    ) -> None:
        self.patterns: list[tuple[re.Pattern, str]] = []
        self._load_jurisdictions(jurisdictions)
        if include_shared:
            from . import shared
            self.patterns.extend(shared.PATTERNS)

    def _load_jurisdictions(self, jurisdictions: Iterable[str | object]) -> None:
        """Load PATTERNS from each jurisdiction module."""
        import importlib

        for j in jurisdictions:
            if isinstance(j, str):
                mod = importlib.import_module(
                    f"pseudonymisation_gateway.patterns.{j}"
                )
            else:
                mod = j
            self.patterns.extend(getattr(mod, "PATTERNS", []))

    def register_pattern(self, pattern: re.Pattern, entity_type: str) -> None:
        """Insert a custom pattern at the front (highest priority)."""
        self.patterns.insert(0, (pattern, entity_type))

    def sanitize(self, text: str) -> tuple[str, TokenMap]:
        """Replace all detected entities with placeholders.

        Returns:
            (sanitized_text, token_map). Pass `token_map` to `desanitize()` later.
        """
        token_map = TokenMap()
        out = text
        for pattern, entity_type in self.patterns:
            matches = list(pattern.finditer(out))
            # Walk matches in reverse so offsets don't break as we substitute
            for m in reversed(matches):
                # Name patterns use a capture group for the name part (preserving honorific)
                if entity_type == "PERSON" and m.lastindex:
                    name_part = m.group(1)
                    placeholder = token_map.add(name_part, entity_type)
                    out = out[: m.start(1)] + placeholder + out[m.end(1) :]
                else:
                    original = m.group(0)
                    placeholder = token_map.add(original, entity_type)
                    out = out[: m.start()] + placeholder + out[m.end() :]
        return out, token_map

    def desanitize(self, text: str, token_map: TokenMap) -> str:
        """Replace placeholders with originals using the token map.

        Walks placeholders longest-first so [PERSON_10] is replaced before [PERSON_1].
        """
        out = text
        # Sort by placeholder length descending — prevents [PERSON_1] eating [PERSON_10]
        placeholders = sorted(token_map.reverse.keys(), key=len, reverse=True)
        for placeholder in placeholders:
            out = out.replace(placeholder, token_map.reverse[placeholder])
        return out

    def is_safe_for_cloud(self, text: str) -> tuple[bool, list[str]]:
        """Quick scan — returns (is_safe, list_of_detected_entity_types).

        Useful for pre-call assertions: refuse cloud send if anything sensitive
        leaked past pseudonymisation.
        """
        detected: list[str] = []
        for pattern, entity_type in self.patterns:
            if pattern.search(text):
                detected.append(entity_type)
        return (len(detected) == 0, detected)
