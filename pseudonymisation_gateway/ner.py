"""Optional NER pass — spaCy-backed entity extraction for low-confidence surfacing.

Design principles:
- **Optional only.** ``spaCy`` and ``en_core_web_sm`` are NEVER hard dependencies.
  If not installed, one warning is logged and the pipeline runs without NER.
- **Lazy import.** spaCy is imported only when ``NERSanitiser`` is instantiated.
- **Lower confidence than dictionary/regex.** NER hits are surfaced through the
  residue tier (``scan_residue()``) — they are NOT automatically redacted.
- **Release gate passes WITHOUT spaCy.** All tests MUST pass when spaCy is absent.

Usage::

    from pseudonymisation_gateway.ner import NERSanitiser
    ner = NERSanitiser()  # logs warning if spaCy missing, otherwise loads en_core_web_sm
    entities = ner.extract_entities("Rahul Verma filed the petition at Delhi High Court.")
    # → [("Rahul Verma", "PERSON"), ("Delhi High Court", "ORG")]
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class NERSanitiser:
    """Optional spaCy-backed named-entity recognition.

    Instantiating this class attempts to load ``en_core_web_sm``. If spaCy or
    the model is not installed, a single warning is emitted and ``available``
    is set to ``False``. All subsequent calls to ``extract_entities()`` return
    an empty list.
    """

    def __init__(self) -> None:
        self._nlp = None
        self.available = False
        try:
            import spacy  # noqa: F811 — lazy import; only runs on instantiation
        except ImportError:
            logger.warning(
                "spaCy is not installed — NER pass skipped. "
                "Install with: pip install pseudonymisation-gateway[ner]"
            )
            return
        try:
            self._nlp = spacy.load("en_core_web_sm")
            self.available = True
        except OSError:
            logger.warning(
                "spaCy model 'en_core_web_sm' not found — NER pass skipped. "
                "Install with: python -m spacy download en_core_web_sm"
            )

    # ── public API ───────────────────────────────────────────────────────

    def extract_entities(self, text: str) -> list[tuple[str, str]]:
        """Extract PERSON / ORG / GPE from text using spaCy NER.

        Args:
            text: raw or partially-sanitised text.

        Returns:
            list of ``(entity_text, entity_type)`` where entity_type is one of
            ``PERSON``, ``ORG``, ``GPE``. Empty list if spaCy is unavailable.
        """
        if not self.available or self._nlp is None:
            return []
        doc = self._nlp(text)
        results: list[tuple[str, str]] = []
        for ent in doc.ents:
            if ent.label_ in ("PERSON", "ORG", "GPE"):
                results.append((ent.text, ent.label_))
        return results
