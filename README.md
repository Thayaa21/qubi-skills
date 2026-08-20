# qubi-skills

AI Skills for building qubi Agentic Flows workflows. Each skill teaches an AI agent (Claude/Kiro) a specific capability.

## Skills

This table is generated from the skill directories -- see `tools/render_readme_table.py`. Run it after adding, removing, or renaming a skill; `tests/test_readme.py` fails if it's out of date.

<!-- SKILLS-TABLE:START -->
| Skill | Purpose |
|-------|---------|
| **agent-nodes** | Add AI Agent nodes to qubi Agentic Flows -- selecting a real agentId, systemPrompt vs userMessage, chaining agent output |
| **branch-and-converge** | Build correct conditional flows in qubi Agentic Flows -- Branch conditions, reconverging paths, and guaranteeing every path reaches End |
| **code-nodes** | Run inline JavaScript or Python in a qubi Agentic Flow Code node |
| **document-ai-nodes** | Add DocumentAI nodes to qubi Agentic Flows for OCR, extraction, and classification of uploaded files |
| **document-to-workflow** | Convert process documents (PDD, SDD, BRD, SOPs) into qubi Agentic Flows workflow JSON |
| **hitl-workflows** | Design human-in-the-loop steps in qubi Agentic Flows using Hitl and HitlTask nodes -- approval gates, escalation, task assignment |
| **http-nodes** | Call external APIs from qubi Agentic Flows with Http nodes -- the five valid methods, headers, body, and URL interpolation |
| **json-parser-nodes** | Extract fields from JSON responses in qubi Agentic Flows with JsonParser mappings |
| **qcli-troubleshooting** | Fix qcli command failures -- authentication problems, Windows console crashes, flow run not actually running, no flow create |
| **qubi-cli** | Complete CLI reference for the qcli command-line tool |
| **qubi-skill-authoring** | Write a new skill in this repo so it passes the fixture sweep and claim linter in tests/ |
| **rpa-automation** | Call an existing qubi RPA automation from an Agentic Flow |
| **text-parser-nodes** | Extract structured values from free text in qubi Agentic Flows with TextParser -- regex patterns, capture-group mappings, and fallbacks |
| **validation-triage** | Diagnose and fix every qcli flow validate error and warning code, in fix order |
| **variables-and-assign** | Move data between nodes in qubi Agentic Flows -- saveOutputAs, {{variable}} interpolation, the Assign node, and Input Source |
| **workflow-builder** | Generate, validate, and deploy qubi Agentic Flows (JSON graph format) |
| **workflow-optimizer** | Analyze existing qubi Agentic Flows workflows and suggest improvements — reduce steps, fix inefficiencies, add error handling, optimize data flow |
| **workflow-patterns** | Reusable qubi Agentic Flow shapes -- retry, error branch, bounded polling, fan-out/fan-in |
<!-- SKILLS-TABLE:END -->

## How Skills Work

Each skill is a set of markdown files that an AI agent reads to understand:
- What it can do
- What schema/format to follow
- What rules to obey
- Examples to pattern-match from

## Usage

Point your AI agent (Claude Code, Kiro, etc.) at the skill folder:
- Claude Code: symlink or copy into `.claude/skills/`
- Kiro: reference in `.kiro/steering/`

## Skill Structure

```
skill-name/
├── SKILL.md              # Main entry — when to invoke, rules, phases
├── schema-reference.md   # Node types, fields, formats (optional)
├── examples.md           # Complete working examples (optional)
├── error-handling.md     # How to fix validation errors (optional)
└── fixtures/
    ├── *.json             # must validate to 0 errors AND 0 warnings
    └── invalid/
        ├── *.json          # each reproduces a specific diagnostic code
        └── expected.json   # the codes each one must produce
```

## Testing

A pytest harness in `tests/` checks every skill against the real qcli validator (from the sibling `qcli-web` repo) at runtime: fixtures must validate cleanly, and every node type, field, diagnostic code, and CLI command/flag mentioned in a skill's markdown must actually exist.

```bash
pip install -e ../qcli-web    # one-time, or set $QCLI_WEB to a checkout
python -m pytest -q
```

See [qubi-skill-authoring/SKILL.md](qubi-skill-authoring/SKILL.md) for the full contract, and `UNVERIFIED.md` for what the offline harness can't settle until the qubi server is reachable.

## Adding a New Skill

1. Create a folder: `my-new-skill/`
2. Build `fixtures/*.json` first, validated directly against `qcli flow validate` — fixtures are the proof, not an afterthought
3. Write `SKILL.md`: what it does, when to invoke, phases, rules
4. Run `python -m pytest -q -k my-new-skill` until green
5. Run `python tools/render_readme_table.py` to add it to the table above
