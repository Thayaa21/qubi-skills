---
name: workflow-builder
description: "Generate, validate, and deploy qubi Agentic Flows (JSON graph format). Use when building a qubi web workflow; creating agentic flow graphs; validating workflow JSON; deploying to qubi AgentHub."
---

# qubi Agentic Flows Builder

> Build valid qubi Agentic Flows from plain English, validate locally, and deploy to the qubi web platform via the qcli pipeline.

## What this skill is

A workflow authoring skill that knows qubi's 13 Agentic Flow node types, their required fields, and the exact CLI commands to validate and push workflow graphs to the platform. You write the graph JSON directly, validate offline, fix errors yourself, and ask the human only for confirmation before writes and for platform-specific IDs.

## What it solves

- Knowing which node types exist and what fields each requires
- Writing structurally valid workflow graphs that pass qcli validation
- Following the exact command sequence to save a workflow to qubi
- Handling validation errors without human help

## When to invoke

- User asks to build, create, or generate a qubi Agentic Flow
- User asks to write a workflow graph for qubi's web platform
- User asks to validate or deploy a flow with qcli
- User mentions qubi, agentic flows, or AgentHub in a web/JSON context

## Reference files

This file covers the common cases. Read the companion file when you hit its topic —
don't try to hold all of it in context up front.

| File | Read it when |
|------|-------------|
| [schema-reference.md](./schema-reference.md) | You need the full field list for a node type, including which fields are select-from-dropdown vs free text |
| [examples.md](./examples.md) | You want a complete, validated graph to start from or compare against |
| [error-handling.md](./error-handling.md) | `qcli flow validate` reported an error or warning code and you need the fix |

## Phase 0: Get the Real Starting Point

Prefer editing an existing workflow over authoring one from scratch:

```bash
qcli flow list
qcli flow get <workflow-id> -o base.json --pretty
```

The downloaded graph already carries designer-only fields (`measured`, `selected`)
that a hand-authored graph won't have. Editing it in place avoids having to guess
whether those fields matter for a given save. If there is no existing workflow to
extend, a human must create one in the qubi web UI first and give you its ID —
`qcli flow save` writes into an existing workflow, there is no `flow create`.

If any networked command (`flow list`, `flow get`, `agents list`, `rpa list`,
`flow save`, `flow run`) fails with a 401/auth error, do not retry it blindly.
Tell the human and suggest `qcli login --browser`, which opens a real browser
window for them to log in and harvests the session cookies afterward. The
non-browser `qcli login` is known to store cookies for the wrong host and will
not authenticate networked calls.

## Phase 1: Understand the Request

Determine:
- What the workflow does (call API, run AI agent, parse data, execute RPA, etc.)
- Which node types are needed
- Whether agent IDs or RPA automation IDs are needed (if yes, use `qcli agents list` or `qcli rpa list` and ask the human to pick)

## Phase 2: Write the Graph JSON

Generate a complete workflow JSON file:

```json
{
  "nodes": [ ... ],
  "edges": [ ... ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "executionMode": "Sequential"
}
```

**Node structure:**
```json
{
  "id": "<uuid-v4>",
  "type": "<NodeType>",
  "position": { "x": <number>, "y": <number> },
  "data": { "type": "<NodeType>", "name": "<display name>", ...fields }
}
```

**Edge structure:**
```json
{
  "id": "xy-edge__<sourceId>-<targetId>",
  "source": "<source-node-id>",
  "target": "<target-node-id>"
}
```

**Available node types and required fields:**

| Type | Required Fields | Optional Fields |
|------|----------------|----------------|
| Start | name | description, input, saveOutputAs |
| End | name | description, input, saveOutputAs |
| Agent | name, **agentId** | description, input, systemPrompt, userMessage, saveOutputAs |
| Assign | name | description, assignments |
| Branch | name | description, conditions, input, saveOutputAs |
| Code | name, language, code | description, input, saveOutputAs |
| DocumentAI | name, operation | description, fileVariable, saveOutputAs, input |
| Http | name, method, url | description, input, headers, body, saveOutputAs |
| RPA | name, **automationId** | description, input, saveOutputAs |
| Hitl | name | description, input, saveOutputAs |
| HitlTask | name, taskName, taskType, assignTo | description, template, saveOutputAs, input |
| JsonParser | name | description, input, mappings |
| TextParser | name, regexPattern | description, input, ignoreCase, multiline, singleline, trimOutput, fallbackValue, outputMappings |

Every node type also accepts an optional `description` field. See
[schema-reference.md](./schema-reference.md) for the full field list per type,
including which fields are dropdown-selects on the platform (e.g. `taskType`,
`operation`) rather than free text you can invent.

**Type name casing matters:** `Http` not `HTTP`, `Hitl` not `HITL`, `RPA` not `Rpa`, `DocumentAI` not `documentAI`.

**Enum constraints:**
- Http.method: GET, POST, PUT, DELETE, PATCH — this is the platform's actual list.
  (`HEAD` and `OPTIONS` are not offered by the designer's Method dropdown; don't use them.)
- Code.language: javascript, python

**Rules:**
- Every graph must have exactly one Start node and one End node
- Node IDs must be UUID-shaped, all unique. This applies to *node* ids only —
  `agentId`, `automationId`, and `workflowId` are opaque platform identifiers
  (some are non-RFC-4122 .NET sequential GUIDs) that you discover via
  `qcli agents list` / `qcli rpa list` / `qcli flow list`, never generate
- `data.type` must match the node's `type` field
- Every `data` key must be one of that type's required/optional fields (plus
  `type` and `description`) — an unrecognised key is very likely a typo
  (`saveOutputas` instead of `saveOutputAs`) and will not do anything on the platform
- Position nodes at sensible x/y coordinates (100px spacing works)
- Edges must reference existing node IDs, no self-loops
- Every node must be reachable from Start and have a path to End — a disconnected
  node validates without an error but does nothing when the flow runs
- Edge `id` should follow `xy-edge__{source}-{target}` to match what the designer writes

## Phase 3: Validate

```bash
qcli flow validate <file.json>
```

For machine-parseable output:
```bash
qcli flow validate <file.json> --json-output
```

## Phase 4: Fix Errors

If validation fails, fix each error. Full list with explanations is in
[error-handling.md](./error-handling.md) — quick reference:

**Errors — these set `valid: false` and must be fixed before saving:**

| Error Code | Fix |
|-----------|-----|
| INVALID_FORMAT / INVALID_JSON | Fix JSON syntax / top-level structure |
| MISSING_NODES / MISSING_EDGES / INVALID_NODES / INVALID_NODE | Add or fix the top-level array, or the malformed entry |
| MISSING_NODE_ID | Add a UUID id |
| DUPLICATE_NODE_ID | Generate a new UUID |
| MISSING_NODE_TYPE | Set the node's `type` |
| UNKNOWN_NODE_TYPE | Fix the type name (check exact casing) |
| MISSING_REQUIRED_FIELD | Add the field to the node's data |
| INVALID_HTTP_METHOD | Use one of GET, POST, PUT, DELETE, PATCH |
| INVALID_CODE_LANGUAGE | Use javascript or python |
| MISSING_START / MISSING_END | Add a Start or End node |
| MISSING_EDGE_SOURCE / TARGET | Add the missing `source`/`target` on the edge |
| INVALID_EDGE_SOURCE / TARGET | Fix the edge to reference real node IDs |
| SELF_LOOP | Remove the edge or change the target |
| FILE_NOT_FOUND | Check the path you passed to `flow validate` |

**Warnings — these do not fail the exit code, but fix them before asking to save
(they mean the graph will misbehave on canvas or at runtime even though it passes):**

| Warning Code | Fix |
|-----------|-----|
| INVALID_NODE_DATA | `data` isn't an object — set it to `{ "type": ..., "name": ... }` plus fields |
| DATA_TYPE_MISMATCH | Set `data.type` to match the node's `type` |
| UNREACHABLE_NODE | Connect the node to the flow with an edge, or remove it |
| NO_PATH_TO_END | Add an outgoing edge so this branch reaches End |
| DUPLICATE_START / DUPLICATE_END | Keep exactly one Start / End node |
| INVALID_NODE_ID_FORMAT | Use a UUID-shaped node id |
| MISSING_EDGE_ID / EDGE_ID_MISMATCH | Set edge `id` to `xy-edge__{source}-{target}` |
| MISSING_VIEWPORT / MISSING_EXECUTION_MODE | Add `viewport: {x:0,y:0,zoom:1}` / `executionMode: "Sequential"` |
| MISSING_POSITION | Add `position: {x, y}` to the node |
| UNKNOWN_DATA_FIELD | Remove the field, or fix the typo (check the suggested field name) |

Re-validate after fixing. Repeat until there are zero errors and zero warnings.

## Phase 5: Discover Platform Resources (if needed)

For Agent nodes — get the agentId:
```bash
qcli agents list
```

For RPA nodes — get the automationId:
```bash
qcli rpa list
```

Ask the human to pick if there are multiple options.

## Phase 6: Save to qubi

**Ask the human for confirmation:**

"Ready to save this workflow to qubi?"

```bash
qcli flow save <file.json> --workflow-id <id>
```

The workflow must already exist on the platform. The human provides the workflow ID (visible in the URL: `/workflows/{id}/designer`).

## Phase 7: Run (optional)

**Ask the human for confirmation:**

"Ready to run this workflow?"

```bash
qcli flow run <workflow-id>
```

## Output

- A valid workflow `.json` file
- Validation confirmation (zero errors, zero warnings)
- Confirmation of save to qubi (if requested)
- Job ID from execution (if run requested)

## Operating rules

**Always:**
- Include Start and End nodes in every graph
- Use UUID-shaped IDs for all nodes
- Duplicate the type in `data.type`
- Validate before saving
- Treat validation warnings as must-fix, not optional — re-validate until both
  error_count and warning_count are 0 before asking to save
- Ask the human before `flow save` or `flow run`
- Ask the human to pick agent/automation IDs from `agents list` / `rpa list`
- Use exact type casing: `Http`, `Hitl`, `RPA`, `DocumentAI`, `HitlTask`, `JsonParser`, `TextParser`
- If a networked command fails on auth, tell the human and suggest `qcli login --browser`
  rather than retrying silently

**Never:**
- Invent node types not in the schema
- Invent agentId, automationId, or workflowId values — always discover from the platform
- Save or run without human saying "yes"
- Skip validation
- Use `-y/--yes` flags (those bypass the human gate)
