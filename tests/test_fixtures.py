"""
Fixture sweep: every clean example a skill ships must validate to zero errors
AND zero warnings, and every invalid example must reproduce exactly the codes
its sidecar expects -- no more, no fewer, so a new regression can't sneak in
beside an expected one.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcli.schema import validate_file

from tests.conftest import REPO, skill_dirs
from tests import truth


def _clean_fixtures() -> list[Path]:
    out = []
    for skill in skill_dirs():
        fx = skill / "fixtures"
        if not fx.is_dir():
            continue
        for p in sorted(fx.glob("*.json")):
            out.append(p)
    return out


def _invalid_dirs() -> list[Path]:
    return [skill / "fixtures" / "invalid" for skill in skill_dirs()
            if (skill / "fixtures" / "invalid").is_dir()]


def _fixture_id(path: Path) -> str:
    try:
        rel = path.relative_to(REPO)
    except ValueError:
        rel = path
    return str(rel).replace("\\", "/")


@pytest.mark.parametrize("path", _clean_fixtures(), ids=_fixture_id)
def test_clean_fixture_has_no_errors_and_no_warnings(path):
    result = validate_file(str(path))
    assert result.valid, [str(e) for e in result.errors]
    assert not result.warnings, [str(w) for w in result.warnings]


@pytest.mark.parametrize("invalid_dir", _invalid_dirs(), ids=lambda p: _fixture_id(p.parent.parent))
def test_invalid_fixtures_match_their_expected_codes(invalid_dir):
    expected_path = invalid_dir / "expected.json"
    assert expected_path.is_file(), f"{invalid_dir} has no expected.json sidecar"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))

    fixture_files = {p.name for p in invalid_dir.glob("*.json") if p.name != "expected.json"}
    assert fixture_files == set(expected), (
        f"expected.json entries {sorted(expected)} do not match fixture files "
        f"{sorted(fixture_files)} in {invalid_dir}"
    )

    for name, want in expected.items():
        result = validate_file(str(invalid_dir / name))
        got_errors = {e.code for e in result.errors}
        got_warnings = {w.code for w in result.warnings}
        assert got_errors == set(want.get("errors", [])), f"{invalid_dir / name}: errors {got_errors}"
        assert got_warnings == set(want.get("warnings", [])), f"{invalid_dir / name}: warnings {got_warnings}"


def test_every_node_type_has_a_clean_fixture():
    """Makes a coverage regression like the Hitl gap impossible to reintroduce."""
    seen = set()
    for path in _clean_fixtures():
        graph = json.loads(path.read_text(encoding="utf-8"))
        for node in graph.get("nodes", []):
            t = node.get("type")
            if t:
                seen.add(t)
    missing = set(truth.NODE_TYPES) - seen
    assert not missing, f"no clean fixture anywhere exercises: {sorted(missing)}"


def test_every_diagnostic_code_has_a_reproducing_fixture():
    seen = set()
    for invalid_dir in _invalid_dirs():
        expected_path = invalid_dir / "expected.json"
        if not expected_path.is_file():
            continue
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        for want in expected.values():
            seen |= set(want.get("errors", [])) | set(want.get("warnings", []))
    missing = truth.codes() - seen
    if missing:
        pytest.skip(
            f"{len(missing)} code(s) have no reproducing fixture yet: {sorted(missing)} "
            "(tracked, not yet a hard failure -- flip to assert once validation-triage ships)"
        )
