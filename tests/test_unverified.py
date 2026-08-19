"""
The teeth of the "leave room for qubi" mechanism.

Six node data fields are backed by a platform dropdown whose real option list
was never captured (see tests/truth.py::unverified_fields). A skill is
allowed to *discuss* those fields, but not to state a confident value for one
without marking it: a plausible-looking fake ("operation": "extract") is
indistinguishable from a real value, and someone will eventually `flow save`
it. Every fixture/example value for these fields must be a documented
sentinel, a placeholder, or explicitly tagged with a UV-... ledger id.
"""
from __future__ import annotations

import json
import re

import pytest

from tests import skillmd, truth
from tests.conftest import REPO, skill_dirs, skill_id

SKILLS = skill_dirs()
UV_ID_RE = re.compile(r"\bUV-[A-Z0-9]+-\d{2}\b")
PLACEHOLDER_RE = re.compile(
    r"^(\{\{.*\}\}|<.*>|\.\.\.$"
    r"|.*uuid.*"           # e.g. "uuid-from-agents-list", "template-uuid"
    r"|.*-id(-.*)?$"       # e.g. "user-or-group-id", "your-rpa-id-here"
    r")$",
    re.IGNORECASE,
)


def _is_acceptable(field: str, value: str, annotated: bool) -> bool:
    if value in (truth.SENTINEL_UUID, truth.SENTINEL_TEXT):
        return True
    if PLACEHOLDER_RE.match(value):
        return True
    return annotated


@pytest.mark.parametrize("skill", SKILLS, ids=skill_id)
def test_no_confident_assertion_of_unverified_values(skill):
    fields = truth.unverified_fields()
    field_alt = "|".join(re.escape(f) for f in fields)
    pattern = re.compile(rf'"({field_alt})"\s*:\s*"([^"]*)"')

    problems = []
    for md_path in sorted(skill.glob("*.md")):
        doc = skillmd.parse(md_path)
        for fence in doc.fences:
            # a UV- id anywhere in the fence body or the line right before it
            # counts as an annotation for every match inside that fence
            annotated = bool(UV_ID_RE.search(fence.body) or UV_ID_RE.search(fence.preceding))
            for line_offset, line in enumerate(fence.body.splitlines()):
                for m in pattern.finditer(line):
                    field, value = m.group(1), m.group(2)
                    if not _is_acceptable(field, value, annotated):
                        problems.append(
                            f"{md_path.name}:{fence.line + line_offset + 1} "
                            f"asserts {field}={value!r} as if confirmed. "
                            f"Use the sentinel ({truth.SENTINEL_UUID!r} for ids, "
                            f"{truth.SENTINEL_TEXT!r} for enums), a placeholder, "
                            f"or a preceding UV-... ledger id."
                        )
    assert not problems, "\n" + "\n".join(problems)


def test_unverified_field_set_is_derived_and_nonempty():
    # guards the derivation itself: if this ever comes back empty, the
    # capture file moved or its shape changed, and every check above would
    # silently stop checking anything
    fields = truth.unverified_fields()
    assert fields, "unverified_fields() returned nothing -- check schema-extractor capture"
    assert fields == frozenset({"agentId", "operation", "automationId", "taskType", "assignTo", "template"})


def test_rollup_is_current():
    """
    UNVERIFIED.md must match what the generator produces right now -- the
    black --check pattern. Nobody hand-edits it, so 14 parallel skill authors
    never conflict on it; they just forget to regenerate, and this catches
    that.
    """
    import sys
    sys.path.insert(0, str(REPO / "tools"))
    from rollup_unverified import build

    target = REPO / "UNVERIFIED.md"
    assert target.is_file(), "UNVERIFIED.md is missing -- run: python tools/rollup_unverified.py"
    current = target.read_text(encoding="utf-8")
    expected = build()
    assert current == expected, (
        "UNVERIFIED.md is out of date. Run: python tools/rollup_unverified.py"
    )
