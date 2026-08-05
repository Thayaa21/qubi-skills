# How to Use qcli (Web Version)

## Installation

```bash
# Requires Python 3.9+
cd web-version
pip install -e .

# Verify
qcli --help
```

## Authentication

```bash
# Interactive login
qcli login
# Prompts: Identity Server URL, Tenant, Username, Password

# Non-interactive (for scripts)
qcli login --server https://test.identityserver.qubi.com --tenant default -u user@email.com -p password

# Check status
qcli status

# Logout
qcli logout
```

Session is stored at `~/.qcli/session.json`.

## Working with Workflows

### List workflows
```bash
qcli flow list
qcli flow list --search "my workflow"
```

### Download an existing workflow
```bash
qcli flow get <workflow-id> -o workflow.json --pretty
```

### Validate a workflow file
```bash
qcli flow validate workflow.json

# Machine-readable output
qcli flow validate workflow.json --json-output
```

### Save (push) to qubi
```bash
# Validates first, then pushes
qcli flow save workflow.json --workflow-id <id>

# Skip confirmation prompt
qcli flow save workflow.json --workflow-id <id> --yes

# Skip validation (not recommended)
qcli flow save workflow.json --workflow-id <id> --skip-validate
```

### Execute a workflow
```bash
qcli flow run <workflow-id>

# With input data
qcli flow run <workflow-id> --input data.json
```

## Discovering Resources

### List AI agents (needed for Agent nodes)
```bash
qcli agents list
qcli agents list --json-output
```

### List RPA automations (needed for RPA nodes)
```bash
qcli rpa list
qcli rpa list --json-output
```

## Using with AI (Claude Code / Kiro)

### Setup
Load `skills/SKILL.md` as a skill file in your AI agent. The agent will then:
- Know all 13 node types and their fields
- Follow the validate → confirm → save sequence
- Ask for confirmation before any write operations
- Fix validation errors autonomously

### Example Prompts

> "Build a workflow that calls the weather API for London and summarizes the result with an AI agent"

> "Create a flow that takes user input, parses the JSON, and routes to different endpoints based on the status field"

> "Download the workflow with ID abc-123, add a TextParser node after the HTTP call, and save it back"

## Writing Workflows Manually

Minimal workflow (Start → End):

```json
{
  "nodes": [
    {
      "id": "11111111-1111-1111-1111-111111111111",
      "type": "Start",
      "position": {"x": 100, "y": 200},
      "data": {"type": "Start", "name": "Start"}
    },
    {
      "id": "22222222-2222-2222-2222-222222222222",
      "type": "End",
      "position": {"x": 400, "y": 200},
      "data": {"type": "End", "name": "End"}
    }
  ],
  "edges": [
    {
      "id": "xy-edge__11111111-1111-1111-1111-111111111111-22222222-2222-2222-2222-222222222222",
      "source": "11111111-1111-1111-1111-111111111111",
      "target": "22222222-2222-2222-2222-222222222222"
    }
  ],
  "viewport": {"x": 0, "y": 0, "zoom": 1},
  "executionMode": "Sequential"
}
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Not logged in" | Run `qcli login` |
| Connection timeout | Check VPN connection |
| 401 Unauthorized | Session expired — run `qcli login` again |
| Validation fails | Check error message, fix the JSON, re-validate |
| "Unknown node type" | Check spelling — it's `Http` not `HTTP`, `Hitl` not `HITL` |
