---
name: qubi-cli
description: "Complete CLI reference for the qubi command-line tool. Auth, workflow lifecycle (validate/save/get/list/run), agent discovery, RPA discovery, skills management. Use when running any qubi command."
---

# qubi CLI

> The complete command reference for the `qubi` CLI — authenticate, manage workflows, discover platform resources, and install skills.

## When to invoke

- User asks to run a qubi command
- User needs to authenticate with qubi (`qubi login`)
- User wants to list, get, save, validate, or run workflows
- User wants to find available agents or RPA automations
- User wants to install or manage qubi skills
- User asks "how do I deploy to qubi" or "how do I push my workflow"

## Critical Rules

1. **Always authenticate first** — `qubi login` must succeed before any platform command works
2. **Always validate before saving** — run `qubi flow validate` before `qubi flow save`
3. **Never use `-y` flags** — always let the human confirm destructive operations (save, run, uninstall)
4. **Never invent IDs** — get `workflow-id` from `qubi flow list`, `agentId` from `qubi agents list`, `automationId` from `qubi rpa list`
5. **Use `--json-output` for parsing** — when you need to extract data programmatically, use the `-j` flag
6. **Check `qubi status` first** — if unsure whether the user is logged in, check before running platform commands

## Quick Start

1. Authenticate: `qubi login`
2. List workflows: `qubi flow list`
3. Select a workflow: `qubi flow use <number>`
4. Download it: `qubi flow get <workflow-id> -o workflow.json --pretty`
5. Edit the JSON
6. Validate: `qubi flow validate workflow.json`
7. Save back: `qubi flow save workflow.json --workflow-id <id>`
8. Run: `qubi flow run <workflow-id>`

## Command Reference

### Authentication

#### `qubi login`

Authenticate with the qubi platform. Uses automated browser login by default.

```bash
qubi login                  # Browser-based login (default)
qubi login --headed         # Show browser window (debugging)
qubi login --no-browser     # Direct API login (prompts for credentials)
qubi login --server <url>   # Custom AgentHub URL
```

**Behavior:**
- Credentials are prompted once and stored for future sessions
- Default uses headless browser automation
- `--no-browser` falls back to direct API username/password prompt

#### `qubi logout`

Clear stored session credentials.

```bash
qubi logout
```

#### `qubi status`

Show current login status (logged in / not logged in, which server).

```bash
qubi status
```

---

### Workflow Commands (`qubi flow`)

#### `qubi flow list`

List all workflows on the platform.

```bash
qubi flow list                    # Show all workflows
qubi flow list -s "invoice"       # Search by name
qubi flow list --json-output      # Machine-readable JSON output
```

| Flag | Description |
|------|-------------|
| `-s, --search TEXT` | Filter workflows by name |
| `-j, --json-output` | Output as JSON |

#### `qubi flow use <number>`

Select a workflow from the list by its display number. Useful after running `qubi flow list`.

```bash
qubi flow use 3     # Select workflow #3 from the list
```

#### `qubi flow get <workflow-id>`

Download a workflow graph as JSON.

```bash
qubi flow get abc123                           # Print to stdout
qubi flow get abc123 -o my-flow.json           # Save to file
qubi flow get abc123 -o my-flow.json --pretty  # Pretty-printed
```

| Flag | Description |
|------|-------------|
| `-o, --output TEXT` | Output file path |
| `--pretty / --no-pretty` | Pretty-print the JSON |

#### `qubi flow validate <file>`

Validate a workflow JSON file against the schema. Always run this before saving.

```bash
qubi flow validate workflow.json              # Human-readable output
qubi flow validate workflow.json -j           # JSON error output
```

| Flag | Description |
|------|-------------|
| `-j, --json-output` | Output errors as JSON |

**Exit codes:**
- `0` — valid, no errors
- `1` — validation errors found

#### `qubi flow save <file>`

Push a local workflow JSON file to the qubi platform.

```bash
qubi flow save workflow.json --workflow-id <id>
```

| Flag | Required | Description |
|------|----------|-------------|
| `-w, --workflow-id TEXT` | **yes** | Target workflow ID on the platform |
| `-y, --yes` | no | Skip confirmation (DO NOT USE in agent context) |
| `--skip-validate` | no | Skip pre-save validation (NOT RECOMMENDED) |

**Rules:**
- The workflow must already exist on the platform
- The workflow ID is visible in the URL: `/workflows/{id}/designer`
- Always ask the human for confirmation before saving
- Always validate first (don't use `--skip-validate`)

#### `qubi flow run <workflow-id>`

Execute a workflow on the platform.

```bash
qubi flow run <workflow-id>
```

| Flag | Description |
|------|-------------|
| `-y, --yes` | Skip confirmation (DO NOT USE in agent context) |

**Rules:**
- Always ask the human for confirmation before running
- Returns a job/execution ID on success

---

### Agent Commands (`qubi agents`)

#### `qubi agents list`

List all available AI agents on the platform. Use this to get `agentId` values for Agent nodes.

```bash
qubi agents list                # Human-readable table
qubi agents list -j             # JSON output for parsing
```

| Flag | Description |
|------|-------------|
| `-j, --json-output` | Output as JSON |

**When to use:** Whenever you need an `agentId` for an Agent node in a workflow.

---

### RPA Commands (`qubi rpa`)

#### `qubi rpa list`

List all available RPA automations. Use this to get `automationId` values for RPA nodes.

```bash
qubi rpa list                   # Human-readable table
qubi rpa list -j                # JSON output for parsing
```

| Flag | Description |
|------|-------------|
| `-j, --json-output` | Output as JSON |

**When to use:** Whenever you need an `automationId` for an RPA node in a workflow.

---

### Skills Commands (`qubi skills`)

#### `qubi skills install`

Download and install qubi skills into your AI coding agent's skills directory.

```bash
qubi skills install                         # Install for default agent (Claude)
qubi skills install --agent claude          # Explicit agent target
qubi skills install --repo <url>            # Custom skills repository
```

| Flag | Description |
|------|-------------|
| `--repo TEXT` | Custom skills repository URL |
| `--agent [claude]` | Target AI agent |

#### `qubi skills list`

Show which skills are currently installed.

```bash
qubi skills list                            # List installed skills
qubi skills list --agent claude             # For specific agent
```

#### `qubi skills update`

Update installed skills to the latest version from the repository.

```bash
qubi skills update                          # Update all
qubi skills update --repo <url>             # From custom repo
```

#### `qubi skills uninstall`

Remove all installed qubi skills.

```bash
qubi skills uninstall                       # Prompts for confirmation
qubi skills uninstall --agent claude        # For specific agent
```

| Flag | Description |
|------|-------------|
| `--agent [claude]` | Target AI agent |
| `-y, --yes` | Skip confirmation (DO NOT USE in agent context) |

---

## Common Workflows

### First-time setup
```bash
qubi login
qubi status          # Verify: "Logged in as ..."
qubi flow list       # See what's available
```

### Build and deploy a new workflow
```bash
# 1. Create workflow JSON (use workflow-builder skill)
# 2. Validate locally
qubi flow validate my-flow.json
# 3. Get the target workflow ID
qubi flow list -s "my workflow"
# 4. Push to platform
qubi flow save my-flow.json --workflow-id <id>
# 5. Run it
qubi flow run <id>
```

### Download, edit, re-upload
```bash
qubi flow list
qubi flow get <id> -o flow.json --pretty
# Edit flow.json...
qubi flow validate flow.json
qubi flow save flow.json --workflow-id <id>
```

### Find platform resources
```bash
qubi agents list -j    # Get agentId for Agent nodes
qubi rpa list -j       # Get automationId for RPA nodes
```

## Error Handling

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Not authenticated" | Session expired or never logged in | Run `qubi login` |
| "Workflow not found" | Wrong workflow ID | Run `qubi flow list` to find correct ID |
| "Validation failed" | Invalid workflow JSON | Run `qubi flow validate` and fix errors |
| "Connection refused" | Wrong server or network issue | Check `qubi status`, try `qubi login --server <url>` |
| "Permission denied" | Account lacks access | Contact platform admin |

## Operating Rules

**Always:**
- Check `qubi status` if unsure about auth state
- Use `qubi flow validate` before `qubi flow save`
- Use `--json-output` when extracting data programmatically
- Get IDs from list commands, never guess them
- Ask human for confirmation before save/run/uninstall

**Never:**
- Use `-y` or `--yes` flags (bypasses human confirmation)
- Use `--skip-validate` (risks pushing invalid workflows)
- Assume workflow IDs — always discover from `qubi flow list`
- Run platform commands without checking auth first
