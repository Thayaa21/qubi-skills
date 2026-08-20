"""
README.md's skills table is itself a claim -- rows must match directories --
so it's checked the same way UNVERIFIED.md is: generated, never hand-edited,
with a test asserting the checked-in file matches the generator.
"""
from __future__ import annotations

import sys

from tests.conftest import REPO


def test_readme_skills_table_is_current():
    sys.path.insert(0, str(REPO / "tools"))
    from render_readme_table import START, END, build_table

    text = (REPO / "README.md").read_text(encoding="utf-8")
    assert START in text and END in text, f"README.md is missing {START} / {END} markers"
    before, rest = text.split(START, 1)
    current, after = rest.split(END, 1)
    expected = "\n" + build_table() + "\n"
    assert current == expected, "README.md skills table is out of date -- run: python tools/render_readme_table.py"
