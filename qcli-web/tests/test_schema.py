"""
Validation regression suite for qcli/schema.py.

The `invalid/` fixtures are the ten adversarial graphs that all returned
valid=True before the validator was hardened, plus a few extras. Each asserts
the exact codes we expect, so a regression shows up as a named diff rather than
a silent pass.
"""

import json
from pathlib import Path

import pytest

from qcli.schema import (
    NODE_TYPES,
    VALID_CODE_LANGUAGES,
    VALID_HTTP_METHODS,
    validate_file,
    validate_graph,
)

FIXTURES = Path(__file__).parent / "fixtures"
VALID_DIR = FIXTURES / "valid"
INVALID_DIR = FIXTURES / "invalid"
REPO_ROOT = Path(__file__).resolve().parents[1]


def codes(items):
    return {item.code for item in items}


# ---------------------------------------------------------------------------
# Valid fixtures must be completely clean — no errors AND no warnings
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", sorted(VALID_DIR.glob("*.json")), ids=lambda p: p.name)
def test_valid_fixtures_are_clean(path):
    result = validate_file(path)
    assert result.valid, f"unexpected errors: {[str(e) for e in result.errors]}"
    assert not result.warnings, f"unexpected warnings: {[str(w) for w in result.warnings]}"


# ---------------------------------------------------------------------------
# Invalid fixtures — expected codes per file
#
# "errors" / "warnings" are subsets that MUST be present. Extra codes are
# tolerated except where noted by test_no_unexpected_errors below.
# ---------------------------------------------------------------------------

EXPECTATIONS = {
    # The worst hole: the skill's hardest rule is "never invent an agentId",
    # yet a node with no agentId at all used to validate clean.
    "agent_data_null.json": {
        "errors": {"MISSING_REQUIRED_FIELD"},
        "warnings": {"INVALID_NODE_DATA", "DATA_TYPE_MISMATCH"},
    },
    "data_type_mismatch.json": {"errors": set(), "warnings": {"DATA_TYPE_MISMATCH"}},
    "no_edges.json": {"errors": set(), "warnings": {"UNREACHABLE_NODE"}},
    "orphan_node.json": {"errors": set(), "warnings": {"UNREACHABLE_NODE"}},
    "duplicate_start.json": {"errors": set(), "warnings": {"DUPLICATE_START"}},
    "edge_missing_id.json": {"errors": set(), "warnings": {"MISSING_EDGE_ID"}},
    "bad_node_id_format.json": {"errors": set(), "warnings": {"INVALID_NODE_ID_FORMAT"}},
    "missing_canvas_keys.json": {
        "errors": set(),
        "warnings": {"MISSING_VIEWPORT", "MISSING_EXECUTION_MODE"},
    },
    # Used to raise AttributeError: 'int' object has no attribute 'upper'
    "http_method_not_string.json": {"errors": {"INVALID_HTTP_METHOD"}, "warnings": set()},
    "unknown_data_fields.json": {"errors": set(), "warnings": {"UNKNOWN_DATA_FIELD"}},
    # HEAD was permitted by schema.py but is absent from the designer's dropdown
    "http_method_head.json": {"errors": {"INVALID_HTTP_METHOD"}, "warnings": set()},
    "assorted_errors.json": {
        "errors": {"UNKNOWN_NODE_TYPE", "DUPLICATE_NODE_ID", "SELF_LOOP",
                   "INVALID_EDGE_TARGET"},
        "warnings": set(),
    },
}


@pytest.mark.parametrize("name", sorted(EXPECTATIONS), ids=str)
def test_invalid_fixtures_report_expected_codes(name):
    result = validate_file(INVALID_DIR / name)
    expected = EXPECTATIONS[name]

    missing_errors = expected["errors"] - codes(result.errors)
    assert not missing_errors, f"{name}: expected errors not raised: {missing_errors}"

    missing_warnings = expected["warnings"] - codes(result.warnings)
    assert not missing_warnings, f"{name}: expected warnings not raised: {missing_warnings}"

    # Any fixture with expected errors must fail the exit code, and vice versa
    assert result.valid is (not expected["errors"]), (
        f"{name}: valid={result.valid} but expected_errors={expected['errors']}"
    )


def test_no_fixture_crashes_the_validator():
    """Every fixture must return a result rather than raise."""
    for path in sorted(INVALID_DIR.glob("*.json")) + sorted(VALID_DIR.glob("*.json")):
        validate_file(path)


# ---------------------------------------------------------------------------
# File-level codes
# ---------------------------------------------------------------------------

def test_missing_file():
    result = validate_file(FIXTURES / "does_not_exist.json")
    assert not result.valid
    assert codes(result.errors) == {"FILE_NOT_FOUND"}


def test_malformed_json():
    result = validate_file(INVALID_DIR / "malformed.json.txt")
    assert not result.valid
    assert codes(result.errors) == {"INVALID_JSON"}


@pytest.mark.parametrize("graph,code", [
    ("not a dict", "INVALID_FORMAT"),
    ({"edges": []}, "MISSING_NODES"),
    ({"nodes": "nope", "edges": []}, "INVALID_NODES"),
    ({"nodes": []}, "MISSING_EDGES"),
    ({"nodes": ["nope"], "edges": []}, "INVALID_NODE"),
    ({"nodes": [], "edges": []}, "MISSING_START"),
])
def test_top_level_structure_codes(graph, code):
    assert code in codes(validate_graph(graph).errors)


def test_missing_node_id_and_type():
    graph = {"nodes": [{"data": {"name": "x"}}], "edges": []}
    found = codes(validate_graph(graph).errors)
    assert {"MISSING_NODE_ID", "MISSING_NODE_TYPE"} <= found


def test_edge_source_and_target_codes():
    start = {"id": "11111111-1111-4111-8111-111111111111", "type": "Start",
             "position": {"x": 0, "y": 0}, "data": {"type": "Start", "name": "Start"}}
    end = {"id": "22222222-2222-4222-8222-222222222222", "type": "End",
           "position": {"x": 9, "y": 0}, "data": {"type": "End", "name": "End"}}
    graph = {"nodes": [start, end], "edges": [{"id": "e"}, "not-an-edge"]}
    found = codes(validate_graph(graph).errors)
    assert {"MISSING_EDGE_SOURCE", "MISSING_EDGE_TARGET", "INVALID_EDGE"} <= found


def test_missing_position_is_a_warning_not_an_error():
    graph = {
        "nodes": [
            {"id": "11111111-1111-4111-8111-111111111111", "type": "Start",
             "data": {"type": "Start", "name": "Start"}},
            {"id": "22222222-2222-4222-8222-222222222222", "type": "End",
             "data": {"type": "End", "name": "End"}},
        ],
        "edges": [{"id": "xy-edge__11111111-1111-4111-8111-111111111111-"
                         "22222222-2222-4222-8222-222222222222",
                   "source": "11111111-1111-4111-8111-111111111111",
                   "target": "22222222-2222-4222-8222-222222222222"}],
        "viewport": {"x": 0, "y": 0, "zoom": 1},
        "executionMode": "Sequential",
    }
    result = validate_graph(graph)
    assert result.valid
    assert "MISSING_POSITION" in codes(result.warnings)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

def test_http_methods_match_the_designer_dropdown():
    """The designer's Method select offers exactly these five."""
    assert VALID_HTTP_METHODS == {"GET", "POST", "PUT", "DELETE", "PATCH"}


def test_code_languages():
    assert VALID_CODE_LANGUAGES == {"javascript", "python"}


@pytest.mark.parametrize("lang", ["ruby", 42])
def test_invalid_code_language(lang):
    graph = json.loads((VALID_DIR / "code_processing.json").read_text(encoding="utf-8"))
    for node in graph["nodes"]:
        if node["type"] == "Code":
            node["data"]["language"] = lang
    result = validate_graph(graph)
    assert not result.valid
    assert "INVALID_CODE_LANGUAGE" in codes(result.errors)


# ---------------------------------------------------------------------------
# Contract: NODE_TYPES must not drift from the captured designer schema
# (SDD §10.3 / §12.5 — NODE_TYPES was hand-transcribed and nothing re-checks it)
# ---------------------------------------------------------------------------

# The extractor records UI labels; NODE_TYPES uses the code names that appear
# in the serialised graph. This is the only sanctioned difference.
UI_LABEL_TO_CODE_NAME = {
    "HTTP": "Http",
    "Human In The Loop": "Hitl",
    "HITL Task": "HitlTask",
}

EXTRACTOR_OUTPUT = REPO_ROOT / "schema-extractor" / "output" / "element_properties.json"


@pytest.mark.skipif(not EXTRACTOR_OUTPUT.exists(), reason="extractor output not present")
def test_node_types_match_captured_designer_schema():
    captured = json.loads(EXTRACTOR_OUTPUT.read_text(encoding="utf-8"))
    captured_names = {UI_LABEL_TO_CODE_NAME.get(k, k) for k in captured}

    assert captured_names == set(NODE_TYPES), (
        "NODE_TYPES has drifted from the captured designer schema.\n"
        f"  only in extractor: {sorted(captured_names - set(NODE_TYPES))}\n"
        f"  only in NODE_TYPES: {sorted(set(NODE_TYPES) - captured_names)}"
    )


@pytest.mark.skipif(not EXTRACTOR_OUTPUT.exists(), reason="extractor output not present")
def test_every_node_type_accepts_description():
    """Every node in the designer has a Description input."""
    for name, spec in NODE_TYPES.items():
        assert "description" in spec["optional"], f"{name} is missing 'description'"


def test_captured_payload_parses_and_validates():
    """The real captured save payload must run through the validator.

    It reports MISSING_REQUIRED_FIELD legitimately — it is a snapshot of one of
    each node dropped on the canvas with nothing configured — but it must not
    crash, and it must not produce UNKNOWN_NODE_TYPE, which would mean drift.
    """
    sample = REPO_ROOT / "schema-extractor" / "output" / "save_payload_sample.json"
    if not sample.exists():
        pytest.skip("captured payload not present")
    payload = json.loads(sample.read_text(encoding="utf-8"))
    graph = json.loads(payload["payload"]["graphJson"])

    result = validate_graph(graph)
    assert "UNKNOWN_NODE_TYPE" not in codes(result.errors), (
        "captured graph contains a node type NODE_TYPES does not know about"
    )
    assert codes(result.errors) <= {"MISSING_REQUIRED_FIELD"}


# ---------------------------------------------------------------------------
# Platform IDs must not be format-checked
# ---------------------------------------------------------------------------

def test_non_rfc_platform_ids_are_accepted():
    """qubi's agentId values are .NET sequential GUIDs, not RFC-4122 v4.

    e9af665c-6bd1-4644-6333-08dee4aa9ecc has variant nibble '6', which strict
    uuid4 validation would reject. It is a real, working agent id.
    """
    result = validate_file(VALID_DIR / "simple_agent.json")
    assert result.valid
    assert not result.warnings
