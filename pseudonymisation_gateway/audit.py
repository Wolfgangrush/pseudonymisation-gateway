"""Per-call audit log — append-only JSONL, COUNTS ONLY, never values.

Design principles (SECURITY-CRITICAL):
- **COUNTS ONLY.** No original string — no name, ID, placeholder original, or
  residue *value* — may EVER be written to the log. The audit log contains
  entity counts, entity-type labels, residue-count aggregates, and metadata.
- **Opt-in.** ``audit_log_path`` defaults to ``None``; no log is written unless
  the caller explicitly provides a path.
- **Append-only JSONL.** Each ``.log()`` call writes one JSON line. No
  read-modify-write, no in-place update.

Entry schema (per line)::

    {
      "matter_id": "M-2024-001",
      "jurisdiction": ["india", "uae"],
      "entity_count": 5,
      "entity_types": ["PERSON", "AADHAAR", "PAN", "EMAIL", "ORG"],
      "residue_result": {"high_n": 1, "low_n": 2},
      "model": "claude-sonnet-4-6",
      "timestamp": "2026-06-17T12:00:00+00:00"
    }
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import ResidueReport


@dataclass
class AuditLogger:
    """Append-only JSONL audit log. Counts only — never stores original values.

    Args:
        path: filesystem path for the JSONL log file. If ``None``, ``.log()``
            is a no-op.
    """

    path: str | None = None

    # ── public API ───────────────────────────────────────────────────────

    def log(
        self,
        *,
        matter_id: str | None,
        jurisdiction: list[str],
        entity_count: int,
        entity_types: list[str],
        residue_report: ResidueReport | None = None,
        model: str | None = None,
        timestamp: str | None = None,
    ) -> None:
        """Write one audit entry.

        Args:
            matter_id: caller-supplied matter identifier. May be ``None``.
            jurisdiction: active jurisdiction slugs at call time.
            entity_count: total number of entities in the TokenMap.
            entity_types: list of entity-type labels (e.g. ``["PERSON","PAN"]``).
            residue_report: optional ``ResidueReport`` from ``scan_residue()``.
                Only ``high_n`` and ``low_n`` counts are logged — residue
                **values** are NEVER written.
            model: optional LLM model identifier (e.g. ``"claude-sonnet-4-6"``).
            timestamp: ISO-8601 string. If ``None``, uses ``datetime.now(timezone.utc)``.
        """
        if self.path is None:
            return

        ts = timestamp or datetime.now(timezone.utc).isoformat()

        residue_counts: dict[str, int] = {}
        if residue_report is not None:
            residue_counts = {
                "high_n": len(residue_report.high),
                "low_n": len(residue_report.low),
            }

        entry: dict = {
            "matter_id": matter_id,
            "jurisdiction": jurisdiction,
            "entity_count": entity_count,
            "entity_types": entity_types,
            "residue_result": residue_counts,
            "model": model,
            "timestamp": ts,
        }

        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
