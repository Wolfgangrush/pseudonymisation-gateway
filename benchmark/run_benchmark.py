#!/usr/bin/env python3
"""Two-sided detector benchmark for the pseudonymisation-gateway.

RECALL  : every VALID identifier (bare + real-world variant + buried in
          mini-generated document context) MUST be detected — else it would be
          silently shipped to a cloud LLM.
PRECISION: every shaped-but-INVALID look-alike MUST be ignored — else the tool
          over-redacts and erodes trust.

Where the regex detector misses a valid variant, we additionally check the
residue scanner — the gateway's recall safety net — so the finding is fair:
"detector regex misses X, but residue flags it, so it is not silently sent."

Outputs: benchmark_results.json + BENCHMARK_REPORT.md
"""
from __future__ import annotations
import json, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
GW = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, GW)
from pseudonymisation_gateway import PseudonymisationGateway

JURIS = ["india", "usa", "eu", "uk", "australia", "singapore", "uae"]
gw = PseudonymisationGateway(jurisdictions=JURIS, include_shared=True)

# The gateway tags some identifiers under jurisdiction-specific entity types.
# Map the benchmark's coarse type onto the set the gateway may legitimately emit,
# so a correct detection under UK_IBAN/FIN is not mis-scored as a recall miss.
TYPE_ALIASES = {
    "IBAN": {"IBAN", "UK_IBAN", "UAE_IBAN", "EU_IBAN"},
    "NRIC": {"NRIC", "FIN"},
}
def alias(t):
    return TYPE_ALIASES.get(t, {t})

def load(name):
    p = os.path.join(HERE, name)
    return [json.loads(l) for l in open(p, encoding="utf-8")] if os.path.exists(p) else []

rows = load("corpus_gold.jsonl") + load("corpus_context.jsonl")

recall_by_type = collections.defaultdict(lambda: [0, 0])   # type -> [caught, total]
prec = [0, 0]                                              # [correctly_ignored, total_neg]
misses, leaks = [], []

for r in rows:
    text, typ, expect = r["text"], r["type"], r["expect_detect"]
    safe, detected = gw.is_safe_for_cloud(text)
    if expect:  # positive — recall
        caught = bool(alias(typ) & set(detected))
        recall_by_type[typ][1] += 1
        if caught:
            recall_by_type[typ][0] += 1
        else:
            # consult the residue safety net
            res = gw.scan_residue(text)
            saved_by_residue = bool(getattr(res, "high", None))
            misses.append({"text": text, "type": typ, "variant": r.get("variant", ""),
                           "note": r.get("note", ""), "residue_high": saved_by_residue})
    else:       # negative — precision
        prec[1] += 1
        if typ == "LOOKALIKE_MIXED":
            leaked = not safe
        else:
            leaked = bool(alias(typ) & set(detected))
        if leaked:
            leaks.append({"text": text, "type": typ, "variant": r.get("variant", ""),
                          "detected": detected, "note": r.get("note", "")})
        else:
            prec[0] += 1

# ── aggregate ──────────────────────────────────────────────────────────────
tot_pos = sum(v[1] for v in recall_by_type.values())
tot_caught = sum(v[0] for v in recall_by_type.values())
overall_recall = tot_caught / tot_pos if tot_pos else 1.0
overall_prec = prec[0] / prec[1] if prec[1] else 1.0
residue_saved = sum(1 for m in misses if m["residue_high"])

results = {
    "jurisdictions": JURIS,
    "totals": {"rows": len(rows), "positives": tot_pos, "negatives": prec[1]},
    "recall": {"overall": round(overall_recall, 4), "caught": tot_caught, "total": tot_pos,
               "by_type": {k: {"caught": v[0], "total": v[1],
                               "recall": round(v[0]/v[1], 4)} for k, v in sorted(recall_by_type.items())}},
    "precision_on_negatives": {"overall": round(overall_prec, 4),
                               "correctly_ignored": prec[0], "total": prec[1]},
    "recall_misses": misses,
    "residue_safety_net_caught": residue_saved,
    "precision_leaks": leaks,
}
json.dump(results, open(os.path.join(HERE, "benchmark_results.json"), "w"), indent=2, ensure_ascii=False)

# ── report ──────────────────────────────────────────────────────────────────
L = []
L.append("# Pseudonymisation-Gateway — Two-Sided Detector Benchmark\n")
L.append("_Generated on-box (Mac mini ornith-9b + nomic) · zero egress · "
         "checksums minted & verified by deterministic code, not the LLM._\n")
L.append(f"**Jurisdictions loaded:** {', '.join(JURIS)}  ·  **shared patterns:** on\n")
L.append(f"**Corpus:** {len(rows)} rows — {tot_pos} valid positives, {prec[1]} look-alike negatives\n")
L.append("\n## Headline\n")
L.append(f"| Axis | Score | |")
L.append(f"|---|---|---|")
L.append(f"| **Recall** (valid IDs caught) | **{overall_recall:.1%}** | {tot_caught}/{tot_pos} |")
L.append(f"| **Precision** (look-alikes ignored) | **{overall_prec:.1%}** | {prec[0]}/{prec[1]} |")
L.append(f"| Residue net caught of the recall misses | {residue_saved}/{len(misses)} | safety tier |")

L.append("\n## Recall by identifier type\n")
L.append("| Type | Recall | Caught/Total |")
L.append("|---|---|---|")
for k, v in sorted(recall_by_type.items()):
    L.append(f"| {k} | {v[0]/v[1]:.0%} | {v[0]}/{v[1]} |")

L.append("\n## Recall misses (detector regex did NOT fire)\n")
if not misses:
    L.append("_None._\n")
else:
    L.append("| Type | Variant | Caught by residue net? | Sample |")
    L.append("|---|---|---|---|")
    for m in misses:
        net = "✅ yes (HIGH)" if m["residue_high"] else "❌ NO — silent send risk"
        L.append(f"| {m['type']} | {m['variant']} | {net} | `{m['text'][:48]}` |")

L.append("\n## Precision leaks (detector fired on a look-alike)\n")
if not leaks:
    L.append("_None — every shaped-but-invalid decoy was correctly ignored._\n")
else:
    L.append("| Type | Variant | Detected as | Sample |")
    L.append("|---|---|---|---|")
    for lk in leaks:
        L.append(f"| {lk['type']} | {lk['variant']} | {lk['detected']} | `{lk['text'][:48]}` |")

L.append("\n## How to reproduce\n")
L.append("```bash\npython3 gold_generator.py        # deterministic gold (checksums)\n"
         "python3 build_context_mini.py    # mini adds realistic context (on-box)\n"
         "python3 run_benchmark.py         # this report\n```\n")
open(os.path.join(HERE, "BENCHMARK_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))

print(f"recall {overall_recall:.1%} ({tot_caught}/{tot_pos})  "
      f"precision {overall_prec:.1%} ({prec[0]}/{prec[1]})")
print(f"recall misses: {len(misses)} (residue caught {residue_saved})  precision leaks: {len(leaks)}")
print("wrote BENCHMARK_REPORT.md + benchmark_results.json")
