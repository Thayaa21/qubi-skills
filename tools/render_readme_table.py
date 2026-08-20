"""
Regenerate the Skills table in README.md from the real skill directories.

The table is itself a claim -- rows must match directories -- so it's
generated the same way UNVERIFIED.md is, rather than hand-maintained.

    python tools/render_readme_table.py           # check + rewrite
    python tools/render_readme_table.py --check   # exit 1 if out of date
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from tests.locate_qcli import resolve as _resolve_qcli  # noqa: E402

try:
    _resolve_qcli()
except RuntimeError as e:
    print(e, file=sys.stderr)
    raise SystemExit(4)

from tests import skillmd  # noqa: E402
from tests.conftest import skill_dirs  # noqa: E402

START = "<!-- SKILLS-TABLE:START -->"
END = "<!-- SKILLS-TABLE:END -->"


def _one_liner(description: str) -> str:
    # descriptions are one sentence, then usage guidance -- keep just the
    # first sentence for the table so rows stay scannable
    first = description.split(". ")[0].strip().rstrip(".")
    return first[0].upper() + first[1:] if first else description


def build_table() -> str:
    lines = ["| Skill | Purpose |", "|-------|---------|"]
    for skill in skill_dirs():
        doc = skillmd.parse(skill / "SKILL.md")
        name = doc.frontmatter.get("name", skill.name)
        desc = doc.frontmatter.get("description", "")
        lines.append(f"| **{name}** | {_one_liner(desc)} |")
    return "\n".join(lines)


def main() -> int:
    check_only = "--check" in sys.argv
    readme = REPO / "README.md"
    text = readme.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print(f"README.md is missing {START} / {END} markers", file=sys.stderr)
        return 1
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    new_text = before + START + "\n" + build_table() + "\n" + END + after
    if new_text == text:
        print("README.md skills table is up to date")
        return 0
    if check_only:
        print("README.md skills table is out of date -- run: python tools/render_readme_table.py", file=sys.stderr)
        return 1
    readme.write_text(new_text, encoding="utf-8", newline="\n")
    print("wrote README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
