"""Example: Integrating pseudonymisation-gateway with OpenAI API.

Same pattern as the Claude example. Plug your SDK of choice in.
"""
import os

try:
    from openai import OpenAI
except ImportError:
    raise SystemExit("Install: pip install openai")

from pseudonymisation_gateway import PseudonymisationGateway


def main() -> None:
    # Dubai firm handling Indian-expat client — UAE + India diaspora coverage
    gw = PseudonymisationGateway(jurisdictions=["uae", "india"])

    client_query = (
        "Drafting a Trade License Transfer Agreement. "
        "Transferor: Mr. Khalid Al-Mansoori (Emirates ID 784-1985-1234567-8). "
        "Transferee: Mr. Rahul Sharma (Aadhaar 1234 5678 9012, PAN ABCDE1234F). "
        "Subject license: DIFC-CL1234. Consideration: AED 250,000. "
        "Please draft Clause 3 (Representations and Warranties)."
    )

    # 1. Sanitize
    clean, token_map = gw.sanitize(client_query)

    # Pre-flight: confirm nothing slipped past
    safe, detected_remaining = gw.is_safe_for_cloud(clean)
    if not safe:
        raise RuntimeError(f"PII leaked past sanitize(): {detected_remaining}")

    print("✓ Pre-flight clean — safe to send")
    print(f"  Token map size: {len(token_map.forward)} entities scrubbed")
    print(f"  Categories: {set(token_map.counters.keys())}")
    print()

    # 2. Send to OpenAI (skipping actual call in demo)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # Demo with simulated response
        fake_response = (
            "Clause 3 — Representations and Warranties:\n"
            "3.1 [PERSON_1] warrants that license [TRADE_LICENSE_1] is in good standing.\n"
            "3.2 [PERSON_2] warrants that the consideration of [AED_AMOUNT_1] has been paid.\n"
            "3.3 Both parties confirm Emirates ID [EMIRATES_ID_1] and Aadhaar [AADHAAR_1] are valid.\n"
        )
        real = gw.desanitize(fake_response, token_map)
        print(real)
        return

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": clean}],
    )
    real = gw.desanitize(resp.choices[0].message.content, token_map)
    print(real)


if __name__ == "__main__":
    main()
