# Changelog

## [0.1.0] — 2026-05-20

### Initial release

First publication of `pseudonymisation-gateway` — extracted from production use across 7 country AI Law Firms + 1 AI Startup Firm + 14 Indian-litigation drafting plugins (22 repos under the Wolfgang Rush publishing brand).

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

**Used in production by:**
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
