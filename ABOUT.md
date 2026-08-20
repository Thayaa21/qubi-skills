# About qubi-skills

> A reference for what this project is, why it exists, and how it fits alongside
> the qubi CLI and web projects. Read this first if you're new to the repo, or if
> you've placed `qubi-skills/` inside a larger workspace and need to understand its
> role.

## What this project is

**qubi-skills** is a repository of **AI agent skills** for building qubi Agentic
Flows workflows. A "skill" is a self-contained package of markdown instructions
(and validated example fixtures) that teaches an AI coding agent — Claude Code,
Kiro, Cursor, and others — how to perform one specific qubi task correctly.

It is modeled on [UiPath's Agent Skills](https://github.com/UiPath/skills): each
skill is a folder, the AI reads it on demand, and skills are self-contained (no
skill depends on another). The AI reads the skill, follows its rules, and produces
correct workflow JSON that passes the qubi validator.

This repo contains **only the skills and their test harness**. It does not contain
the CLI implementation or the web platform — those live in separate projects (see
"How it fits with the other projects" below).

## Why it exists

qubi Agentic Flows are authored as a JSON graph (nodes + edges). Getting that JSON
right by hand is error-prone: there are 13 node types, each with specific required
fields, exact type-name casing (`Http` not `HTTP`), enum constraints, and a set of
dropdown fields whose values can't be invented. An AI agent without guidance guesses
— and guesses wrong.

These skills encode the ground truth so an agent can:

- Know which node types exist and what each requires
- Write graphs that pass `qcli flow validate` with zero errors and zero warnings
- Follow the exact CLI command sequence to validate, save, and run a workflow
- Discover platform resources (agent IDs, automation IDs) instead of fabricating them
- Fix validation errors on its own using a documented error → fix mapping

The guiding principle is **truth-anchoring**: every claim in a skill is meant to be
backed by a captured designer schema or a passing fixture, not by what seems
plausible. Where something can't be verified offline, it is marked `UNVERIFIED`
rather than guessed (see `UNVERIFIED.md`).

## Repository structure

```
qubi-skills/
├── README.md                  # Skill catalog (auto-generated table) + usage
├── ABOUT.md                   # This file — project overview and orientation
├── README1.md                 # Changelog note for the validator-hardening push
├── UNVERIFIED.md              # Rolled-up list of claims that need a live server to confirm
├── pyproject.toml             # Python project config for the test harness
│
├── <skill-name>/              # One folder per skill (see catalog below)
│   ├── SKILL.md               # Entry point: frontmatter + when-to-invoke + rules + phases
│   ├── schema-reference.md    # (optional) full field list per node type
│   ├── examples.md            # (optional) complete validated example graphs
│   ├── error-handling.md      # (optional) validation error → fix mapping
│   └── fixtures/
│       ├── *.json             # valid graphs — must validate to 0 errors AND 0 warnings
│       └── invalid/
│           ├── *.json         # each reproduces one specific diagnostic code
│           └── expected.json  # the codes each invalid fixture must produce
│
├── tests/                     # pytest harness — validates skills against the real validator
│   ├── test_fixtures.py       # every fixture validates as claimed
│   ├── test_skill_structure.py# every SKILL.md has required shape/frontmatter
│   ├── test_claim_linter.py   # every node type/field/code/command mentioned actually exists
│   ├── test_readme.py         # the README skill table is in sync
│   ├── test_validator_provenance.py # validator matches the captured designer schema
│   ├── truth.py / skillmd.py / allowlist.py / locate_qcli.py  # harness internals
│   └── conftest.py
│
├── tools/                     # repo maintenance scripts
│   ├── render_readme_table.py # regenerates the skill table in README.md
│   └── rollup_unverified.py   # regenerates UNVERIFIED.md from per-skill UV- markers
│
└── .github/workflows/         # CI harness
```

## Skill catalog

The skills fall into three groups. The canonical, always-current list with
descriptions is the auto-generated table in [README.md](README.md).

**Node-type skills** — how to author one node type correctly:
`agent-nodes`, `code-nodes`, `http-nodes`, `document-ai-nodes`,
`json-parser-nodes`, `text-parser-nodes`, `rpa-automation`,
`variables-and-assign`, `hitl-workflows`, `branch-and-converge`.

**Workflow & authoring skills** — how to assemble and improve whole flows:
`workflow-builder` (write → validate → deploy end to end),
`document-to-workflow` (turn a PDD/SDD/BRD into a graph),
`workflow-optimizer` (analyze and improve an existing flow),
`workflow-patterns` (retry, error branch, polling, fan-out/fan-in shapes),
`qubi-skill-authoring` (how to write a new skill that passes the harness).

**CLI & diagnostics skills** — how to drive and debug the tool:
`qubi-cli` (complete `qcli` command reference),
`qcli-troubleshooting` (why a command failed or lied about succeeding),
`validation-triage` (every validate error/warning code and its fix, in fix order).

## How skills are used

Point an AI coding agent at the skill folders:

- **Claude Code:** copy/symlink into `.claude/skills/`, or run `qcli skills install`
- **Kiro:** reference in `.kiro/steering/`
- **Others (Cursor, etc.):** load the skill folder as project context

The agent reads a skill's `SKILL.md` first and only opens the companion reference
files (`schema-reference.md`, `examples.md`, `error-handling.md`) when it hits the
topic they cover — keeping context focused.

## How it's tested

A pytest harness in `tests/` checks every skill against the **real qcli validator**
(from the sibling qcli project) at runtime:

- Every valid fixture must validate to 0 errors and 0 warnings
- Every invalid fixture must produce exactly the diagnostic codes it claims
- Every node type, field, diagnostic code, and CLI command/flag mentioned in a
  skill's markdown must actually exist in the validator/CLI

```bash
pip install -e ../qcli-web    # one-time: make the validator importable (or set $QCLI_WEB)
python -m pytest -q
```

If the tests fail with "only N codes discovered" or "rejects description," the
locally installed validator is **older than the skills expect** — update the sibling
qcli checkout to the hardened version. The skills in this repo are written against
the hardened validator described in `README1.md`.

## How it fits with the other projects

This is one of (at least) three related qubi projects. When you place them together
in one workspace, they relate like this:

| Project | What it is | Relationship to qubi-skills |
|---------|-----------|-----------------------------|
| **qubi-skills** (this repo) | Markdown skills + fixtures + test harness that teach an AI to build qubi workflows | The knowledge layer. Consumes the CLI/validator as its source of truth |
| **qcli / qcli-web** (the CLI) | The `qcli` command-line tool — auth, `flow validate/save/get/list/run`, `agents list`, `rpa list`, and the offline schema validator (`qcli/schema.py`) | The runtime the skills drive and the truth source the tests validate against |
| **qubi web platform** | The AgentHub web app where workflows live and run | The deployment target. `qcli flow save` pushes into a workflow that must already exist here |

**Direction of dependency:** skills depend on the CLI (for validation and truth),
the CLI depends on the web platform (for auth and deploy). Nothing depends on the
skills — they are the documentation/behavior layer on top.

**A note on command naming:** skills consistently use `qcli` as the command name
(matching the CLI project and the test harness). A locally installed binary may be
exposed as `qubi` instead; if so, `qcli` and `qubi` refer to the same tool.

## Where to look next

- New here? Read [README.md](README.md) for the skill catalog, then open any
  skill's `SKILL.md`.
- Writing a skill? Read [qubi-skill-authoring/SKILL.md](qubi-skill-authoring/SKILL.md)
  for the full contract the harness enforces.
- Something can't be confirmed offline? Check [UNVERIFIED.md](UNVERIFIED.md).
- Wondering why the validator changed? Read [README1.md](README1.md).
