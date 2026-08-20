# README1 — What Changed in This Push (Rishi / Skills track)

This push adds two things to the `Rishi` branch:

1. **`qcli-web/`** — the full qcli web-track project (Python CLI + skill files + tests),
   added as a new top-level folder. Nothing existing in this repo (`README.md`,
   `document-to-workflow/`, `workflow-builder/`, `workflow-optimizer/`) was deleted or
   overwritten.
2. **Fixes to `workflow-builder/SKILL.md`, `error-handling.md`, `schema-reference.md`**
   — the same fixes applied to `qcli-web/skills/`, ported over since this folder is the
   pre-existing analog of that skill.

## Why: the validator was passing broken graphs

Before this push, `qcli/schema.py` (the offline validator behind `qcli flow validate`)
had real holes. Confirmed by direct testing:

| Input | Before | After |
|---|---|---|
| Agent node with `"data": null` (agentId is required) | **valid, 0 errors** | `MISSING_REQUIRED_FIELD` |
| `type: "Http"` node with `data.type: "Agent"` | valid | `DATA_TYPE_MISMATCH` warning |
| Graph with zero edges connecting anything | valid | `UNREACHABLE_NODE` warning |
| Two `Start` nodes | valid | `DUPLICATE_START` warning |
| `"method": 123` (not a string) | **crashed with AttributeError** | `INVALID_HTTP_METHOD` error |
| Typo'd field `saveOutputas` instead of `saveOutputAs` | valid, silently ignored | `UNKNOWN_DATA_FIELD` warning |

The worst one: the skill's hardest rule is *"never invent an agentId"* — and a node
with no `agentId` at all used to pass validation clean. The fix-and-retry loop the
skill promises (write → validate → fix → retry) was giving false confidence.

Also fixed: `qcli flow validate` and `qcli login` crashed with `UnicodeEncodeError`
on a plain Windows console (cp1252), because they printed hardcoded `✓`/`✗` glyphs.
They now fall back to `OK`/`X` when the console can't encode Unicode.

## What's in `qcli-web/`

```
qcli-web/
├── qcli/               # the CLI itself (schema.py validator, flow/login commands, HTTP client)
├── skills/              # SKILL.md + schema-reference.md + examples.md + error-handling.md
├── tests/               # pytest suite — one fixture per error/warning code, plus a
│                         # contract test that catches NODE_TYPES drifting from the
│                         # captured designer schema
├── docs/                 # design docs (SDD, API reference, graph schema spec)
└── schema-extractor/     # the Playwright script + captured payloads used as ground truth
```

Run the tests: `cd qcli-web && pip install pytest && python -m pytest tests/ -v`
(35 tests, all passing as of this push.)

## Skill-file changes (both `qcli-web/skills/` and `workflow-builder/`)

- Linked the `schema-reference.md` / `examples.md` / `error-handling.md` companion
  files from `SKILL.md` — they existed but were never referenced from the main file,
  so an agent reading only `SKILL.md` never learned they existed.
- Synced the error table with every code the validator can actually emit (previously
  documented 11 of 23).
- Dropped `HEAD`/`OPTIONS` from the allowed HTTP methods — the real designer's Method
  dropdown only offers `GET, POST, PUT, DELETE, PATCH`; `schema.py` and the skill both
  incorrectly allowed two more.
- Added a warnings section: warnings don't fail `qcli flow validate`'s exit code, but
  the skill now explicitly says to treat them as must-fix before asking a human to save.
- Added a "Phase 0" recommending `qcli flow get <id>` and editing that file, rather
  than authoring a graph from scratch — the downloaded graph carries designer-only
  fields (`measured`, `selected`) that a hand-authored one won't have.

## Known limitations (unchanged, documented, not addressed by this push)

- `qcli login` doesn't complete the OAuth2 PKCE flow, so it authenticates against the
  wrong host. `qcli login --browser` works around it. See `qcli-web/docs/SDD.md` §12.1.
- `flow run` / job-status endpoints are inferred, never confirmed against live traffic.
- There is no `flow create` — `flow save` only writes into an existing workflow ID.
