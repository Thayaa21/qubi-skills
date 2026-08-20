---
name: qubi-cli
description: "Complete CLI reference for the qubi command-line tool. Auth, workflow lifecycle (validate/save/get/list/run/use), agent discovery, RPA discovery. Use when running any qubi command."
---

# qubi CLI

> The complete command reference for the `qubi` CLI — authenticate, manage workflows, and discover platform resources.

## When to invoke

- User asks to run a qubi command
- User needs to authenticate with qubi (`qubi login`)
- User wants to list, get, save, validate, or run workflows
- User wants to find available agents or RPA automations
- User asks "how do I deploy to qubi" or "how do I push my workflow"

## Critical Rules

1. **Always authenticate first** — `qubi login` must succeed before any platform command works
2. **Always validate before saving** — run `qubi flow validate` before `qubi flow save`
3. **Never use `-y` flags** — always let the human confirm destructive operations (save, run)
4. **Never invent IDs** — get `workflow-id` from `qubi flow list`, `agentId` from `qubi agents list`, `automationId` from `qubi rpa list`
5. **Use `--json-output` for parsing** — when you need to extract data programmatically, use the `-j` flag
6. **Check `qubi status` first** — if unsure whether the user is logged in, check before running platform commands
7. **There is no `qubi flow create`** — a workflow must already exist on the platform (created in the web UI) before `qubi flow save` can push to it

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
- `--no-browser` falls back to direct API username/password prompt, which captures Identity Server cookies (not AgentHub cookies) — networked commands may still 401 afterward, so prefer the default browser login

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

List all workflows on the platform. Results are cached locally so `flow use` can reference them by number.

```bash
qubi flow list                    # show all workflows
qubi flow list -s "invoice"       # search by name
qubi flow list --json-output      # machine-readable JSON output
```

| Flag | Description |
|------|-------------|
| `-s, --search TEXT` | Filter workflows by name |
| `-j, --json-output` | Output as JSON |

#### `qubi flow use <number>`

Select a workflow from the last `qubi flow list` by its display number.

```bash
qubi flow use 3     # select workflow #3 from the list
```

#### `qubi flow get <workflow-id>`

Download a workflow graph as JSON.

```bash
qubi flow get abc123                            # save to file
qubi flow get abc123 -o my-flow.json            # save to a specific file
qubi flow get abc123 -o my-flow.json --pretty   # pretty-printed
```

| Flag | Description |
|------|-------------|
| `-o, --output TEXT` | Output file path |
| `--pretty / --no-pretty` | Pretty-print the JSON |

#### `qubi flow validate <file>`

Validate a workflow JSON file against the schema. Always run this before saving.

```bash
qubi flow validate workflow.json              # human-readable output
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
qubi agents list                # human-readable table
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
qubi rpa list                   # human-readable table
qubi rpa list -j                # JSON output for parsing
```

| Flag | Description |
|------|-------------|
| `-j, --json-output` | Output as JSON |

**When to use:** Whenever you need an `automationId` for an RPA node in a workflow.

---

## Common Workflows

### First-time setup
```bash
qubi login
qubi status          # verify: "Logged in as ..."
qubi flow list       # see what's available
```

### Build and deploy a new workflow
```bash
# 1. Create workflow JSON (use the workflow-builder skill)
# 2. Validate locally
qubi flow validate my-flow.json
# 3. Get the target workflow ID (must already exist on the platform)
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
# edit flow.json...
qubi flow validate flow.json
qubi flow save flow.json --workflow-id <id>
```

### Find platform resources
```bash
qubi agents list -j    # get agentId for Agent nodes
qubi rpa list -j       # get automationId for RPA nodes
```

## Error Handling

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Not authenticated" | Session expired or never logged in | Run `qubi login` |
| "Workflow not found" | Wrong workflow ID | Run `qubi flow list` to find the correct ID |
| "Validation failed" | Invalid workflow JSON | Run `qubi flow validate` and fix errors |
| Login times out or fails silently | Browser automation couldn't find/fill the form | Run `qubi login --headed` to see what's happening |
| `--no-browser` login accepted but other commands 401 | Direct API login captures Identity Server cookies, not AgentHub cookies — a known limitation | Use the default browser login instead |
| "Could not start the workflow" from `flow run` | Neither REST endpoint nor the SignalR hub could run it | The workflow may only be runnable from the web UI for now — a real platform limitation, not a bug to work around |
| Connection issue | Wrong server or network issue | Check `qubi status`, try `qubi login --server <url>` |
| Permission denied | Account lacks access | Contact platform admin |

## Unverified

| ID | Claim | Why unverifiable offline | How to verify | Status |
|----|-------|--------------------------|----------------|--------|
| UV-RUNTIME-02 | `qubi flow run` executes a workflow and returns a real job id | Both REST endpoints and the SignalR hub are unreachable offline | Run any saved workflow and confirm a job id comes back | open |

## Operating Rules

**Always:**
- Check `qubi status` if unsure about auth state
- Use `qubi flow validate` before `qubi flow save`
- Use `--json-output` when extracting data programmatically
- Get IDs from list commands, never guess them
- Ask human for confirmation before save/run

**Never:**
- Use `-y` or `--yes` flags (bypasses human confirmation)
- Use `--skip-validate` (risks pushing invalid workflows)
- Assume workflow IDs — always discover from `qubi flow list`
- Assume a workflow can be created from the CLI — it must already exist on the platform
- Run platform commands without checking auth first
