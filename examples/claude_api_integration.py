"""Example: Integrating pseudonymisation-gateway with Anthropic Claude API.

Pattern:
    user input → sanitize() → Claude API call → desanitize() → user sees real names

Run with:
    pip install pseudonymisation-gateway anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python claude_api_integration.py
"""
import os

# Note: this example uses Anthropic's SDK. Adapt to your client of choice.
try:
    import anthropic
except ImportError:
    raise SystemExit("Install: pip install anthropic")

from pseudonymisation_gateway import PseudonymisationGateway


def main() -> None:
    # Single jurisdiction setup
    gw = PseudonymisationGateway(jurisdictions=["uk"])

    client_query = (
        "I'm acting for client AB123456C in a contract dispute. "
        "The opposing party is Mr. James Wilson at james.wilson@example.com. "
        "Filed in [2024] EWHC Comm 1234. Please draft a Reply to Defence."
    )

    # 1. Sanitize before send
    clean, token_map = gw.sanitize(client_query)
    print("Sending to Claude (sanitized):")
    print(clean)
    print()

    # 2. Send only sanitized text to Claude
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY to actually call the API. Showing demo flow only.")
        # Fake response — placeholders preserved across the round-trip
        fake_response = (
            "Reply to Defence:\n"
            "1. The First Defendant Mr. [PERSON_2] denies the allegations.\n"
            "2. Client [NI_NUMBER_1] reserves the right to amend.\n"
            "3. Court case [UK_CASE_1] proceeds.\n"
            "Contact: [EMAIL_1]"
        )
        # 3. Desanitize to show user
        real = gw.desanitize(fake_response, token_map)
        print("User sees (restored):")
        print(real)
        return

    # Real API call
    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": clean}],
    )

    response_text = resp.content[0].text
    real = gw.desanitize(response_text, token_map)
    print("User sees (restored):")
    print(real)


if __name__ == "__main__":
    main()
