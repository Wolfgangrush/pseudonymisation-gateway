"""Pseudonymisation Gateway — jurisdiction-aware PII middleware for legal-tech tools.

Strips PII from user text before any cloud-API call; restores PII in the response.
Session-scoped, in-memory only, token map NEVER persisted to disk.

v0.3 adds layered sanitisation (per-matter parties.json dictionary + optional NER),
tiered residue scan, and a per-call audit log (counts only, never values).

Quick start:

    from pseudonymisation_gateway import PseudonymisationGateway
    from pseudonymisation_gateway.patterns import uae

    gw = PseudonymisationGateway(jurisdictions=[uae, "india"])  # UAE + India diaspora
    clean, token_map = gw.sanitize("Mr. Khalid Al-Mansoori (Emirates ID 784-1985-1234567-8) ...")
    # send `clean` to cloud LLM
    response = cloud_call(clean)
    real = gw.desanitize(response, token_map)
    # show `real` to user

See https://github.com/Wolfgangrush/pseudonymisation-gateway for documentation.
"""

from .core import PseudonymisationGateway, TokenMap, ResidueReport

__version__ = "0.4.0"
__all__ = ["PseudonymisationGateway", "TokenMap", "ResidueReport", "__version__"]
