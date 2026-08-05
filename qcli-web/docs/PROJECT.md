# qcli Web Version — Project Overview

## What Is This?

**qcli (web)** is a CLI tool + AI Skill for generating, validating, and deploying Agentic Flows workflows to qubi's web-based platform.

Unlike the studio version (which targeted desktop XAML workflows), this targets the **web designer** — a Next.js app using React Flow for visual workflow building, backed by a .NET API.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI Agent (Claude Code / Kiro)                      │
│                                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Reads Skill │  │ Builds graph │  │ Calls qcli   │               │
│  │ for schema  │  │ JSON directly│  │ to validate  │               │
│  └─────────────┘  └──────────────┘  │ & deploy     │               │
│                                      └──────────────┘               │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     qcli (Deterministic CLI)                          │
│                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ validate │ │  build   │ │  auth    │ │  save    │ │  run     │ │
│  │          │ │          │ │          │ │          │ │          │ │
│  │ Check    │ │ Generate │ │ Login &  │ │ Push to  │ │ Execute  │ │
│  │ graph    │ │ graph    │ │ get      │ │ qubi API │ │ workflow │ │
│  │ validity │ │ JSON     │ │ session  │ │          │ │          │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│               qubi Platform (test.agenthub.qubi.com)                 │
│                                                                      │
│  Identity Server  │  Workflow API  │  Agent Registry  │  Execution   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Differences from Studio Version

| Aspect | Studio Version | Web Version |
|--------|---------------|-------------|
| Format | XAML (XML) | JSON (React Flow graph) |
| Platform | Desktop app | Web app (Next.js) |
| Auth | Simple token | OAuth2 + Identity Server + Tenant |
| Nodes | Activities (98 connectors) | 13 node types |
| Validation | XML structure + namespace checks | JSON schema + edge validation |
| Save | Package as .qpkg + upload | Direct API POST of graph JSON |
| Complexity | Very complex (678 functions) | Focused (13 node types) |

---

## CLI Commands (Planned)

| Command | Purpose | Auth Required |
|---------|---------|---------------|
| `qcli login` | Authenticate via Identity Server | No |
| `qcli logout` | Clear session | No |
| `qcli status` | Show current auth state | No |
| `qcli flow list` | List all workflows | Yes |
| `qcli flow validate <file>` | Validate a workflow JSON file | No |
| `qcli flow save <file> --workflow-id <id>` | Push graph to qubi | Yes |
| `qcli flow get <id> -o <file>` | Download a workflow graph | Yes |
| `qcli flow run <id>` | Execute a workflow | Yes |
| `qcli agents list` | List available agents | Yes |
| `qcli rpa list` | List available RPA automations | Yes |

---

## Workflow Format

Workflows are React Flow graphs stored as JSON:

```json
{
  "nodes": [
    { "id": "uuid", "type": "Start", "position": {x, y}, "data": {...} }
  ],
  "edges": [
    { "id": "xy-edge__src-tgt", "source": "uuid", "target": "uuid" }
  ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "executionMode": "Sequential"
}
```

See [GRAPH_SCHEMA.md](./GRAPH_SCHEMA.md) for full node type reference.

---

## Build Order

```
1. docs/          ← Schema + API documentation (DONE)
2. qcli/
   ├── auth.py    ← OAuth login flow
   ├── client.py  ← HTTP client for qubi API
   ├── schema.py  ← Graph validation logic
   └── cli.py     ← Entry point + commands
3. skills/        ← AI Skill files
```

---

## Dependencies

- Python 3.9+
- click (CLI framework)
- requests (HTTP)
- No AI/LLM libraries in the CLI itself
