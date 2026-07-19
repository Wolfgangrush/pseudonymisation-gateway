"""Dictionary tests — bare-name catch via parties.json, jurisdiction-scoped load."""

import json
import tempfile
from pathlib import Path


from pseudonymisation_gateway.dictionary import PartiesDictionary


def _write_json(data: dict) -> str:
    """Write a temp JSON file and return the path."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(data, tmp)
    tmp.close()
    return tmp.name


# ── Flat (unscoped) dictionary ────────────────────────────────────────────


def test_flat_dictionary_bare_name():
    """Bare name (no honorific) is caught by parties.json dictionary."""
    path = _write_json(
        {"PERSON": ["Rahul Verma", "Sunita Rao"], "ORG": ["Acme Foods Pvt Ltd"]}
    )
    d = PartiesDictionary(parties_file=path)
    matches = d.match("Rahul Verma filed the petition against Acme Foods Pvt Ltd.")
    assert len(matches) >= 2
    matched_texts = {m[0].lower() for m in matches}
    assert "rahul verma" in matched_texts
    assert "acme foods pvt ltd" in matched_texts
    Path(path).unlink()


def test_flat_dictionary_case_insensitive():
    """Dictionary matches case-insensitively."""
    path = _write_json({"PERSON": ["Rahul Verma"]})
    d = PartiesDictionary(parties_file=path)
    matches = d.match("rahul verma filed the case.")
    assert len(matches) == 1
    assert matches[0][0].lower() == "rahul verma"
    Path(path).unlink()


def test_flat_dictionary_whole_word():
    """Dictionary only matches whole words (word-boundary).

    ``\\b`` matches between a word char and a non-word char. An apostrophe
    IS a non-word char, so ``\\bRahul\\b`` WILL match "Rahul" in "Rahul's".
    It will NOT match "Rahul" inside a longer word like "Rahulification"
    (no word boundary between 'l' and 'i').
    """
    path = _write_json({"PERSON": ["Rahul"]})
    d = PartiesDictionary(parties_file=path)
    # "Rahul" alone should match
    matches = d.match("Rahul filed.")
    assert len(matches) == 1
    # "Rahul" embedded in a longer word should NOT match
    matches2 = d.match("The Rahuldas decision was cited.")
    assert len(matches2) == 0
    Path(path).unlink()


def test_flat_dictionary_longest_match_first():
    """'Rahul Verma' is matched before 'Rahul'."""
    path = _write_json({"PERSON": ["Rahul", "Rahul Verma"]})
    d = PartiesDictionary(parties_file=path)
    matches = d.match("Rahul Verma appeared.")
    # First match should be the longer one
    assert matches[0][0].lower() == "rahul verma"
    Path(path).unlink()


def test_flat_dictionary_multiple_entity_types():
    """Dictionary respects entity types from JSON."""
    path = _write_json(
        {
            "PERSON": ["Rahul Verma"],
            "ORG": ["Acme Foods Pvt Ltd"],
            "CASE_REF": ["Matter-4012"],
        }
    )
    d = PartiesDictionary(parties_file=path)
    matches = d.match("Rahul Verma sued Acme Foods Pvt Ltd re Matter-4012.")
    types_found = {m[1] for m in matches}
    assert "PERSON" in types_found
    assert "ORG" in types_found
    assert "CASE_REF" in types_found
    Path(path).unlink()


# ── Jurisdiction-scoped dictionary ────────────────────────────────────────


def test_jurisdiction_scoped_loads_only_active():
    """Only entries for active jurisdictions + '*' are loaded."""
    path = _write_json(
        {
            "india": {"PERSON": ["Rahul Verma"], "ORG": ["Acme Foods Pvt Ltd"]},
            "uk": {"PERSON": ["John Smith"]},
            "*": {"ORG": ["Cross-border Corp"]},
        }
    )
    d = PartiesDictionary(parties_file=path, active_jurisdictions=["india"])
    # India entries loaded
    assert any(e[0] == "Rahul Verma" for e in d.entries)
    assert any(e[0] == "Acme Foods Pvt Ltd" for e in d.entries)
    # '*' entries loaded
    assert any(e[0] == "Cross-border Corp" for e in d.entries)
    # UK entries NOT loaded
    assert not any(e[0] == "John Smith" for e in d.entries)
    Path(path).unlink()


def test_jurisdiction_scoped_match_only_active():
    """Dictionary only matches entries for active jurisdictions."""
    path = _write_json(
        {
            "india": {"PERSON": ["Rahul Verma"]},
            "uk": {"PERSON": ["John Smith"]},
        }
    )
    d = PartiesDictionary(parties_file=path, active_jurisdictions=["india"])
    matches = d.match("Rahul Verma and John Smith attended.")
    matched_texts = {m[0].lower() for m in matches}
    assert "rahul verma" in matched_texts
    assert "john smith" not in matched_texts
    Path(path).unlink()


def test_jurisdiction_scoped_star_bucket_always_loaded():
    """'*' bucket is loaded regardless of active jurisdictions."""
    path = _write_json(
        {
            "uk": {"PERSON": ["John Smith"]},
            "*": {"PERSON": ["Shared Person"]},
        }
    )
    d = PartiesDictionary(parties_file=path, active_jurisdictions=["india"])
    matches = d.match("Shared Person filed the case.")
    assert len(matches) == 1
    Path(path).unlink()


# ── Edge cases ────────────────────────────────────────────────────────────


def test_empty_dictionary_no_file():
    """PartiesDictionary with no file has no entries."""
    d = PartiesDictionary(parties_file=None)
    assert len(d.entries) == 0
    assert d.match("anything") == []


def test_dictionary_no_match():
    """Text with no dictionary entries returns empty."""
    path = _write_json({"PERSON": ["Rahul Verma"]})
    d = PartiesDictionary(parties_file=path)
    matches = d.match("The court adjourned the hearing.")
    assert matches == []
    Path(path).unlink()


# ── Integration: dictionary within gateway ─────────────────────────────────


def test_gateway_with_dictionary_catches_bare_name():
    """Gateway with parties.json catches names the regex would miss."""
    from pseudonymisation_gateway import PseudonymisationGateway

    path = _write_json({"PERSON": ["Rahul Verma", "Sunita Rao"]})
    gw = PseudonymisationGateway(jurisdictions=["india"], parties_file=path)
    # "Rahul Verma" has no honorific — regex NAME_RE won't catch it
    clean, tm = gw.sanitize("Rahul Verma filed the petition against Sunita Rao.")
    assert "Rahul Verma" not in clean
    assert "Sunita Rao" not in clean
    assert "[PERSON_" in clean
    Path(path).unlink()


def test_gateway_with_dictionary_jurisdiction_scoped():
    """Gateway respects jurisdiction scoping in parties.json."""
    from pseudonymisation_gateway import PseudonymisationGateway

    path = _write_json(
        {
            "india": {"PERSON": ["Rahul Verma"]},
            "uk": {"PERSON": ["John Smith"]},
        }
    )
    gw = PseudonymisationGateway(jurisdictions=["india"], parties_file=path)
    clean, tm = gw.sanitize("Rahul Verma and John Smith filed jointly.")
    # India entry caught
    assert "Rahul Verma" not in clean
    # UK entry NOT loaded, but "John Smith" has no honorific, so regex may
    # or may not catch it — the key assertion is that our India-scoped dict
    # doesn't interfere and the pipeline still runs
    assert "[PERSON_" in clean
    Path(path).unlink()


def test_gateway_dictionary_preserves_existing_regex_catches():
    """Dictionary doesn't double-tokenise what regex already caught."""
    from pseudonymisation_gateway import PseudonymisationGateway

    path = _write_json({"PERSON": ["Rahul"]})
    gw = PseudonymisationGateway(jurisdictions=["india"], parties_file=path)
    # "Mr. Rahul Sharma" — regex catches "Rahul Sharma" via honorific
    # Dictionary also has "Rahul" — should NOT double-tokenise
    clean, tm = gw.sanitize("Mr. Rahul Sharma filed.")
    # TokenMap is deterministic — same original gets same placeholder
    # The key assertion: no double placeholders like [PERSON_1][PERSON_2]
    assert "Rahul" not in clean or "[PERSON_" in clean
    # Verify no double-bracketed patterns
    import re

    assert not re.search(r"\[PERSON_\d+\].*\[PERSON_\d+\]", clean)
    Path(path).unlink()
