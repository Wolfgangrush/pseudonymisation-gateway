# 🌐 JURISDICTIONS — pattern catalog + extension guide

Each jurisdiction module under `pseudonymisation_gateway/patterns/` exposes a `PATTERNS` list. Below is the full catalog of what each module detects + how to extend or add new jurisdictions.

---

## 🇮🇳 India (`patterns.india`)

| Entity type | Format | Example | Regex name |
|---|---|---|---|
| AADHAAR | 12 digits in 4-4-4 or unspaced | `1234 5678 9012` | `AADHAAR_RE` |
| PAN | 5 letters + 4 digits + 1 letter | `ABCDE1234F` | `PAN_RE` |
| GSTIN | state code + PAN + entity + Z + checksum | `27ABCDE1234F1Z5` | `GSTIN_RE` |
| IFSC | 4 letters + 0 + 6 alphanumerics | `SBIN0001234` | `IFSC_RE` |
| FIR_NO | "FIR No. X/YYYY" | `FIR No. 123/2024` | `FIR_RE` |
| INDIA_CASE | Civil/Criminal/Writ etc. + No + year | `Civil Appeal No. 1234 of 2024` | `INDIA_CASE_RE` |
| INDIA_VEHICLE | State-District-Series-Num | `MH-12-AB-1234` | `INDIA_VEHICLE_RE` |
| INDIA_PHONE | +91 + 10 digits starting 6-9 | `+919876543210` | `INDIA_PHONE_RE` |
| INR_AMOUNT | ₹ / Rs / INR + amount | `₹4,50,000` | `INR_AMOUNT_RE` |

---

## 🇦🇪 UAE / Dubai-DIFC (`patterns.uae`)

| Entity type | Format | Example | Regex name |
|---|---|---|---|
| EMIRATES_ID | 784-YYYY-XXXXXXX-X | `784-1985-1234567-8` | `EMIRATES_ID_RE` |
| UAE_IBAN | AE + 2 check + 19 digits | `AE070331234567890123456` | `UAE_IBAN_RE` |
| TRADE_LICENSE | Dubai Economy / DIFC / Free Zones | `CN-1234567`, `DIFC-CL1234`, `IFZA-12345` | `TRADE_LICENSE_RE` |
| DIFC_CASE | [YYYY] DIFC CFI/CA/SCT N | `[2024] DIFC CFI 023` | `DIFC_CASE_RE` |
| UAE_CASE | Cassation Petition No. X of YYYY | `Cassation Petition No. 123 of 2024` | `UAE_CASSATION_RE` |
| UAE_PHONE | +971 / 050/052/054/055/056/058 | `+971 50 123 4567` | `UAE_PHONE_RE` |
| AED_AMOUNT | AED / د.إ / Dhs / DH | `AED 45,000` | `AED_AMOUNT_RE` |
| VAT_TRN | TRN keyword + 15 digits | `TRN 100123456700003` | `VAT_TRN_RE` |

---

## 🇦🇺 Australia (`patterns.australia`)

| Entity type | Format | Example | Regex name |
|---|---|---|---|
| TFN | keyword TFN + 9 digits | `TFN: 123 456 789` | `TFN_RE` |
| MEDICARE | keyword Medicare + 10 digits | `Medicare 1234 56789 0` | `MEDICARE_RE` |
| ABN | keyword ABN + 11 digits | `ABN 12 345 678 901` | `ABN_RE` |
| ACN | keyword ACN + 9 digits | `ACN 123 456 789` | `ACN_RE` |
| AU_BSB | keyword BSB + 6 digits | `BSB 062-001` | `AU_BSB_RE` |
| AU_CASE | [YYYY] HCA/FCA/etc + N | `[2024] HCA 12` | `AU_CASE_RE` |
| AU_PHONE | +61 / 04XX format | `+61 4 1234 5678` | `AU_PHONE_RE` |
| AUD_AMOUNT | A$ / AUD | `A$25,000` | `AUD_AMOUNT_RE` |

---

## 🇬🇧 UK (`patterns.uk`)

| Entity type | Format | Example | Regex name |
|---|---|---|---|
| NI_NUMBER | 2 letters + 6 digits + 1 letter | `AB123456C` | `NI_NUMBER_RE` |
| NHS_NUMBER | keyword NHS + 10 digits | `NHS 123 456 7890` | `NHS_NUMBER_RE` |
| UTR | keyword UTR + 10 digits | `UTR 1234567890` | `UTR_RE` |
| UK_VAT | GB + 9 or 12 digits | `GB123456789` | `UK_VAT_RE` |
| UK_IBAN | GB + 2 check + 18 alphanumeric | `GB29NWBK60161331926819` | `UK_IBAN_RE` |
| UK_CASE | [YYYY] EWHC/EWCA/UKSC + division | `[2024] EWHC Comm 1234` | `UK_CASE_RE` |
| UK_PHONE | +44 / 07 / 01 / 02 | `+44 20 1234 5678` | `UK_PHONE_RE` |
| GBP_AMOUNT | £ | `£15,000` | `GBP_AMOUNT_RE` |

---

## 🇺🇸 USA (`patterns.usa`)

| Entity type | Format | Example | Regex name |
|---|---|---|---|
| SSN | XXX-XX-XXXX (with SSA exclusions) | `123-45-6789` | `SSN_RE` |
| ITIN | 9XX-XX-XXXX | `912-34-5678` | `ITIN_RE` |
| EIN | keyword EIN + XX-XXXXXXX | `EIN 12-3456789` | `EIN_RE` |
| US_DL | keyword DL/DLN/License + alphanumeric | `DL ABC12345` | `US_DL_RE` |
| US_DOCKET | Federal docket: X:XX-cv-NNNN | `1:24-cv-12345` | `US_DOCKET_RE` |
| US_PHONE | +1 / 10-digit format | `+1 (212) 555-1234` | `US_PHONE_RE` |
| USD_AMOUNT | US$ / USD | `US$50,000` | `USD_AMOUNT_RE` |

---

## 🇪🇺 EU (`patterns.eu`)

| Entity type | Format | Example | Regex name |
|---|---|---|---|
| EU_IBAN | 27-country prefix + 11-30 alphanumeric | `DE89370400440532013000` | `EU_IBAN_RE` |
| EU_VAT | country prefix + 8-12 alphanumeric | `DE123456789` | `EU_VAT_RE` |
| EU_EORI | country prefix + 15 alphanumeric | `DE123456789012345` | `EU_EORI_RE` |
| DE_TAX_ID | Steuer-ID + 11 digits | `Steuer-ID 12345678901` | `GERMAN_TAX_ID_RE` |
| FR_INSEE | INSEE + 15 digits | `INSEE 123456789012345` | `FRENCH_INSEE_RE` |
| IT_CF | Italian Codice Fiscale alphanumeric | `RSSMRA80A01H501Z` | `ITALIAN_CF_RE` |
| CJEU_CASE | C-NNN/YY or T-NNN/YY | `C-456/23` | `CJEU_CASE_RE` |
| EUR_AMOUNT | € | `€25,000` | `EUR_AMOUNT_RE` |

---

## 🇸🇬 Singapore (`patterns.singapore`)

| Entity type | Format | Example | Regex name |
|---|---|---|---|
| NRIC | S/T + 7 digits + letter | `S1234567A` | `NRIC_RE` |
| FIN | F/G/M + 7 digits + letter | `F1234567B` | `FIN_RE` |
| UEN | keyword UEN + 8-10 digits + letter | `UEN 201234567A` | `UEN_RE` |
| CPF | keyword CPF + 8 digits | `CPF 1234 5678` | `CPF_RE` |
| SG_CASE | [YYYY] SGCA/SGHC/SGDC/SGMC + N | `[2024] SGCA 12` | `SG_CASE_RE` |
| SG_PHONE | +65 / 8XXX / 9XXX | `+65 9123 4567` | `SG_PHONE_RE` |
| SGD_AMOUNT | S$ | `S$15,000` | `SGD_AMOUNT_RE` |

---

## 🌐 Shared (`shared`)

Loaded by default (unless `include_shared=False`). Apply cross-jurisdiction:

| Entity type | Format | Example | Regex name |
|---|---|---|---|
| EMAIL | RFC-ish | `client@firm.com` | `EMAIL_RE` |
| BANK_ACCT | keyword Account/A/C + 9-18 digits | `Account No. 123456789012` | `BANK_ACCT_RE` |
| CASE_NO | generic Civil/Criminal/Writ + No + year | `Civil Appeal No. 1234 of 2024` | `GENERIC_CASE_RE` |
| DATE | ISO / DD-MMM-YYYY / DD/MM/YYYY | `2024-03-15`, `15 March 2024` | `DATE_RE` |
| PERSON | honorific + name (capture group 1) | `Mr. John Smith` | `NAME_RE` |

---

## 🛠️ Extending — add your own jurisdiction

### Step 1 — research the jurisdiction's PII types

For a new country, identify:
- National ID format (Aadhaar / SSN / NI / etc.)
- Tax ID format (PAN / UTR / EIN / TFN / etc.)
- Healthcare ID (Medicare / NHS / etc.)
- Phone format (country code + national format)
- Currency symbol + grouping convention
- Court case-number convention
- Company/business registration ID format
- Bank routing format (IBAN / IFSC / BSB / etc.)
- Driver license format
- Sectoral IDs relevant to legal practice (Bar number, etc.)

### Step 2 — write the pattern module

Create `pseudonymisation_gateway/patterns/<country_slug>.py`:

```python
"""<Country> PII patterns."""
import re

# National ID
COUNTRY_ID_RE = re.compile(r"<regex>")

# Tax ID
COUNTRY_TAX_RE = re.compile(r"<regex>")

# Phone
COUNTRY_PHONE_RE = re.compile(r"<regex>")

# Currency
COUNTRY_AMOUNT_RE = re.compile(r"<regex>")

# Case nums
COUNTRY_CASE_RE = re.compile(r"<regex>")

PATTERNS: list[tuple[re.Pattern, str]] = [
    (COUNTRY_ID_RE, "COUNTRY_ID"),
    (COUNTRY_TAX_RE, "COUNTRY_TAX"),
    (COUNTRY_PHONE_RE, "COUNTRY_PHONE"),
    (COUNTRY_AMOUNT_RE, "COUNTRY_AMOUNT"),
    (COUNTRY_CASE_RE, "COUNTRY_CASE"),
]
```

### Step 3 — write tests

Create `tests/test_<country_slug>.py`:

```python
from pseudonymisation_gateway import PseudonymisationGateway

def test_country_national_id():
    gw = PseudonymisationGateway(jurisdictions=["<slug>"])
    clean, _ = gw.sanitize("Client ID 1234567890 attached.")
    assert "[COUNTRY_ID_1]" in clean
```

Use synthetic-format-realistic PII in tests. No real client data ever.

### Step 4 — register in `patterns/__init__.py`

```python
from . import india, uae, australia, uk, usa, eu, singapore, <country_slug>

__all__ = [..., "<country_slug>"]
```

### Step 5 — run tests + open PR

```bash
python3 -m pytest -q
```

Open a PR with: pattern module + tests + README/JURISDICTIONS update + sourcing for the regex patterns (link to official government PII format spec).

---

## 🎯 Pattern design guidelines

When writing patterns:

1. **Anchor with `\b` word boundaries** to prevent matching mid-word
2. **Require keyword prefixes for ambiguous numeric IDs** (TFN/Medicare/EIN need keyword; SSN doesn't because XXX-XX-XXXX is unique)
3. **Use case-insensitive flag** for keyword-prefixed patterns (`re.IGNORECASE`)
4. **Test against negative cases** — strings that LOOK like the format but aren't (e.g., postcodes that match a 4-digit pattern in Australia)
5. **Order patterns within a module** — specific before general
6. **Document the format source** — link to government regulation defining the format
7. **Synthetic-but-valid test data** — patterns must match real format without exposing any actual person's PII

---

## 🌍 Diaspora extension pattern

When a jurisdiction has substantial diaspora populations whose PII appears in client matters, load multiple jurisdiction modules:

```python
# Dubai-DIFC firm handling Indian-expat matters
gw = PseudonymisationGateway(jurisdictions=["uae", "india"])

# UK firm handling Indian + Pakistani diaspora matters
gw = PseudonymisationGateway(jurisdictions=["uk", "india", "pakistan"])  # pakistan module hypothetical

# Australia firm handling Indian + Chinese diaspora
gw = PseudonymisationGateway(jurisdictions=["australia", "india", "china"])  # china module hypothetical
```

UAE patterns load first (jurisdiction priority), Indian patterns load second (diaspora coverage), shared patterns last (catch-all). Priority order is intentional — don't reorder unless you understand the implications.

---

## 📋 Stability guarantees

For v0.1.x:
- Pattern names are stable across patches
- Entity type labels are stable across patches
- New patterns may be ADDED to existing modules
- Patterns will NOT be removed in patch releases
- Pattern semantics (what they match) MAY refine — false-positive reduction is welcome, new entity types are not breaking changes

For v0.2.0+ (future):
- Optional spaCy NER backend for name detection
- More jurisdiction modules (Pakistan · Bangladesh · Sri Lanka · China · Japan · Brazil · Mexico · Canada · etc.)
- Per-member-state EU national-ID variants (currently DE/FR/IT; v0.2 adds ES/NL/BE/PL/AT/others)
- US state-specific driver license + state-court patterns

---

## 🤝 Contributing a jurisdiction

PRs welcome. To accept your contribution:

- Patterns must be sourced (link to official format spec or government regulation)
- Tests must cover at least 3 positive + 1 negative case per pattern
- No real PII ever — synthetic format-realistic only
- README + JURISDICTIONS.md tables updated with new entries
- Pattern naming follows existing conventions

Open an issue first to discuss the jurisdiction + scope, then PR.
