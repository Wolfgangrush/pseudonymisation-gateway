# 🛡️ pseudonymisation-gateway

> **Jurisdiction-aware PII pseudonymisation middleware for legal-tech tools using cloud LLMs.**
>
> Strips client PII before any cloud-API call, restores it in the response. Session-scoped. In-memory only. Token map never persisted.
>
> MIT licensed · Open infrastructure for the legal-technology community.

---

## ⚠️ Why this exists

The Wolfgang Rush **AI Law Firm** family (7 country firms · India · UAE · UK · USA · EU · Singapore · Australia) + 14 Indian-litigation drafting plugins are designed as **dual-mode** legal-tech tools:

- **🥇 Local-first by default** — the `connect-local` command in each AI Law Firm configures Ollama + Qwen3 to run the language model on the user's laptop. In this configuration, no prompt ever leaves the machine; the Gateway is not invoked because there is no cross-vendor transmission to firewall.
- **🥈 / 🥉 Cloud-LLM optional** — for users who choose to opt into Claude / Gemini / DeepSeek for quality reasons, the AI Law Firm wires this library in front of every outbound prompt. The Gateway is the bridge architecture that makes cloud-mode defensible for client-confidential work.

The architectural problem this library solves shows up the moment a solicitor opts into cloud mode:

**Without a pseudonymisation layer, the moment a solicitor points a cloud-AI legal tool at a real matter, client PII goes to the cloud LLM in cleartext.**

A solicitor asks the LLM to draft a witness statement. The prompt contains the client's real name, NRIC, NI Number, Emirates ID, Aadhaar, case file numbers. The cloud vendor gets all of it. Stored in their training pipeline. Logged. Subpoena-able.

Existing solutions:
- **Microsoft Presidio** — solid, but optimised for US/EU PII patterns. No coverage for Emirates ID, NRIC, TFN, Aadhaar, Indian GSTIN.
- **AWS/Google/Azure DLP APIs** — paid, cloud-dependent (the very thing we're trying to avoid), and the same Western-jurisdiction blind spots.
- **Roll your own regex** — every legal-tech project re-solving the same problem badly.

So I built this as the privacy primitive that closes the gap when cloud mode is invoked. It ships as the integration layer across **22 Wolfgang Rush legal-tech repos** — so anyone opting into cloud mode on any of those tools is firewalled by Gateway sanitisation before any prompt leaves their machine.

**The boundary this library does NOT cross:** the Gateway sanitisation does not transform a cloud-LLM tool into an "architecturally local" tool. The data still leaves the machine — what crosses the border is structurally pseudonymised, which is materially stronger than raw transmission but is not equivalent to zero transmission. Users with sensitivity ceilings that require zero cross-border data flow (e.g. Section 77 Australian My Health Records data; UAE PDPL Article 22 restricted categories; certain UK GDPR Schedule 21 special-category data) should use the Local-Ollama tier instead.

---

## 🎯 What it does

```python
from pseudonymisation_gateway import PseudonymisationGateway

gw = PseudonymisationGateway(jurisdictions=["uae", "india"])  # Dubai firm + Indian diaspora

original = "Mr. Khalid Al-Mansoori (Emirates ID 784-1985-1234567-8) is acting for Mr. Rahul Sharma (Aadhaar 1234 5678 9012)."

clean, token_map = gw.sanitize(original)
# clean now: "Mr. [PERSON_1] (Emirates ID [EMIRATES_ID_1]) is acting for Mr. [PERSON_2] (Aadhaar [AADHAAR_1])."

# safe to send to cloud LLM
response = anthropic_client.messages.create(messages=[{"role": "user", "content": clean}])

# restore real names in the LLM completion
real = gw.desanitize(response.content[0].text, token_map)
# real now contains "Khalid Al-Mansoori" and "Rahul Sharma" again
```

---

## 🌐 Jurisdiction coverage (v0.1.0)

| Country | Patterns covered |
|---|---|
| 🇮🇳 **India** | Aadhaar · PAN · GSTIN · IFSC · ₹ amounts · Indian phone · FIR · vehicle registration · case numbers |
| 🇦🇪 **UAE** | Emirates ID · UAE IBAN · Trade License (Dubai Economy · DIFC · IFZA · DMCC · JAFZA · DAFZA) · DIFC Court case nums (CFI · CA · SCT) · Cassation case nums · UAE phone · AED amounts |
| 🇦🇺 **Australia** | TFN · Medicare · ABN · ACN · BSB · AU phone (+61) · AUD amounts · HCA / FCA / FCAFC / state Supreme Court case nums |
| 🇬🇧 **UK** | NI Number · NHS Number · UTR · UK VAT · UK IBAN · UK phone (+44) · GBP amounts · EWHC / EWCA / UKSC case nums |
| 🇺🇸 **USA** | SSN · ITIN · EIN · US phone · USD amounts · driver license · Federal docket numbers |
| 🇪🇺 **EU** | IBAN (27 member states) · EU VAT · EORI · German Steuer-ID · French INSEE · Italian Codice Fiscale · CJEU case nums · EUR amounts |
| 🇸🇬 **Singapore** | NRIC · FIN · UEN · CPF · SG phone (+65) · SGD amounts · SGCA / SGHC / SGDC case nums |

Plus **shared cross-jurisdiction patterns**: email · honorific-driven names · ISO dates · bank account heuristics · generic Common-Law case numbers.

See [JURISDICTIONS.md](JURISDICTIONS.md) for the per-country pattern catalog + how to extend.

---

## 🌍 Diaspora coverage (the cross-jurisdiction insight)

The 6 non-India country firms layer **Indian PII detection** alongside their country-native patterns. Why:

- Dubai has **~3.4M Indian residents** (largest expat group)
- USA has **~5.4M Indian-Americans**
- UK has **~1.9M British-Indian**
- Australia has **~1M Indian-Australians**
- EU has **~2M Indian-diaspora** (UK pre-Brexit · Germany · France · NL · others)
- Singapore is **~9.2% Indian** (citizens + PRs + workers)

A solicitor in Dubai handling an Indian-expat client matter benefits from BOTH Emirates ID detection AND Aadhaar detection in the same gateway. Existing tools force you to choose one jurisdiction's PII map — leaving the other invisible.

Same principle applies for other diasporas (Chinese in SG · Pakistani in UK · Mexican in USA · etc.) — extensible via the same per-country module pattern.

---

## 📦 Install

```bash
pip install git+https://github.com/Wolfgangrush/pseudonymisation-gateway.git
```

Python 3.10+. Zero runtime dependencies (uses stdlib `re` only).

---

## 🚀 Quick start

### Single jurisdiction

```python
from pseudonymisation_gateway import PseudonymisationGateway

gw = PseudonymisationGateway(jurisdictions=["uk"])
clean, tm = gw.sanitize("Client AB123456C lives in Manchester.")
# → "Client [NI_NUMBER_1] lives in Manchester."
```

### Multi-jurisdiction (diaspora)

```python
gw = PseudonymisationGateway(jurisdictions=["uae", "india"])
clean, tm = gw.sanitize("UAE client + Indian-expat partner matter.")
```

### Pre-flight safety check

```python
safe, detected = gw.is_safe_for_cloud(user_text)
if not safe:
    raise ValueError(f"PII leaked past sanitize(): {detected}")
# only safe text goes to cloud
```

### Custom patterns at runtime

```python
import re
gw.register_pattern(re.compile(r"MATTER-\d{6}"), "FIRM_MATTER_ID")
# now all your firm's matter IDs get scrubbed too
```

### Round-trip with Claude API

```python
import anthropic
from pseudonymisation_gateway import PseudonymisationGateway

gw = PseudonymisationGateway(jurisdictions=["uk"])
client = anthropic.Anthropic()

# 1. Sanitize before send
clean, token_map = gw.sanitize(user_input)

# 2. Send sanitized text only
resp = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": clean}],
)

# 3. Restore real names in response
final = gw.desanitize(resp.content[0].text, token_map)
```

See `examples/` for OpenAI · Gemini · multi-turn-conversation patterns.

---

## 🏗️ Architecture (60-second version)

```
USER INPUT (real names, IDs, etc.)
       │
       ▼
PseudonymisationGateway.sanitize()
   │
   ├─→ Priority-ordered regex pass (country-specific first, then shared)
   ├─→ Each match → TokenMap.add(original, entity_type) → "[TYPE_N]" placeholder
   └─→ Returns (clean_text, token_map)
       │
       ▼
Cloud LLM API call (sees only placeholders)
       │
       ▼
LLM response (placeholders preserved across the round-trip)
       │
       ▼
PseudonymisationGateway.desanitize(response, token_map)
       │
       ├─→ Walks placeholders longest-first ([PERSON_10] before [PERSON_1])
       └─→ Replaces each with original
       │
       ▼
USER SEES restored text + LLM completion
```

**Key properties:**

- **Session-scoped** — each `PseudonymisationGateway()` is one session. New instance = fresh token map.
- **In-memory only** — token map exists only in Python memory. Never written to disk. Destroyed when the gateway goes out of scope.
- **Deterministic** — same entity within one session → same placeholder. `[PERSON_1]` stays `[PERSON_1]` if "John Smith" appears 10 times in the same conversation.
- **Extensible** — `register_pattern()` adds custom patterns at the front of the priority list.
- **Jurisdiction-agnostic by default** — load only the country modules you need.

Full deep-dive: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 📊 Comparison with prior art

I built on the shoulders of:
- **GDPR Article 4(5)** — the legal definition of "pseudonymisation" in EU law (2018)
- **DPDP Act 2023** — India's adoption of the same framework
- **Microsoft Presidio** — open-source PII detection + anonymization, the gold standard since 2018
- **AWS Comprehend PII** · **Google DLP** · **Azure AI Language PII** — cloud-vendor services with similar capabilities
- Two decades of academic work on differential privacy, k-anonymity, and tokenization

What this library adds:
1. **Per-jurisdiction modular packs** — load only the countries you need, mix freely
2. **South Asian diaspora coverage** — Indian PII patterns layered across non-India firms (Dubai · Australia · UK · USA · EU · Singapore)
3. **Legal-tech-specific patterns** — court case numbers across 7 jurisdictions, license numbers, regulatory IDs
4. **Zero runtime dependencies** — pure-stdlib `re`, no API keys, no cloud, no telemetry
5. **MIT-licensed open source** — drop into any legal-tech project, fork as needed
6. **Session-scoped + in-memory-only** — designed for the privacy-default-ON solo / small-firm practice

Full honest comparison: [COMPARISON.md](COMPARISON.md)

---

## 🤖 How the agents use it

This library is integrated at TWO architectural layers across the ecosystem. **Both layers only activate when the user has opted into a cloud-LLM tier** — in the local-default (Ollama) configuration the Gateway is not invoked because no prompt crosses the machine boundary.

### Layer 1 — AI Law Firm specialist agents (7 country firms + 1 startup firm), CLOUD MODE

Each AI Law Firm's brain-classifier routes user requests to specialist agents (Matter Manager · Citation Clerk · Court Registrar · Drafting Assistant · Compliance Officer · Calendar Sync · etc.). When the user has configured a cloud-LLM provider in `~/.ailawfirm-<jurisdiction>/config.json` (e.g. `ai_provider="anthropic"`), the firm's internalised `PseudonymisationGateway` (source: `ailawfirm_<jurisdiction>/pseudonymisation.py`) is invoked before ANY specialist agent calls the cloud LLM. The cloud LLM sees only `[PERSON_1]`, `[EMIRATES_ID_1]`, `[NI_NUMBER_1]` placeholders. The response is then run through `gw.desanitize()` before being shown to the user.

In local mode (`ai_provider="ollama"` or absent — the default), specialist agents talk directly to the on-device Ollama runtime. The Gateway is not in the call path because there is no cross-vendor transmission to firewall.

### Layer 2 — Drafting plugin Reader → Overseer pipeline (14 Indian-litigation drafting plugins), CLOUD MODE

The Wolfgang Rush drafting plugins each implement a **6-agent pipeline**:

```
Reader → Format → Drafter → Verifier → Refiner → Overseer
```

The **Reader agent** is the first agent — it reads the user's case folder (matter notes, party details, statements). This is where real PII enters the pipeline. Before the Reader hands sanitized facts to Format/Drafter/Verifier/Refiner for cloud-LLM-assisted drafting, it calls:

```python
clean_facts, token_map = gw.sanitize(case_folder_text)
```

All four middle agents (Format · Drafter · Verifier · Refiner) operate exclusively on placeholder-bearing sanitized text. The cloud LLM vendor never sees the client's real name, Aadhaar, NI Number, Emirates ID, NRIC, or any other government identifier across the entire drafting cycle.

The **Overseer agent** is the final agent. Before writing the completed pleading to disk, it calls:

```python
final_draft = gw.desanitize(refined_draft, token_map)
```

Real client names and IDs reappear ONLY in the final filed pleading on the practitioner's local machine. No intermediate version with both real PII AND LLM output exists anywhere.

This architecture means: even if a cloud LLM vendor's logs are subpoenaed or a vendor's training pipeline retains prompts, the practitioner's client PII was never in those payloads. The session-scoped `TokenMap` lived in Python memory for ~30 seconds during one drafting run, then was garbage-collected.

---

## 🌗 Dual-mode privacy posture — at a glance

The Wolfgang Rush AI Law Firm family ships with a clear dual-mode privacy story. This library is the cloud-mode half.

| Configuration | What happens to a prompt | What the Gateway does | Whom this is for |
|---|---|---|---|
| 🥇 **Local mode (default)** — `ai_provider="ollama"` or unset (v0.1 keyword-matching brain · v0.2+ Ollama + Qwen3) | Stays on the user's laptop. Ollama runtime processes it. Nothing crosses the machine boundary. | Not invoked. There is no cross-vendor transmission to firewall. | Practitioners whose matter sensitivity requires zero cross-border data flow (e.g. Section 77 MHR data · UAE PDPL Article 22 restricted categories · most privileged advocate-client communications). |
| 🥈 **DeepSeek cloud mode (opt-in)** | Sanitised via Gateway → transmitted to DeepSeek API → response de-sanitised on receipt. | Active. Strips names, government IDs, contact identifiers, case references before transmission; restores them in the response. | Practitioners doing public-law research · template-building · study work where cost matters and the user has independently accepted China-routed transmission of pseudonymised data. |
| 🥉 **Claude / Gemini cloud mode (opt-in)** | Sanitised via Gateway → transmitted to Anthropic / Google API → response de-sanitised on receipt. | Active. Same protection. | Practitioners doing heavy daily drafting where cloud-LLM quality matters AND who have executed the vendor DPA + jurisdiction-specific safeguards (UK GDPR Schedule 21 · EU Schrems II Article 46 · US BAA where HIPAA applies · APP 8 risk assessment where Australian APP applies · etc.). |

**What this library does NOT discharge:**
- It does NOT discharge your vendor DPA / Article 28 / BAA / Schrems II supplementary safeguard / APP 8 risk-assessment / state-bar opinion obligations. Those remain yours to execute.
- It does NOT cure jurisdiction-specific prohibitions on offshore data handling for specific categories of data — those categories require Local Ollama tier, full stop.
- It does NOT eliminate the need to verify your matter's specific identifiers fall within the Gateway's coverage patterns.

This is **privacy-by-architecture for the cloud-mode half** of the dual-mode story. The local-default half is privacy-by-absence-of-transmission and needs no library at all.

---

## 📚 Used by

This library is the privacy primitive shipped across **22 repos** under the Wolfgang Rush publishing brand:

### 7 country AI Law Firms
- [ai-law-firm-india](https://github.com/Wolfgangrush/ai-law-firm-india)
- [ai-law-firm-uk](https://github.com/Wolfgangrush/ai-law-firm-uk)
- [ai-law-firm-dubai](https://github.com/Wolfgangrush/ai-law-firm-dubai)
- [ai-law-firm-australia](https://github.com/Wolfgangrush/ai-law-firm-australia)
- [ai-law-firm-singapore](https://github.com/Wolfgangrush/ai-law-firm-singapore)
- [ai-law-firm-usa](https://github.com/Wolfgangrush/ai-law-firm-usa)
- [ai-law-firm-eu](https://github.com/Wolfgangrush/ai-law-firm-eu)

### 1 AI Startup Firm
- [ai-startup-firm-india](https://github.com/Wolfgangrush/ai-startup-firm-india)

### 14 Indian-litigation drafting plugins
- [supreme-court-drafting](https://github.com/Wolfgangrush/supreme-court-drafting) · [indian-hc-drafting](https://github.com/Wolfgangrush/indian-hc-drafting) · [district-court-drafting](https://github.com/Wolfgangrush/district-court-drafting)
- [indian-family-drafting](https://github.com/Wolfgangrush/indian-family-drafting) · [indian-contracts-drafting](https://github.com/Wolfgangrush/indian-contracts-drafting) · [indian-banking-drafting](https://github.com/Wolfgangrush/indian-banking-drafting)
- [indian-labour-drafting](https://github.com/Wolfgangrush/indian-labour-drafting) · [indian-property-drafting](https://github.com/Wolfgangrush/indian-property-drafting) · [indian-company-drafting](https://github.com/Wolfgangrush/indian-company-drafting)
- [indian-tax-drafting](https://github.com/Wolfgangrush/indian-tax-drafting) · [indian-consumer-drafting](https://github.com/Wolfgangrush/indian-consumer-drafting) · [indian-mact-drafting](https://github.com/Wolfgangrush/indian-mact-drafting)
- [indian-ip-drafting](https://github.com/Wolfgangrush/indian-ip-drafting) · [indian-rent-control-drafting](https://github.com/Wolfgangrush/indian-rent-control-drafting)

If you're building a legal-tech tool on cloud LLMs and don't have a pseudonymisation layer yet — please add one. This library, Presidio, cloud DLP — pick one. **Don't ship cloud-LLM-based legal-tech without it.** Your clients are trusting you to keep their data safe; the LLM vendor cannot.

---

## 🛡️ Threat model

**What this library protects against:**
- ✅ Client PII reaching cloud-LLM vendor's training pipelines
- ✅ Client PII in cloud-LLM logs / debug traces
- ✅ Client PII in cloud-LLM API request/response payloads at rest
- ✅ Accidental leak via prompt-engineering / fewshot examples

**What it does NOT protect against:**
- ❌ Vendor-side OCR / vision processing of attached documents — strip metadata + redact images separately
- ❌ Audio transcripts — use a separate speech-to-text pseudonymisation layer
- ❌ Side-channel correlation (timing, length, frequency) — orthogonal defense needed
- ❌ User error: pasting sanitized output back into another tool that re-derives the original
- ❌ Determined adversaries with access to your token map — keep gateway instances session-scoped

**This is a privacy-by-default tool, not a zero-knowledge tool.** Use alongside local-LLM-first architecture (Ollama, llama.cpp) for highest-sensitivity matters. For matters that *must* go through cloud LLMs (DPDP/GDPR-permitted scenarios), this library is the minimum defense.

---

## 🔄 Extending

### Add a new jurisdiction

```python
# pseudonymisation_gateway/patterns/japan.py
import re

# Add Japan-specific patterns
MY_NUMBER_RE = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")  # Japanese My Number system
JAPAN_PHONE_RE = re.compile(r"(?:\+81[\s-]?)?0\d{1,3}[\s-]?\d{4}[\s-]?\d{4}\b")
# ...

PATTERNS = [
    (MY_NUMBER_RE, "JP_MY_NUMBER"),
    (JAPAN_PHONE_RE, "JP_PHONE"),
]
```

Then use:
```python
from pseudonymisation_gateway.patterns import japan
gw = PseudonymisationGateway(jurisdictions=[japan])
```

Or PR it into the main repo — see [JURISDICTIONS.md](JURISDICTIONS.md).

---

## 🤝 Contributing

PRs welcome — especially:
- New jurisdiction modules (with test fixtures using realistic-format synthetic PII)
- Improved regex patterns (with reasoning + test cases for the change)
- Diaspora-coverage refinements (e.g., Chinese diaspora patterns for Singapore/USA/Canada)
- Documentation translations (the README would benefit from Arabic, Mandarin, Hindi versions for the firms that use it)

Open an issue first for discussion, then PR.

---

## 📜 License

MIT — see [LICENSE](LICENSE).

Copyright (c) 2026 Rushikesh R. Mahajan (publishing as Wolfgang Rush).

---

## 👤 Author

**Rushikesh R. Mahajan**
Advocate · Bombay High Court (Nagpur Bench) · Bar Council of Maharashtra & Goa
LLM (Law and Technology) · Queen's University Belfast (2024)
Publishing as **Wolfgang Rush**

GitHub: [github.com/Wolfgangrush](https://github.com/Wolfgangrush)
LinkedIn: [linkedin.com/in/rushikesh-ravindra-mahajan](https://www.linkedin.com/in/rushikesh-ravindra-mahajan/)

---

> ⚠️ **AI can make mistakes. Always verify the output.**
>
> This is privacy infrastructure for legal-tech tools, not legal advice. Every implementation, every test fixture, every regex pattern should be independently verified before relying on it in production. The author accepts no liability for outputs used without verification.
