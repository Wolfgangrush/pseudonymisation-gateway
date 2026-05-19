"""Jurisdiction-specific PII pattern modules.

Each module exposes a `PATTERNS` list of `(re.Pattern, entity_type_label)` tuples.

Currently supported:
    - india      (Aadhaar · PAN · GSTIN · IFSC · ₹ · Indian phone · FIR · vehicle reg · case nums)
    - uae        (Emirates ID · UAE IBAN · Trade License · AED · UAE phone · DIFC/Cassation case nums)
    - australia  (TFN · Medicare · ABN · ACN · BSB · AUD · AU phone · HCA/FCA/state case nums)
    - uk         (NI · NHS · UTR · UK VAT · UK IBAN · GBP · UK phone · EWHC/EWCA/UKSC case nums)
    - usa        (SSN · ITIN · EIN · USD · US phone · driver license · federal docket)
    - eu         (IBAN · EU VAT · EORI · German Steuer-ID · French INSEE · Italian CF · CJEU)
    - singapore  (NRIC · FIN · UEN · CPF · SGD · SG phone · SGCA/SGHC/SGDC case nums)

Use:
    from pseudonymisation_gateway import PseudonymisationGateway
    gw = PseudonymisationGateway(jurisdictions=["uae", "india"])  # UAE + Indian diaspora

Or import modules directly:
    from pseudonymisation_gateway.patterns import uae
    gw = PseudonymisationGateway(jurisdictions=[uae])

Extending: see JURISDICTIONS.md for adding new country patterns.
"""

from . import india, uae, australia, uk, usa, eu, singapore

__all__ = ["india", "uae", "australia", "uk", "usa", "eu", "singapore"]
