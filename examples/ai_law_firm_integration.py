"""Example: How the 7 country AI Law Firms integrate this library.

Each wolfgang_rush AI Law Firm (github.com/Wolfgangrush/ai-law-firm-*) replaces
its in-firm pseudonymisation.py with a 3-line module that delegates to this
gateway:

    # ailawfirm_<country>/pseudonymisation.py
    from pseudonymisation_gateway import PseudonymisationGateway
    from pseudonymisation_gateway.patterns import <country>, india

    def get_default_gateway() -> PseudonymisationGateway:
        # Country-native patterns + Indian diaspora layer
        return PseudonymisationGateway(jurisdictions=[<country>, india])

This file shows the full pattern across all 7 country firms.
"""
from pseudonymisation_gateway import PseudonymisationGateway


# Each firm has its own factory function
def dubai_firm_gateway() -> PseudonymisationGateway:
    """ai-law-firm-dubai — UAE-native + Indian diaspora (Dubai has ~3.4M Indian residents)."""
    return PseudonymisationGateway(jurisdictions=["uae", "india"])


def uk_firm_gateway() -> PseudonymisationGateway:
    """ai-law-firm-uk — UK-native + Indian diaspora (UK has ~1.9M British-Indians)."""
    return PseudonymisationGateway(jurisdictions=["uk", "india"])


def australia_firm_gateway() -> PseudonymisationGateway:
    """ai-law-firm-australia — AU-native + Indian diaspora (AU has ~1M Indian-Australians)."""
    return PseudonymisationGateway(jurisdictions=["australia", "india"])


def usa_firm_gateway() -> PseudonymisationGateway:
    """ai-law-firm-usa — US-native + Indian diaspora (US has ~5.4M Indian-Americans)."""
    return PseudonymisationGateway(jurisdictions=["usa", "india"])


def eu_firm_gateway() -> PseudonymisationGateway:
    """ai-law-firm-eu — EU-native + Indian diaspora (EU has ~2M Indian-diaspora)."""
    return PseudonymisationGateway(jurisdictions=["eu", "india"])


def singapore_firm_gateway() -> PseudonymisationGateway:
    """ai-law-firm-singapore — SG-native + Indian diaspora (SG is ~9.2% Indian)."""
    return PseudonymisationGateway(jurisdictions=["singapore", "india"])


def india_firm_gateway() -> PseudonymisationGateway:
    """ai-law-firm-india — India-only (canonical India patterns, no diaspora overlay needed)."""
    return PseudonymisationGateway(jurisdictions=["india"])


def demo_dubai_handling_indian_client() -> None:
    gw = dubai_firm_gateway()
    matter = (
        "Trade License Transfer:\n"
        "Transferor: Mr. Khalid Al-Mansoori (Emirates ID 784-1985-1234567-8, "
        "UAE phone +971 50 123 4567)\n"
        "Transferee: Mr. Rahul Sharma (Aadhaar 1234 5678 9012, PAN ABCDE1234F)\n"
        "License: DIFC-CL1234. Consideration: AED 250,000."
    )
    clean, tm = gw.sanitize(matter)
    print("=== Sanitized (safe for cloud LLM) ===")
    print(clean)
    print()
    print("=== Token map (in-memory only, never persisted) ===")
    for original, placeholder in tm.forward.items():
        print(f"  {placeholder:<25} ← {original}")


def demo_uk_handling_indian_diaspora_client() -> None:
    gw = uk_firm_gateway()
    matter = (
        "Employment tribunal claim:\n"
        "Claimant: Ms. Priya Patel (NI Number AB123456C, "
        "previous Aadhaar 9876 5432 1098 from India)\n"
        "Respondent: Acme Corp, UTR 1234567890.\n"
        "Filed in [2024] EWHC Comm 567. Claim £45,000."
    )
    clean, tm = gw.sanitize(matter)
    print("=== UK firm handling Indian-British client ===")
    print(clean)
    print()
    print(f"Entities scrubbed: {set(tm.counters.keys())}")


if __name__ == "__main__":
    print("─── DEMO 1: Dubai firm + Indian-expat client ───\n")
    demo_dubai_handling_indian_client()
    print()
    print("─── DEMO 2: UK firm + Indian-British client ───\n")
    demo_uk_handling_indian_diaspora_client()
