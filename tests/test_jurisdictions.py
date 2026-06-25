"""Per-jurisdiction pattern tests."""
import pytest
from pseudonymisation_gateway import PseudonymisationGateway


# ─── India ─────────────────────────────────────────────────────────────

def test_india_aadhaar():
    gw = PseudonymisationGateway(jurisdictions=["india"])
    # 9999 9999 0019 is a UIDAI-published, Verhoeff-valid sample Aadhaar.
    clean, _ = gw.sanitize("Aadhaar 9999 9999 0019 belongs to the client.")
    assert "[AADHAAR_1]" in clean
    assert "9999 9999 0019" not in clean


def test_india_pan():
    gw = PseudonymisationGateway(jurisdictions=["india"])
    # ABFPK1234L: 4th letter 'P' (individual) — a structurally valid PAN.
    clean, _ = gw.sanitize("PAN ABFPK1234L is on file.")
    assert "[PAN_1]" in clean


def test_india_gstin():
    gw = PseudonymisationGateway(jurisdictions=["india"])
    # 27AAPFU0939F1ZV is a checksum-valid GSTIN (state 27, check digit 'V').
    clean, _ = gw.sanitize("GSTIN 27AAPFU0939F1ZV verified.")
    assert "[GSTIN_1]" in clean


def test_india_ifsc():
    gw = PseudonymisationGateway(jurisdictions=["india"])
    clean, _ = gw.sanitize("Bank IFSC SBIN0001234.")
    assert "[IFSC_1]" in clean


# ─── UAE ───────────────────────────────────────────────────────────────

def test_uae_emirates_id():
    gw = PseudonymisationGateway(jurisdictions=["uae"])
    clean, _ = gw.sanitize("Emirates ID 784-1985-1234567-8 attached.")
    assert "[EMIRATES_ID_1]" in clean
    assert "784-1985-1234567-8" not in clean


def test_uae_iban():
    gw = PseudonymisationGateway(jurisdictions=["uae"])
    clean, _ = gw.sanitize("Transfer to AE070331234567890123456 today.")
    assert "[UAE_IBAN_1]" in clean


def test_uae_trade_license():
    gw = PseudonymisationGateway(jurisdictions=["uae"])
    clean, _ = gw.sanitize("Licensee DIFC-CL1234.")
    assert "[TRADE_LICENSE_1]" in clean


def test_uae_difc_case():
    gw = PseudonymisationGateway(jurisdictions=["uae"])
    clean, _ = gw.sanitize("Per [2024] DIFC CFI 023, the court held...")
    assert "[DIFC_CASE_1]" in clean


# ─── Australia ─────────────────────────────────────────────────────────

def test_australia_tfn():
    gw = PseudonymisationGateway(jurisdictions=["australia"])
    clean, _ = gw.sanitize("TFN: 123 456 789 attached.")
    assert "[TFN_1]" in clean


def test_australia_medicare():
    gw = PseudonymisationGateway(jurisdictions=["australia"])
    clean, _ = gw.sanitize("Medicare 1234 56789 0 on file.")
    assert "[MEDICARE_1]" in clean


def test_australia_abn():
    gw = PseudonymisationGateway(jurisdictions=["australia"])
    clean, _ = gw.sanitize("Company ABN 12 345 678 901.")
    assert "[ABN_1]" in clean


def test_australia_hca_case():
    gw = PseudonymisationGateway(jurisdictions=["australia"])
    clean, _ = gw.sanitize("In [2024] HCA 12, the court found...")
    assert "[AU_CASE_1]" in clean


# ─── UK ─────────────────────────────────────────────────────────────────

def test_uk_ni_number():
    gw = PseudonymisationGateway(jurisdictions=["uk"])
    clean, _ = gw.sanitize("Client AB123456C lives here.")
    assert "[NI_NUMBER_1]" in clean


def test_uk_nhs():
    gw = PseudonymisationGateway(jurisdictions=["uk"])
    clean, _ = gw.sanitize("Patient NHS 123 456 7890.")
    assert "[NHS_NUMBER_1]" in clean


def test_uk_utr():
    gw = PseudonymisationGateway(jurisdictions=["uk"])
    clean, _ = gw.sanitize("Tax UTR 1234567890.")
    assert "[UTR_1]" in clean


def test_uk_ewhc_case():
    gw = PseudonymisationGateway(jurisdictions=["uk"])
    clean, _ = gw.sanitize("Per [2024] EWHC Comm 1234, ...")
    assert "[UK_CASE_1]" in clean


# ─── USA ────────────────────────────────────────────────────────────────

def test_usa_ssn():
    gw = PseudonymisationGateway(jurisdictions=["usa"])
    clean, _ = gw.sanitize("SSN 123-45-6789 verified.")
    assert "[SSN_1]" in clean


def test_usa_itin():
    gw = PseudonymisationGateway(jurisdictions=["usa"])
    # 912-70-5678: group number 70 is in the IRS-assigned ITIN range.
    clean, _ = gw.sanitize("ITIN 912-70-5678 on file.")
    assert "[ITIN_1]" in clean


def test_usa_ein():
    gw = PseudonymisationGateway(jurisdictions=["usa"])
    clean, _ = gw.sanitize("Corporate EIN 12-3456789 attached.")
    assert "[EIN_1]" in clean


def test_usa_federal_docket():
    gw = PseudonymisationGateway(jurisdictions=["usa"])
    clean, _ = gw.sanitize("Filed in 1:24-cv-12345.")
    assert "[US_DOCKET_1]" in clean


# ─── EU ────────────────────────────────────────────────────────────────

def test_eu_iban_germany():
    gw = PseudonymisationGateway(jurisdictions=["eu"])
    clean, _ = gw.sanitize("Wire to DE89370400440532013000.")
    assert "[EU_IBAN_1]" in clean


def test_eu_german_tax_id():
    gw = PseudonymisationGateway(jurisdictions=["eu"])
    clean, _ = gw.sanitize("Steuer-ID 12345678901 verified.")
    assert "[DE_TAX_ID_1]" in clean


def test_eu_cjeu_case():
    gw = PseudonymisationGateway(jurisdictions=["eu"])
    clean, _ = gw.sanitize("Per C-456/23, the Court ruled...")
    assert "[CJEU_CASE_1]" in clean


# ─── Singapore ─────────────────────────────────────────────────────────

def test_singapore_nric():
    gw = PseudonymisationGateway(jurisdictions=["singapore"])
    # S1234567D: 'D' is the correct weighted check letter for S1234567.
    clean, _ = gw.sanitize("Client S1234567D attended.")
    assert "[NRIC_1]" in clean


def test_singapore_fin():
    gw = PseudonymisationGateway(jurisdictions=["singapore"])
    # F1234567N: 'N' is the correct weighted check letter for F1234567.
    clean, _ = gw.sanitize("Worker F1234567N on contract.")
    assert "[FIN_1]" in clean


def test_singapore_sgca_case():
    gw = PseudonymisationGateway(jurisdictions=["singapore"])
    clean, _ = gw.sanitize("In [2024] SGCA 12, ...")
    assert "[SG_CASE_1]" in clean
