# qcli — qubi Agentic Flows CLI (Web Version)

CLI tool + AI Skill for generating, validating, and deploying workflows to qubi's web-based Agentic Flows platform.

## Quick Start

```bash
cd web-version
pip install -e .
qcli --help
```

## Commands

| Command | Purpose |
|---------|---------|
| `qcli login` | Authenticate with qubi Identity Server |
| `qcli logout` | Clear session |
| `qcli status` | Show login status |
| `qcli flow list` | List all workflows |
| `qcli flow validate <file>` | Validate a workflow JSON file |
| `qcli flow get <id> -o file.json` | Download a workflow |
| `qcli flow save <file> -w <id>` | Push workflow to qubi |
| `qcli flow run <id>` | Execute a workflow |
| `qcli agents list` | List available AI agents |
| `qcli rpa list` | List RPA automations |

## Project Structure

```
web-version/
├── qcli/                  # Python CLI package
│   ├── auth.py            # OAuth2 login + session management
│   ├── client.py          # HTTP client for qubi API
│   ├── schema.py          # Workflow graph validation
│   ├── cli.py             # Entry point (click commands)
│   └── commands/
│       ├── login.py       # login/logout/status
│       ├── flow.py        # list/validate/get/save/run
│       └── agents.py      # agents list / rpa list
├── skills/                # AI Skill files (for Claude Code / Kiro)
│   ├── SKILL.md           # Main skill — rules + command sequence
│   ├── schema-reference.md # All 13 node types with fields
│   ├── examples.md        # Working workflow examples
│   └── error-handling.md  # Validation errors + fixes
├── docs/                  # Technical documentation
│   ├── API.md             # Full API reference
│   ├── GRAPH_SCHEMA.md    # Graph format specification
│   └── PROJECT.md         # Architecture + design
├── requirements.txt
├── setup.py
└── README.md
```

## Workflow Format

Workflows are React Flow graphs (JSON):

```json
{
  "nodes": [
    { "id": "uuid", "type": "Start", "position": {"x":100,"y":200}, "data": {"type":"Start","name":"Start"} },
    { "id": "uuid", "type": "Http", "position": {"x":300,"y":200}, "data": {"type":"Http","name":"Fetch","method":"GET","url":"https://..."} },
    { "id": "uuid", "type": "End", "position": {"x":500,"y":200}, "data": {"type":"End","name":"End"} }
  ],
  "edges": [
    { "id": "xy-edge__src-tgt", "source": "node1-id", "target": "node2-id" }
  ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "executionMode": "Sequential"
}
```

## Node Types

Start, End, Agent, Assign, Branch, Code, DocumentAI, Http, RPA, Hitl, HitlTask, JsonParser, TextParser

See `skills/schema-reference.md` for full field documentation.
