"""
Fails a skill when it documents something that does not exist: a node type
that isn't real, a field a node doesn't accept, a diagnostic code the
validator never emits, or a CLI command/flag that isn't in the click tree.

Rule 0 governs everything here: only fenced code blocks and inline `code`
spans are inspected. Prose is never scanned, so a sentence like "you may
need to branch the flow before the human review step" cannot trip the
Branch/Hitl checks.
"""
from __future__ import annotations

import re
import shlex

import pytest

from tests import skillmd, truth
from tests.allowlist import NON_CODE_TOKENS, RULE_EXEMPTIONS
from tests.conftest import skill_dirs, skill_id

SKILLS = skill_dirs()
CODE_TOKEN_RE = re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b")


def _exempt(skill_name: str, rule: str) -> str | None:
    return RULE_EXEMPTIONS.get(skill_name, {}).get(rule)


# --- Rule 1 & 2: node types and node data fields ---------------------------

@pytest.mark.parametrize("skill", SKILLS, ids=skill_id)
def test_documented_node_types_and_fields_are_real(skill):
    reason = _exempt(skill.name, "node_fields")
    if reason:
        pytest.skip(reason)

    problems = []
    for md_path in sorted(skill.glob("*.md")):
        doc = skillmd.parse(md_path)

        for fence, obj in doc.json_fences():
            for path, node in skillmd.walk_json(obj):
                t = node.get("type")
                if not isinstance(t, str) or t not in truth.NODE_TYPES:
                    continue  # not a node object (or not one we recognise the type of)
                data = node.get("data")
                if not isinstance(data, dict):
                    continue
                allowed = truth.allowed_data_keys(t) | truth.ENVELOPE_KEYS | truth.DESIGNER_ONLY_KEYS
                extra = set(data) - allowed
                if extra:
                    problems.append(
                        f"{md_path.name}:{fence.line} node type {t!r} data has "
                        f"unknown field(s) {sorted(extra)} (path {path or '.'})"
                    )
                missing = truth.required(t) - set(data)
                # only flag missing-required on objects that look complete
                # (have more than just name+type -- an intentionally partial
                # snippet showing one field shouldn't trip this)
                if missing and len(data) >= len(truth.required(t)):
                    problems.append(
                        f"{md_path.name}:{fence.line} node type {t!r} is missing "
                        f"required field(s) {sorted(missing)}"
                    )

        # inline spans: a near-miss on a real type's casing (HTTP, Rpa, ...).
        # Two false-positive classes to guard against:
        #  - an all-lowercase span is almost always a field name or plain
        #    English word ("code", "start", "end") coinciding with a type's
        #    lowercase form, not an attempted type reference
        #  - a line that already shows the correct form alongside the wrong
        #    one ("`Http` not `HTTP`") is teaching the correction, not
        #    committing the mistake
        spans_by_line: dict[int, set[str]] = {}
        for line_no, span in doc.inline_tokens():
            spans_by_line.setdefault(line_no, set()).add(span)

        for line_no, span in doc.inline_tokens():
            if span in truth.NODE_TYPES or span.islower():
                continue
            for real in truth.NODE_TYPES:
                if span.lower() == real.lower() and span != real:
                    if real in spans_by_line.get(line_no, ()):
                        break  # correct form is right there -- this is a worked example
                    problems.append(f"{md_path.name}:{line_no} {span!r} should be {real!r} (exact casing matters)")

    assert not problems, "\n" + "\n".join(problems)


# --- Rule 3: diagnostic codes ----------------------------------------------

@pytest.mark.parametrize("skill", SKILLS, ids=skill_id)
def test_documented_error_and_warning_codes_are_real(skill):
    reason = _exempt(skill.name, "codes")
    if reason:
        pytest.skip(reason)

    known = truth.codes()
    problems = []
    for md_path in sorted(skill.glob("*.md")):
        doc = skillmd.parse(md_path)
        candidates = list(doc.inline_tokens())
        candidates += [(ln, text) for ln, _lvl, text in doc.headings]
        for line_no, text in candidates:
            for tok in CODE_TOKEN_RE.findall(text):
                if tok in known or tok in NON_CODE_TOKENS:
                    continue
                problems.append(f"{md_path.name}:{line_no} {tok!r} is not a known diagnostic code")
    assert not problems, "\n" + "\n".join(problems)


# --- Rule 4: CLI commands and flags -----------------------------------------

_PLACEHOLDER_RE = re.compile(r"^(<.*>|\{.*\}|\$.*|\".*\"|'.*')$")


def _command_segments(fence_body: str):
    for raw_line in fence_body.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        for part in re.split(r"&&|\|\||\||;", line):
            part = part.strip()
            if part:
                yield part


@pytest.mark.parametrize("skill", SKILLS, ids=skill_id)
def test_documented_commands_and_flags_are_real(skill):
    reason = _exempt(skill.name, "cli")
    if reason:
        pytest.skip(reason)

    binaries = truth.binary_names()
    tree = truth.command_tree()
    problems = []

    for md_path in sorted(skill.glob("*.md")):
        doc = skillmd.parse(md_path)
        for fence in doc.fences_with("bash", "sh", "shell", "console"):
            for segment in _command_segments(fence.body):
                try:
                    tokens = shlex.split(segment, posix=False)
                except ValueError:
                    continue
                if not tokens:
                    continue
                binary = tokens[0]
                if binary not in binaries:
                    if binary in ("qubi",) and binary not in binaries:
                        problems.append(
                            f"{md_path.name}:{fence.line} invokes {binary!r}, "
                            f"but the installed console script is {sorted(binaries)}"
                        )
                    continue  # not a qcli invocation (pip, python, etc.)

                # Walk tokens into the command path only while they extend a
                # real group/command prefix, and stop as soon as the path
                # matches a leaf command -- everything after that is a
                # positional argument (a workflow id, a number, a file path),
                # not part of the command name, so `flow use 3` must resolve
                # to ("flow", "use") with "3" left alone.
                path = []
                idx = 1
                while idx < len(tokens):
                    tok = tokens[idx]
                    if tok.startswith("-") or _PLACEHOLDER_RE.match(tok) or "/" in tok or tok.endswith(".json"):
                        break
                    candidate = tuple(path + [tok])
                    if candidate in tree:
                        path = list(candidate)
                        idx += 1
                        break  # matched a full command; remainder is arguments
                    if any(k[:len(candidate)] == candidate for k in tree):
                        path = list(candidate)
                        idx += 1
                        continue
                    break  # tok doesn't extend any known command
                path_t = tuple(path)

                if path_t not in tree:
                    # try progressively shorter prefixes to report the exact
                    # failing segment (e.g. "flow" alone is a valid group)
                    problems.append(
                        f"{md_path.name}:{fence.line} `{binary} {' '.join(path)}` "
                        f"is not a real command"
                    )
                    continue

                allowed_flags = tree[path_t]
                for tok in tokens[idx:]:
                    if tok == "-":
                        continue  # bare "-" is a stdin/stdout placeholder, not a flag
                    flag = tok.split("=", 1)[0]
                    if flag.startswith("-") and flag not in allowed_flags:
                        problems.append(
                            f"{md_path.name}:{fence.line} `{binary} {' '.join(path)}` "
                            f"does not accept {flag!r} (has {sorted(allowed_flags)})"
                        )

    assert not problems, "\n" + "\n".join(problems)
