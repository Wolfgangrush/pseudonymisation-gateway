#!/usr/bin/env python3
"""Mini (ornith-9b) contribution to the benchmark — on-box, zero egress.

Two bulk-generation jobs the local model is good at, both hard-gated by code I
own so the model's ~16% hallucination can never corrupt the corpus:

  1. Realistic neutral document snippets with a {{PII}} slot + date/amount/name
     distractors -> splice gold VALID identifiers in -> tests RECALL-IN-CONTEXT
     (does the detector still fire when the ID is buried in noisy real text?).
  2. Adversarial look-alike strings -> run through the gateway's OWN validators
     -> keep ONLY those every validator rejects -> true NEGATIVES that test
     PRECISION (detector must stay silent).

Output: corpus_context.jsonl
"""
from __future__ import annotations
import json, os, re, random, urllib.request

random.seed(20260628)
HERE = os.path.dirname(os.path.abspath(__file__))
GW = os.path.abspath(os.path.join(HERE, ".."))
import sys; sys.path.insert(0, GW)
from pseudonymisation_gateway.patterns.india import aadhaar_validate, gstin_validate
from pseudonymisation_gateway.patterns._checksums import iban_validate, nric_validate, itin_validate

MINI = os.environ.get("MINI_ENDPOINT", "http://localhost:1346/v1/chat/completions")
MODEL = "ornith-1.0-9b"

def ornith(prompt, max_tokens=1400, retries=3):
    """Call ornith with the </think> prefill fix; assert finish_reason==stop."""
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt},
                     {"role": "assistant", "content": "</think>\n\n"}],
        "max_tokens": max_tokens, "temperature": 0.4,
    }).encode()
    last = None
    for a in range(retries):
        try:
            req = urllib.request.Request(MINI, data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            c = d["choices"][0]
            if c["finish_reason"] != "stop":
                raise RuntimeError(f"finish={c['finish_reason']} (truncated/thinking)")
            return c["message"]["content"]
        except Exception as e:
            last = e
    raise RuntimeError(f"ornith failed: {last}")

def extract_json_array(txt):
    """Pull the first JSON array of strings out of a model reply."""
    m = re.search(r"\[.*\]", txt, re.DOTALL)
    if not m:
        return []
    try:
        arr = json.loads(m.group())
        return [x for x in arr if isinstance(x, str)]
    except Exception:
        return re.findall(r'"([^"]{3,200})"', m.group())

# ── 1. realistic context templates ────────────────────────────────────────
TEMPLATE_PROMPT = (
    "You generate test fixtures for a privacy-redaction tool. Produce {n} short, "
    "realistic one-line document snippets (KYC notes, bank onboarding lines, "
    "invoice rows, HR records, court-filing lines, email sign-offs). Each MUST "
    "contain the EXACT literal token {{PII}} exactly once, where a sensitive "
    "identifier value would sit. Use NEUTRAL surrounding wording (do NOT name a "
    "specific ID type) so any identifier fits the slot. Sprinkle realistic "
    "DISTRACTORS around it — a date, a rupee amount, a person name, a reference "
    "number — to stress the detector. Return ONLY a JSON array of strings, no prose."
)

templates = []
for i in range(3):  # bounded reduce, not a while-loop
    try:
        out = ornith(TEMPLATE_PROMPT.replace("{n}", "22"))
        got = [t for t in extract_json_array(out) if "{{PII}}" in t]
        templates.extend(got)
        print(f"[templates] call {i+1}: +{len(got)} (total {len(templates)})")
    except Exception as e:
        print(f"[templates] call {i+1} failed: {e}")
seen = set(); templates = [t for t in templates if not (t in seen or seen.add(t))]
print(f"[templates] usable: {len(templates)}")

gold = [json.loads(l) for l in open(os.path.join(HERE, "corpus_gold.jsonl"), encoding="utf-8")]
valids = [g for g in gold if g["klass"] == "valid"]

ROWS = []
def add(text, typ, expect, klass, note):
    ROWS.append({"id": len(ROWS), "text": text, "type": typ,
                 "expect_detect": expect, "klass": klass,
                 "source": "mini+gold", "note": note})

if templates:
    for g in valids:
        tmpl = random.choice(templates)
        add(tmpl.replace("{{PII}}", g["text"]), g["type"], True, "valid-in-context",
            f"{g['type']} {g['variant']} embedded in mini-generated context")

# ── 2. adversarial look-alikes, checksum-gated ─────────────────────────────
ADV_PROMPT = (
    "You generate NEGATIVE test cases for a PII detector. Produce {n} strings "
    "that LOOK like an Indian Aadhaar (12 digits), an Indian GSTIN (15 chars), "
    "or an international IBAN, but are DEFINITELY NOT valid ones — e.g. a 12-digit "
    "invoice/order/timestamp number, a GSTIN-shaped string with a wrong check "
    "character, an IBAN-shaped run whose check digits don't reconcile. These are "
    "decoys a good detector must IGNORE. Return ONLY a JSON array of strings."
)
def any_validator_accepts(s):
    cand = s.strip()
    digits = re.sub(r"\D", "", cand)
    checks = [
        aadhaar_validate(cand), gstin_validate(cand), iban_validate(cand),
        nric_validate(cand), itin_validate(cand),
    ]
    if len(digits) == 12:
        checks.append(aadhaar_validate(digits))
    return any(checks)

adv_kept = 0
for i in range(2):
    try:
        out = ornith(ADV_PROMPT.replace("{n}", "20"))
        for s in extract_json_array(out):
            s = s.strip()
            if 6 <= len(s) <= 40 and not any_validator_accepts(s):
                add(s, "LOOKALIKE_MIXED", False, "lookalike-mini",
                    "mini decoy; checksum-gated to confirm no validator accepts it")
                adv_kept += 1
        print(f"[adversarial] call {i+1}: kept {adv_kept} so far")
    except Exception as e:
        print(f"[adversarial] call {i+1} failed: {e}")

OUT = os.path.join(HERE, "corpus_context.jsonl")
with open(OUT, "w", encoding="utf-8") as f:
    for r in ROWS:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"wrote {len(ROWS)} context rows -> {OUT}")
print(f"  valid-in-context: {sum(1 for r in ROWS if r['klass']=='valid-in-context')}")
print(f"  mini lookalikes : {sum(1 for r in ROWS if r['klass']=='lookalike-mini')}")
