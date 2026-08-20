"""
Structural rules for a skill folder.

Deliberately small. Enforcing the full house-style heading template would put
every existing skill red on cosmetics, and a test that is red for cosmetic
reasons gets disabled -- taking the checks that matter with it. Six hard
rules; everything else is reported as a warning summary.
"""
from __future__ import annotations

import re

import pytest

from tests import skillmd
from tests.conftest import REPO, skill_dirs, skill_id

SKILLS = skill_dirs()
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


@pytest.mark.parametrize("skill", SKILLS, ids=skill_id)
def test_frontmatter_is_well_formed(skill):
    doc = skillmd.parse(skill / "SKILL.md")
    assert doc.frontmatter_error is None, doc.frontmatter_error
    assert doc.frontmatter, "SKILL.md has no YAML frontmatter"
    assert doc.frontmatter.get("name"), "frontmatter is missing `name`"
    desc = doc.frontmatter.get("description", "")
    assert desc, "frontmatter is missing `description`"
    assert "\n" not in desc, "description must be a single line"


@pytest.mark.parametrize("skill", SKILLS, ids=skill_id)
def test_frontmatter_name_matches_directory(skill):
    doc = skillmd.parse(skill / "SKILL.md")
    name = doc.frontmatter.get("name", "")
    assert name == skill.name, (
        f"frontmatter name {name!r} does not match directory {skill.name!r}. "
        "Skill selection keys off the name, so a mismatch makes the skill hard "
        "to reason about and impossible to reference by folder."
    )
    assert NAME_RE.match(name), f"{name!r} is not kebab-case"


def test_skill_names_are_unique():
    seen = {}
    for skill in SKILLS:
        doc = skillmd.parse(skill / "SKILL.md")
        name = doc.frontmatter.get("name", skill.name)
        assert name not in seen, f"{skill.name} and {seen[name]} both declare name: {name}"
        seen[name] = skill.name


@pytest.mark.parametrize("skill", SKILLS, ids=skill_id)
def test_has_one_h1_and_a_tagline(skill):
    doc = skillmd.parse(skill / "SKILL.md")
    h1 = [h for h in doc.headings if h[1] == 1]
    assert len(h1) == 1, f"expected exactly one H1, found {len(h1)}"
    assert any(l.startswith("> ") for l in doc.body_lines), "no `> tagline` blockquote"


@pytest.mark.parametrize("skill", SKILLS, ids=skill_id)
def test_has_invocation_and_rules_sections(skill):
    doc = skillmd.parse(skill / "SKILL.md")
    texts = [h[2].lower() for h in doc.headings]
    assert any("when to invoke" in t for t in texts), "no 'When to invoke' section"
    assert any(re.match(r"^(operating\s+)?rules\b", t) for t in texts), \
        "no 'Rules' / 'Operating rules' section"


@pytest.mark.parametrize("skill", SKILLS, ids=skill_id)
def test_relative_links_resolve(skill):
    doc = skillmd.parse(skill / "SKILL.md")
    text = "\n".join(doc.body_lines)
    broken = []
    for target in re.findall(r"\]\(\./([^)#]+)\)", text):
        if not (skill / target).exists():
            broken.append(target)
    assert not broken, f"broken relative links: {broken}"
