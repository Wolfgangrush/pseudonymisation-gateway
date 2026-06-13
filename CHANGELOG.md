# Changelog

## [0.3.0-honest-disclosure] — 2026-06-06

### Documentation
- Refined README architecture diagram (sanitize/desanitize flow) and the "How the agents use it" section to surface v0.3 honest-disclosure: the regex + NER + parties.json layered scanner achieves high recall, but is not 100%. Any residue the scanner can't fully resolve is surfaced to the user and audit-logged before send. Architecture materially strengthens privacy by eliminating the most common attack surface; remaining edge cases are surfaced to the user, not silently passed.
- Locked under doctrine: refinement-not-retraction for architecture-honest overclaim + adoption-first in no-statutory-AI-law jurisdictions (no hard-block UX; tiered-confidence dialog on high-confidence residue with Proceed-anyway available; silent audit log on low-confidence residue; the practitioner retains the final call).

### v0.3-alpha implementation scope (engineering — separate from this doc-only commit)
- Layered sanitiser (regex + Indian-NER-tuned + parties.json per-matter dictionary)
- Tiered residue scan (high-confidence residue → soft dialog; low-confidence → silent audit log)
- Per-call audit log (counts only, never values; matter ID + entity count + types + residue-scan result + model + timestamp)
- Ship target window 2026-06-08 → 2026-06-11. 2-week live testing → lock as v0.3 if zero leaks.

## [0.1.1] — 2026-06-05 · Dual-mode disclosure refinement

### Changed
- **README.md** — clarified the dual-mode privacy posture for the wolfgang_rush AI Law Firm family:
  - "Why this exists" section now opens with the explicit local-default / cloud-optional dual-mode framing, naming the Gateway as the bridge architecture that activates in cloud mode (not always).
  - "How the agents use it" sections now carry the **CLOUD MODE** qualifier so readers do not infer the Gateway is in the call path when an AI Law Firm is configured for Local Ollama.
  - New "Dual-mode privacy posture — at a glance" section before "Used by" — three-row table mapping each configuration (Local Ollama default · DeepSeek opt-in · Claude/Gemini opt-in) to whether the Gateway is invoked, what it does, and whom each tier is for. Also names what the Gateway does NOT discharge (vendor DPA · Article 28 · BAA · Schrems II supplementary safeguards · APP 8 risk assessments · state-bar opinions · jurisdiction-specific offshore-prohibition categories).

### Why this matters
The prior README was technically accurate but did not clearly distinguish that the Gateway only activates in cloud mode. A reader skim could infer the library is the always-on privacy layer for the AI Law Firms, when in fact local-Ollama-tier users have no need for it because no transmission occurs. This refinement makes the dual-mode story explicit and prevents readers from conflating Gateway protection with the absence-of-transmission protection that the local-default tier provides.

### Unchanged
- Engine, jurisdiction modules, pattern catalogs, threat model, and test suite are unchanged. This is a documentation refinement, not a behavioural change.

## [0.1.0] — 2026-05-20

### Initial release

First publication of `pseudonymisation-gateway` — the privacy primitive built to firewall client PII from cloud LLMs, shipped as the integration layer across 7 country AI Law Firms + 1 AI Startup Firm + 14 Indian-litigation drafting plugins (22 repos under the wolfgang_rush publishing brand).

**Engine:**
- `PseudonymisationGateway` — session-scoped, in-memory, deterministic placeholder mapping
- `TokenMap` — forward + reverse + per-entity-type counter
- `register_pattern()` — extensible per-matter custom patterns

**Jurisdiction modules:**
- `patterns.india` — Aadhaar · PAN · GSTIN · IFSC · Indian phone · ₹ amounts · FIR · vehicle registration · case numbers
- `patterns.uae` — Emirates ID · UAE IBAN · Trade License (Dubai/DIFC/IFZA/DMCC/JAFZA/DAFZA) · DIFC Court case numbers · Cassation case numbers · UAE phone · AED amounts
- `patterns.australia` — TFN · Medicare · ABN · ACN · BSB · AU phone (+61) · AUD amounts · HCA/FCA/FCAFC/state court case numbers
- `patterns.uk` — NI Number · NHS Number · UTR · UK VAT · UK IBAN · UK phone (+44) · GBP amounts · EWHC/EWCA/UKSC case numbers
- `patterns.usa` — SSN · ITIN · EIN · US phone (+1) · USD amounts · driver license · federal docket numbers
- `patterns.eu` — IBAN (27 member states) · EU VAT · EORI · German Steuer-ID · French INSEE · Italian Codice Fiscale · CJEU case numbers · EUR amounts
- `patterns.singapore` — NRIC · FIN · UEN · CPF · SG phone (+65) · SGD amounts · SGCA/SGHC/SGDC case numbers

**Shared patterns:** EMAIL_RE · NAME_RE (honorific-driven) · DATE_RE · generic case-number patterns

**Documentation:**
- `README.md` — story + how it works + integration
- `ARCHITECTURE.md` — technical walkthrough
- `JURISDICTIONS.md` — per-country pattern catalog + extension guide
- `COMPARISON.md` — honest comparison with Microsoft Presidio, cloud DLP APIs, differential privacy approaches

**Shipped as the privacy primitive in:**
- 7 country AI Law Firms (Wolfgangrush/ai-law-firm-india · -uk · -uae · -australia · -singapore · -usa · -eu)
- 1 AI Startup Firm (Wolfgangrush/ai-startup-firm-india)
- 14 Indian-litigation drafting plugins (Wolfgangrush/supreme-court-drafting · -indian-hc-drafting · -district-court-drafting · -indian-{family,contracts,banking,labour,property,company,tax,consumer,mact,ip,rent-control}-drafting)

### Honest acknowledgments

This library does not invent pseudonymisation as a concept. It builds on:
- GDPR Article 4(5) — defines pseudonymisation in EU law
- DPDP Act 2023 (India) — adopts the same framework
- Microsoft Presidio — open-source PII detection + anonymization (2018+)
- Cloud DLP APIs from AWS · Google · Azure
- Two decades of academic work on differential privacy, tokenization, and k-anonymity

The library's contribution is the **practical jurisdictional integration pattern**: per-country PII modules + South Asian diaspora coverage across non-India jurisdictions + legal-tech-specific test fixtures + pre-cloud-API middleware shape designed for solo-practice and small-firm legal tools building on cloud LLMs.

See `COMPARISON.md` for an honest assessment of where this library overlaps with and differs from Presidio + cloud DLP services.
