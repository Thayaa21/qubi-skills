"""
Parser for skill markdown.

Rule 0, and it is the whole game: **prose is never scanned.** Only fenced
code blocks and inline `code` spans are visible to the linter. A sentence
like "you may need to branch the flow before the human review step" must not
trip the Branch/Hitl checks, or the team will disable the linter within a
week and lose the checks that matter.
"""
from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

FENCE_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<ticks>`{3,}|~{3,})[ \t]*(?P<info>[^\s`]*)")
INLINE_RE = re.compile(r"`([^`\n]+)`")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass
class Fence:
    info: str
    body: str
    line: int          # 1-based line of the opening fence
    preceding: str     # the non-blank line above the fence, for UV- annotations


@dataclass
class SkillDoc:
    path: Path
    frontmatter: dict = field(default_factory=dict)
    frontmatter_error: str | None = None
    fences: list[Fence] = field(default_factory=list)
    inline: list[tuple[int, str]] = field(default_factory=list)   # (line, text)
    headings: list[tuple[int, int, str]] = field(default_factory=list)  # (line, level, text)
    body_lines: list[str] = field(default_factory=list)

    # -- convenience ------------------------------------------------------

    def fences_with(self, *infos: str) -> list[Fence]:
        wanted = {i.lower() for i in infos}
        return [f for f in self.fences if f.info.lower() in wanted]

    def json_fences(self) -> list[tuple[Fence, object]]:
        """Fences that parse as JSON, whether or not they are tagged json."""
        out = []
        for f in self.fences:
            if f.info.lower() not in ("", "json", "jsonc"):
                continue
            text = f.body.strip()
            if not text.startswith(("{", "[")):
                continue
            try:
                out.append((f, json.loads(text)))
            except ValueError:
                continue
        return out

    def inline_tokens(self) -> list[tuple[int, str]]:
        return self.inline


def parse(path: Path) -> SkillDoc:
    raw = io.open(path, encoding="utf-8").read()
    lines = raw.split("\n")
    doc = SkillDoc(path=path)

    i = 0
    # --- frontmatter ---
    if lines and lines[0].strip() == "---":
        j = 1
        while j < len(lines) and lines[j].strip() != "---":
            j += 1
        if j < len(lines):
            for fl in lines[1:j]:
                if not fl.strip() or fl.lstrip().startswith("#"):
                    continue
                key, sep, value = fl.partition(":")
                if not sep:
                    continue
                v = value.strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                doc.frontmatter[key.strip()] = v
            i = j + 1
        else:
            doc.frontmatter_error = "unterminated frontmatter block"

    doc.body_lines = lines

    # --- fences, inline spans, headings ---
    while i < len(lines):
        line = lines[i]
        m = FENCE_RE.match(line)
        if m and m.group("ticks"):
            ticks = m.group("ticks")
            info = m.group("info") or ""
            open_line = i + 1
            # the full paragraph immediately above the fence (skip trailing
            # blank lines, then take every contiguous non-blank line above
            # that), so a UV-... annotation can span a multi-line comment
            # block and still be found
            preceding_lines: list[str] = []
            k = i - 1
            while k >= 0 and not lines[k].strip():
                k -= 1
            while k >= 0 and lines[k].strip():
                preceding_lines.append(lines[k])
                k -= 1
            preceding = "\n".join(reversed(preceding_lines))
            i += 1
            body = []
            close = ticks[0] * len(ticks)
            while i < len(lines) and not lines[i].strip().startswith(close):
                body.append(lines[i])
                i += 1
            i += 1  # consume closing fence
            doc.fences.append(Fence(info=info, body="\n".join(body), line=open_line, preceding=preceding))
            continue

        h = HEADING_RE.match(line)
        if h:
            doc.headings.append((i + 1, len(h.group(1)), h.group(2).strip()))

        for span in INLINE_RE.findall(line):
            doc.inline.append((i + 1, span))
        i += 1

    return doc


def walk_json(obj, path=""):
    """Yield every (path, dict) in a parsed JSON structure."""
    if isinstance(obj, dict):
        yield path, obj
        for k, v in obj.items():
            yield from walk_json(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for idx, v in enumerate(obj):
            yield from walk_json(v, f"{path}[{idx}]")
