# 📊 COMPARISON — `pseudonymisation-gateway` vs prior art

Honest comparison with the libraries and services this builds on. I want fact-checkable claims, not invention-claims.

---

## 1. GDPR Article 4(5) — the legal definition

**"pseudonymisation"** is a defined term in EU law since the GDPR took effect (May 2018). Article 4(5):

> *"the processing of personal data in such a manner that the personal data can no longer be attributed to a specific data subject without the use of additional information, provided that such additional information is kept separately and is subject to technical and organisational measures to ensure that the personal data are not attributed to an identified or identifiable natural person"*

**DPDP Act 2023 (India)** adopts the same concept under the "Data Fiduciary" framework, with similar pseudonymisation-as-a-safeguard structure.

This library implements that legal definition in the specific context of "before-cloud-LLM-API-call middleware." We did not invent the concept. We implement a recognised legal-technical primitive.

---

## 2. Microsoft Presidio

**[Microsoft/presidio](https://github.com/microsoft/presidio)** — open-source since 2018. The gold standard for PII detection + anonymization in Python.

| | Presidio | this library |
|---|---|---|
| **License** | MIT | MIT |
| **Detection approach** | NLP (spaCy/transformers) + regex hybrid | Pure regex (v0.1) |
| **Coverage** | US, EU, UK, AU PII focus + good HIPAA/medical | India + UAE + AU + UK + USA + EU + SG + cross-jurisdiction diaspora |
| **Jurisdiction modularity** | Built-in recognizers — extending requires understanding recognizer registry | Per-country modules with single `PATTERNS` list — drop-in friendly |
| **Dependencies** | spaCy, transformers, FastAPI, etc. (heavy) | Pure stdlib `re` (zero deps) |
| **Cloud / API** | Has `presidio-analyzer` + `presidio-anonymizer` as REST services | Library only — no service, no API key, no telemetry |
| **Legal-tech specific patterns** | Generic PII — not court case nums, license numbers, etc. | Court case nums (7 jurisdictions), license numbers, regulatory IDs |
| **Indian PII** | No Aadhaar / PAN / GSTIN / IFSC out of the box | Native first-class |
| **Emirates / UAE PII** | No Emirates ID / VAT TRN / Trade License | Native first-class |
| **South Asian diaspora handling** | Would require manual recognizer registration | Built-in via `jurisdictions=["uae", "india"]` |
| **Round-trip (sanitize → cloud → restore)** | Anonymizer + token tracking via `OperatorConfig`, but more setup | Single-call `sanitize()` + `desanitize()` API |
| **NER (name detection)** | Production-grade spaCy/transformers | Regex-heuristic (honorific + capitalized words) |

### When to use Presidio
- You're already invested in a spaCy/NLP pipeline
- You need state-of-the-art NER for unstructured names beyond honorific-prefixed cases
- You operate in jurisdictions Presidio covers well (US, EU, UK, AU)
- You have the compute budget for ML model inference at scale
- You need HIPAA-style structured medical-record patterns

### When to use this library
- You're building legal-tech tools for South Asian markets, UAE, or with diaspora coverage
- You need Indian PII detection that Presidio doesn't provide out of the box
- You want zero-dependency drop-in (no spaCy install, no ML model download)
- You want court case-number detection across 7 jurisdictions
- You're building a solo-practice / small-firm tool and don't want the operational overhead of a full Presidio deployment
- You want a library that respects "in-memory only, no telemetry" as the default posture

**You can use both.** Presidio for name NER, this library for jurisdiction-specific structured PII. They compose cleanly.

---

## 3. Cloud DLP services

**AWS Comprehend PII** · **Google Cloud DLP** · **Azure AI Language PII detection** — all major cloud vendors offer PII detection as a managed service.

| | Cloud DLP services | this library |
|---|---|---|
| **License** | Proprietary, paid per API call | MIT, free |
| **Where data goes** | Your text → the cloud vendor for detection | Stays on your machine |
| **Cost** | Per-call billing (~$0.0001-0.001 per char) | Zero |
| **Latency** | Network roundtrip | Sub-millisecond local |
| **Coverage** | US/EU strong, Asia/MENA weaker | India + UAE first-class, AU/UK/USA/EU/SG strong |
| **Privacy contradiction** | Using a cloud service to detect PII before sending to a cloud LLM = data goes to cloud twice | Sanitize locally → send only cleaned text to cloud |

### When to use cloud DLP
- You're already in that cloud ecosystem and the data-residency contract works for you
- You need their pre-trained ML models for unstructured PII (handwriting OCR + NER + structured detection in one)
- You don't have the engineering team to maintain regex patterns

### When NOT to use cloud DLP
- The whole point of pseudonymisation is to NOT send data to clouds
- Your matter sensitivity exceeds the DLP vendor's residency/contract terms
- You want a fully open-source tool you can audit + fork + ship

For legal-tech, the cloud-DLP-to-protect-cloud-LLM pattern is questionable: you're paying a cloud vendor to scrub data before paying ANOTHER cloud vendor (the LLM). If the matter is sensitive enough to need DLP, it's sensitive enough to use a local-LLM (Ollama/llama.cpp) entirely.

---

## 4. Differential privacy (academic line of work)

**Differential privacy** (Dwork et al., 2006+) is a mathematical framework for adding noise to data so that individual records can't be re-identified from aggregate results.

This library does NOT implement differential privacy. Different problem:
- DP protects **statistical queries over a dataset** from re-identifying individuals
- This library protects **individual records (client matters) going to a cloud LLM**

Pseudonymisation (this library's job) is a different protection technique from DP. They're complementary, not substitutes.

If you need to share aggregated client-matter statistics with researchers, use DP libraries (Google's `differential-privacy`, OpenDP, etc.). If you need to send individual client matters to a cloud LLM for drafting assistance, use pseudonymisation (this library, or Presidio).

---

## 5. Tokenization / format-preserving encryption

**Tokenization** services (Vault, Skyflow, etc.) replace sensitive values with non-sensitive tokens, with the original kept in a secure vault.

| | Tokenization vaults | this library |
|---|---|---|
| **Storage of originals** | Centralized secure vault (network call to retrieve) | In-memory only, session-scoped |
| **Architecture** | Service / API | Library |
| **Round-trip** | Vault lookup per token | Local dict lookup |
| **Audit trail** | Often built-in | None (intentional) |
| **Threat model** | Vault compromise = full disclosure | Session compromise = single session's token map |

Tokenization vaults are appropriate for **persistent** pseudonymisation (e.g., a long-running database where you need stable tokens across many sessions and need an audit trail for compliance).

This library is appropriate for **session-scoped** pseudonymisation (e.g., a single legal-drafting session where you scrub before send, restore after response, and want zero persistence).

---

## 6. Honorable mentions

- **scrubadub** (Python) — older PII scrubbing library, less actively maintained
- **textanon** — academic-focused text anonymization
- **pii-detector** (various) — many one-off projects, varying quality

This library is opinionated about its niche: **legal-tech, jurisdiction-aware, diaspora-covering, session-scoped, no-dependencies, no-telemetry**. If those constraints don't match your use case, one of the alternatives may serve better.

---

## 7. Honest assessment — strengths + weaknesses

### Strengths
- ✅ **First-class Indian + UAE PII** — no other open-source tool covers these as cleanly
- ✅ **Diaspora overlay pattern** — load multiple jurisdiction modules to cover real-world client populations
- ✅ **Legal-tech specific** — court case numbers across 7 jurisdictions, license numbers, regulatory IDs
- ✅ **Zero runtime dependencies** — pure stdlib `re`
- ✅ **Production-tested** — used across 22 live repos
- ✅ **MIT licensed** — drop-in, fork-friendly, no commercial restrictions

### Weaknesses
- ❌ **No ML-based NER** — names without honorifics get missed (e.g., "Khalid told the court that..." misses "Khalid")
- ❌ **No image/PDF processing** — only text input
- ❌ **English-language matching** — patterns + honorifics + keywords are English-language; non-English text needs separate handling
- ❌ **Per-member-state EU coverage incomplete** — only DE/FR/IT national IDs in v0.1; other 24 member states pending
- ❌ **No state-specific USA patterns** — driver license, state court formats vary wildly; only Federal docket numbers in v0.1
- ❌ **Format-realistic only** — patterns match format, not validity (no Aadhaar checksum verification, no Luhn-style ID validation)

### v0.2 roadmap
- Optional spaCy NER backend (additive — keeps regex layer as default)
- More EU member-state national-ID patterns
- US state-specific patterns
- Pakistani / Bangladeshi / Sri Lankan / Nepali / Sinhala diaspora patterns
- Format validation (Aadhaar checksum, IBAN MOD-97, GSTIN checksum)
- Multi-language honorifics (Arabic, Mandarin, Hindi)
- Performance: streaming `sanitize()` for very large documents

---

## 8. Citations + further reading

**Legal definitions:**
- Regulation (EU) 2016/679 (GDPR), Article 4(5)
- Digital Personal Data Protection Act 2023 (India), Section 2(s) "personal data"

**Engineering predecessors:**
- Microsoft/presidio: https://github.com/microsoft/presidio (Itamar Goldberger et al.)
- AWS Comprehend PII: https://docs.aws.amazon.com/comprehend/latest/dg/how-pii.html
- Google Cloud DLP: https://cloud.google.com/dlp

**Academic line:**
- Dwork, C. (2006). "Differential Privacy". ICALP.
- Sweeney, L. (2002). "k-Anonymity: A Model for Protecting Privacy". IJUFKS.

**Indian-context guides:**
- UIDAI Aadhaar verification format spec — https://uidai.gov.in/
- Income Tax India PAN format spec — https://www.incometax.gov.in/
- GST format spec — https://www.gst.gov.in/

---

If this library overlaps with your work + you'd like cross-citation or PR collaboration — open an issue. The goal is wider adoption of pseudonymisation as a baseline for legal-tech tools, not territorial competition.
