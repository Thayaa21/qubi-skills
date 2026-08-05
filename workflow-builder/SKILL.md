---
name: qubi-agentic-flows
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
| Start | name | input, saveOutputAs |
| End | name | input, saveOutputAs |
| Agent | name, **agentId** | input, systemPrompt, userMessage, saveOutputAs |
| Assign | name | assignments |
| Branch | name | conditions, input, saveOutputAs |
| Code | name, language, code | input, saveOutputAs |
| DocumentAI | name, operation | fileVariable, saveOutputAs, input |
| Http | name, method, url | input, headers, body, saveOutputAs |
| RPA | name, **automationId** | input, saveOutputAs |
| Hitl | name | input, saveOutputAs |
| HitlTask | name, taskName, taskType, assignTo | template, saveOutputAs, input |
| JsonParser | name | input, mappings |
| TextParser | name, regexPattern | input, ignoreCase, multiline, singleline, trimOutput, fallbackValue, outputMappings |

**Type name casing matters:** `Http` not `HTTP`, `Hitl` not `HITL`, `RPA` not `Rpa`, `DocumentAI` not `documentAI`.

**Enum constraints:**
- Http.method: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- Code.language: javascript, python

**Rules:**
- Every graph must have exactly one Start node and one End node
- Node IDs must be UUID v4 format, all unique
- `data.type` must match the node's `type` field
- Position nodes at sensible x/y coordinates (100px spacing works)
- Edges must reference existing node IDs, no self-loops

## Phase 3: Validate

```bash
qcli flow validate <file.json>
```

For machine-parseable output:
```bash
qcli flow validate <file.json> --json-output
```

## Phase 4: Fix Errors

If validation fails, fix each error:

| Error Code | Fix |
|-----------|-----|
| INVALID_JSON | Fix JSON syntax |
| MISSING_NODES / MISSING_EDGES | Add the missing top-level key |
| MISSING_NODE_ID | Add a UUID v4 id |
| DUPLICATE_NODE_ID | Generate a new UUID |
| UNKNOWN_NODE_TYPE | Fix the type name (check exact casing) |
| MISSING_REQUIRED_FIELD | Add the field to the node's data |
| INVALID_HTTP_METHOD | Use one of GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS |
| INVALID_CODE_LANGUAGE | Use javascript or python |
| MISSING_START / MISSING_END | Add a Start or End node |
| INVALID_EDGE_SOURCE / TARGET | Fix the edge to reference real node IDs |
| SELF_LOOP | Remove the edge or change the target |

Re-validate after fixing. Repeat until valid.

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
- Validation confirmation (zero errors)
- Confirmation of save to qubi (if requested)
- Job ID from execution (if run requested)

## Operating rules

**Always:**
- Include Start and End nodes in every graph
- Use UUID v4 for all node IDs
- Duplicate the type in `data.type`
- Validate before saving
- Ask the human before `flow save` or `flow run`
- Ask the human to pick agent/automation IDs from `agents list` / `rpa list`
- Use exact type casing: `Http`, `Hitl`, `RPA`, `DocumentAI`, `HitlTask`, `JsonParser`, `TextParser`

**Never:**
- Invent node types not in the schema
- Invent agentId or automationId values — always discover from the platform
- Save or run without human saying "yes"
- Skip validation
- Use `-y/--yes` flags (those bypass the human gate)
