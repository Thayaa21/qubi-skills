---
name: qubi-skill-authoring
description: "Write a new skill in this repo so it passes the fixture sweep and claim linter in tests/. Use when adding a new SKILL.md, adding fixtures, or when a skill fails the harness and the fix isn't obvious."
---

# qubi Skill Authoring

> Every skill in this repo is checked by a pytest harness that derives ground truth from the real qubi validator at runtime. This is the reference for passing it, not just for the house style.

## What this skill is

`qubi-skills/tests/` enforces a contract: frontmatter matching the directory, node types and fields that actually exist, diagnostic codes that are real, CLI commands and flags that exist, and no confidently-stated value for a field nobody has confirmed. This skill documents that contract from the author's side. Run `pip install -e ../qcli-web` once (or set `$QCLI_WEB`) before working on any skill -- the harness needs the real validator to check anything.

## When to invoke

- Adding a new skill directory
- A skill fails `python -m pytest` in `qubi-skills/tests/` and the fix isn't obvious
- Adding fixtures to an existing skill

## Required structure

```
my-skill/
├── SKILL.md              # required
├── schema-reference.md   # optional companion
├── examples.md           # optional companion
├── error-handling.md     # optional companion
└── fixtures/
    ├── *.json             # must validate to 0 errors AND 0 warnings
    └── invalid/
        ├── *.json          # each reproduces a specific diagnostic code
        └── expected.json   # {"file.json": {"errors": [...], "warnings": [...]}}
```

`SKILL.md` frontmatter:

```yaml
---
name: my-skill          # MUST equal the directory name, kebab-case, unique repo-wide
description: "..."      # one line, includes trigger phrases
---
```

Required headings: an H1, a `> tagline` blockquote right after it, a `## When to invoke` section, and a rules section matched by `^##\s+(operating\s+)?rules\b` (case-insensitive) -- `## Rules` or `## Operating Rules` both work. Everything else in the house template (What this skill is / What it solves / Phase N: .../ Unverified) is recommended, not enforced -- the four pre-existing skills don't follow it uniformly, and enforcing all of it would fail them on cosmetics.

## Fixtures first, prose second

Write and validate fixtures before writing the SKILL.md prose that references them. A fixture that validates 0/0 is proof the shape you're documenting actually works; prose written first is a hypothesis. Validate directly against the real validator while drafting:

```bash
qubi flow validate my-skill/fixtures/example.json
```

For an invalid fixture, run it and copy the exact codes it produces into `expected.json` -- don't guess the codes, read them:

```bash
qubi flow validate my-skill/fixtures/invalid/example.json -j
```

`expected.json` is checked by **exact set equality**, not subset -- list every code the fixture actually produces, no more, no fewer.

## Six things the linter checks (and why each exists)

1. **Node types and casing** -- `Http` not `HTTP`, `Hitl` not `HITL`. Checked only inside fenced code blocks and inline `` `spans` `` -- prose is never scanned, so writing "you may need to branch the flow" is always safe.
2. **Node `data` fields** -- every key in a node's `data` object must be in that type's required/optional set (plus envelope keys and designer-only round-trip keys like `measured`/`selected`). Catches invented fields.
3. **Diagnostic codes** -- any all-caps underscored token (like `MISSING_START`), in an inline span or heading, must be a real code from `qubi.schema`. `tests/allowlist.py` exempts non-code tokens like environment variable names.
4. **CLI commands and flags** -- every ``` ```bash ``` ``` invocation of the real console script is checked against the live click command tree (walked from the actual `qubi.cli` module, never regexed). This is what catches a wrong binary name or an invented flag.
5. **Frontmatter** -- `name` matches the directory, is kebab-case, and is unique across the repo.
6. **No confident assertion of an unverified value** -- `agentId`, `operation`, `automationId`, `taskType`, `assignTo`, `template` may only appear as the sentinel (`00000000-0000-0000-0000-000000000000` for ids, `UNVERIFIED` for enums), an obvious placeholder, or annotated with a `UV-...` id in the fenced block or the paragraph immediately above it. This is what stops an invented enum value like `"operation": "extract"` from sitting in the repo looking confirmed.

## When a skill touches something nobody can confirm offline

Add a `## Unverified` table:

```markdown
## Unverified

| ID | Claim | Why unverifiable offline | How to verify | Status |
|----|-------|---------------------------|----------------|--------|
| UV-MYAREA-01 | `taskType` accepts a value like `approval` | Designer dropdown; option list not captured | Open the node in the designer and read the dropdown | open |
```

Then regenerate the root roll-up:

```bash
python tools/rollup_unverified.py
```

`test_rollup_is_current` fails if you forget -- nobody hand-edits `UNVERIFIED.md`, so this is the only step required.

## Running the harness

```bash
python -m pytest -q                    # everything
python -m pytest -q -k my-skill        # just your skill
```

If it can't find the validator, it exits with an explicit install hint (`pip install -e ../qcli-web`, or set `$QCLI_WEB`) rather than silently skipping -- a skipped harness is a green build that proves nothing.

## Operating Rules

**Always:**
- Build fixtures first, validate them directly, then write prose around what's proven to work
- Copy diagnostic codes from an actual `qubi flow validate -j` run, never guess them
- Run `tools/rollup_unverified.py` after adding or editing an `## Unverified` table
- Make `name` in frontmatter equal the directory name

**Never:**
- State a value for `agentId`/`operation`/`automationId`/`taskType`/`assignTo`/`template` as if confirmed unless it really is
- Hand-edit `UNVERIFIED.md` -- it's generated
- Reference a CLI command or flag without checking it against `qubi --help` (or the real click tree) first
