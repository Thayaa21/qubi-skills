---
name: qubi-cli
description: "Complete CLI reference for the qcli command-line tool. Auth, workflow lifecycle (validate/save/get/list/run/use), agent discovery, RPA discovery. Use when running any qcli command."
---

# qubi CLI

> The complete command reference for the `qcli` CLI — authenticate, manage workflows, and discover platform resources.

## When to invoke

- User asks to run a qcli command
- User needs to authenticate with qubi (`qcli login`)
- User wants to list, get, save, validate, or run workflows
- User wants to find available agents or RPA automations
- User asks "how do I deploy to qubi" or "how do I push my workflow"

## Critical Rules

1. **Always authenticate first** — `qcli login` must succeed before any platform command works
2. **Always validate before saving** — run `qcli flow validate` before `qcli flow save`
3. **Never use `-y` flags** — always let the human confirm destructive operations (save, run)
4. **Never invent IDs** — get `workflow-id` from `qcli flow list`, `agentId` from `qcli agents list`, `automationId` from `qcli rpa list`
5. **Use `--json-output` for parsing** — when you need to extract data programmatically, use the `-j` flag
6. **Check `qcli status` first** — if unsure whether the user is logged in, check before running platform commands
7. **There is no `qcli flow create`** — a workflow must already exist on the platform (created in the web UI) before `qcli flow save` can push to it

## Quick Start

1. Authenticate: `qcli login`
2. List workflows: `qcli flow list`
3. Select a workflow: `qcli flow use <number>`
4. Download it: `qcli flow get <workflow-id> -o workflow.json --pretty`
5. Edit the JSON
6. Validate: `qcli flow validate workflow.json`
7. Save back: `qcli flow save workflow.json --workflow-id <id>`
8. Run: `qcli flow run <workflow-id>`

## Command Reference

### Authentication

#### `qcli login`

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
qcli logout
```

#### `qcli status`
qubi logout
```

#### `qubi status`

Show current login status (logged in / not logged in, which server).

```bash
qcli status
```

---

### Workflow Commands (`qcli flow`)

#### `qcli flow list`

List all workflows on the platform. Results are cached locally so `flow use` can reference them by number.

```bash
qcli flow list                    # show all workflows
qcli flow list -s "invoice"       # search by name
qcli flow list --json-output      # machine-readable JSON output
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

#### `qcli flow use <number>`

Select a workflow from the last `qcli flow list` by its display number.

```bash
qcli flow use 3     # select workflow #3 from the list
```

#### `qcli flow get <workflow-id>`

Download a workflow graph as JSON. By default this writes a file under `workflows/` (named from the cached workflow name, or the id) rather than printing — pass `-o -` for stdout.

```bash
qcli flow get abc123                            # auto-saves to workflows/<name>.json
qcli flow get abc123 -o my-flow.json            # save to a specific file
qcli flow get abc123 -o my-flow.json --pretty   # pretty-printed
qcli flow get abc123 -o -                       # print to stdout, for piping
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
# 1. Create workflow JSON (use the workflow-builder skill)
# 2. Validate locally
qcli flow validate my-flow.json
# 3. Get the target workflow ID (must already exist on the platform)
qcli flow list -s "my workflow"
# 4. Push to platform
qcli flow save my-flow.json --workflow-id <id>
# 5. Run it
qcli flow run <id>
```

### Download, edit, re-upload
```bash
qcli flow list
qcli flow get <id> -o flow.json --pretty
# edit flow.json...
qcli flow validate flow.json
qcli flow save flow.json --workflow-id <id>
```

### Find platform resources
```bash
qcli agents list -j    # get agentId for Agent nodes
qcli rpa list -j       # get automationId for RPA nodes
```

## Error Handling

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Not authenticated" | Session expired or never logged in | Run `qcli login` |
| "Workflow not found" | Wrong workflow ID | Run `qcli flow list` to find the correct ID |
| "Validation failed" | Invalid workflow JSON | Run `qcli flow validate` and fix errors |
| Login times out or fails silently | Browser automation couldn't find/fill the form | Run `qcli login --headed` to see what's happening |
| `--no-browser` login accepted but other commands 401 | Direct API login captures Identity Server cookies, not AgentHub cookies — a known limitation | Use the default browser login instead |
| "Could not start the workflow" from `flow run` | Neither REST endpoint nor the SignalR hub could run it | The workflow may only be runnable from the web UI for now — this is a real platform limitation, not a bug to work around |
| Connection issue | Wrong server or network issue | Check `qcli status`, try `qcli login --server <url>` |
| Permission denied | Account lacks access | Contact platform admin |

## Unverified

| ID | Claim | Why unverifiable offline | How to verify | Status |
|----|-------|--------------------------|----------------|--------|
| UV-RUNTIME-02 | `qcli flow run` executes a workflow and returns a real job id | Both REST endpoints and the SignalR hub are unreachable offline | Run any saved workflow and confirm a job id comes back | open |

## Operating Rules

**Always:**
- Check `qcli status` if unsure about auth state
- Use `qcli flow validate` before `qcli flow save`
- Use `--json-output` when extracting data programmatically
- Get IDs from list commands, never guess them
- Ask human for confirmation before save/run

**Never:**
- Use `-y` or `--yes` flags (bypasses human confirmation)
- Use `--skip-validate` (risks pushing invalid workflows)
- Assume workflow IDs — always discover from `qcli flow list`
- Assume a workflow can be created from the CLI — it must already exist on the platform
- Run platform commands without checking auth first
