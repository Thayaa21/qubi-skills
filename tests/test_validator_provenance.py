"""
Assert we are testing against the hardened validator, not an older one.

This is the interlock between the two repos. If a future merge in qcli-web
resolves in favour of an older schema.py, these tests go red here and name
the file that was actually loaded -- rather than the skills silently being
checked against a validator that cannot see half the defect classes.
"""
from __future__ import annotations

import qcli.schema as schema

from tests import truth


def _where() -> str:
    return f"loaded validator: {schema.__file__}"


def test_http_methods_match_the_captured_designer_dropdown():
    # schema-extractor captured the designer's Method dropdown as exactly these
    # five. HEAD/OPTIONS were in an older schema.py and are not offered by the
    # platform.
    assert truth.VALID_HTTP_METHODS == {"GET", "POST", "PUT", "DELETE", "PATCH"}, _where()


def test_all_thirteen_node_types_present():
    assert len(truth.NODE_TYPES) == 13, _where()
    assert {"Start", "End", "Agent", "Assign", "Branch", "Code", "DocumentAI",
            "Http", "RPA", "Hitl", "HitlTask", "JsonParser", "TextParser"} == set(truth.NODE_TYPES), _where()


def test_console_encoding_guard_present():
    # Without this, `qcli flow validate` dies with UnicodeEncodeError on a
    # default Windows console before printing anything.
    assert hasattr(schema, "_console_supports"), _where()
    for name in ("OK", "BAD", "WARN", "ARROW"):
        assert hasattr(schema, name), f"{name} missing -- {_where()}"


def test_hardened_diagnostic_codes_present():
    hardened = {
        "UNREACHABLE_NODE", "NO_PATH_TO_END", "DATA_TYPE_MISMATCH",
        "UNKNOWN_DATA_FIELD", "EDGE_ID_MISMATCH", "MISSING_EDGE_ID",
        "DUPLICATE_START", "DUPLICATE_END", "INVALID_NODE_DATA",
        "INVALID_NODE_ID_FORMAT", "MISSING_VIEWPORT", "MISSING_EXECUTION_MODE",
    }
    missing = hardened - truth.codes()
    assert not missing, f"validator is missing {sorted(missing)} -- {_where()}"


def test_every_node_type_allows_description():
    # every designer node has a Description field; a validator that rejects it
    # would fail on any graph downloaded from the platform
    for name, spec in truth.NODE_TYPES.items():
        assert "description" in spec.get("optional", []), f"{name} rejects description -- {_where()}"
