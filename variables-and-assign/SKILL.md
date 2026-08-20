---
name: variables-and-assign
description: "Move data between nodes in qubi Agentic Flows -- saveOutputAs, {{variable}} interpolation, the Assign node, and Input Source. Use when a workflow needs to pass a value from one step to another."
---

# Variables and Assign

> Every node in a qubi flow is an island unless something explicitly saves its output and something else explicitly reads it. This is the skill that owns that wiring.

## What this skill is

qubi's data-flow model is simple but has no dedicated owner elsewhere in the skill set: a node writes a value with `saveOutputAs`, and any later node reads it with `{{variableName}}` interpolation inside a string field (a URL, a message, a code input). `Assign` is the node that sets variables directly, without needing an API call or an agent to produce them. It's used 15 times across the 100-workflow evaluation corpus -- and notably, **zero times in any of the 20 complex workflows**, which is exactly where explicit configuration variables (API keys, thresholds, environment flags) matter most.

## When to invoke

- A workflow needs a value available to more than one downstream node (a config value, an API key, a threshold)
- The user describes passing data from one step to the next
- `qcli flow validate` reports `UNKNOWN_DATA_FIELD` on an `Assign` node, or a downstream node's `{{variable}}` reference looks wrong

## Node reference

| Field | Required | Notes |
|---|---|---|
| `name` | yes | |
| `description` | no | |
| `assignments` | no | **Optional, so the validator never inspects its shape -- see Unverified.** `[{"variable": "<name>", "value": "<value>"}, ...]` |

Every other node type accepts `input` (source of the node's input -- the designer's only captured option is `"Previous node output"`) and, where applicable, `saveOutputAs` (the variable name to store the result under).

## Phase 1: Set a variable with Assign

```json
{
  "type": "Assign",
  "name": "Set API Key",
  "assignments": [{ "variable": "apiKey", "value": "abc123" }]
}
```

`assignments` takes a list, so one `Assign` node can set several variables at once -- see [fixtures/multiple_assignments.json](fixtures/multiple_assignments.json). Prefer one `Assign` node with multiple entries over several single-variable `Assign` nodes; it keeps configuration in one place on the canvas.

## Phase 2: Read it back with `{{variable}}`

Any string-valued field on a later node can interpolate a variable:

```json
{ "type": "Http", "name": "Fetch Orders", "method": "GET", "url": "https://api.example.com/orders?key={{apiKey}}" }
```

See [fixtures/assign_then_use.json](fixtures/assign_then_use.json) for the minimal Assign-then-use shape, and [fixtures/output_chain.json](fixtures/output_chain.json) for a three-node chain where each node's `saveOutputAs` feeds the next node's `{{variable}}` reference (Http saves `userRaw` → Code reads it and saves `userName` → Agent reads `{{userName}}`).

## Phase 3: Name variables so the chain is traceable

- Use `saveOutputAs` values that describe *what the data is*, not the node that produced it (`orderTotal`, not `httpOutput2`)
- When a variable is only used once, immediately after being set, consider whether it needs `Assign` at all -- a literal inline value may be simpler
- When a variable crosses several nodes, keep its name identical everywhere it's referenced -- a typo in `{{variable}}` fails silently at runtime, since the validator doesn't check interpolation targets (see Unverified)

## Phase 4: Validate

```bash
qcli flow validate <file.json>
```

A typo'd key inside `data` (e.g. `assignmnets` instead of `assignments`) produces `UNKNOWN_DATA_FIELD` -- see [fixtures/invalid/assign_typo_field.json](fixtures/invalid/assign_typo_field.json). The validator does **not** check that `{{variable}}` references inside strings actually correspond to a variable that was set somewhere upstream -- that's a design-time discipline, not something `flow validate` enforces.

## Unverified

| ID | Claim | Why unverifiable offline | How to verify | Status |
|----|-------|---------------------------|----------------|--------|
| UV-ASSIGN-01 | The exact shape of `Assign.assignments` entries | The field is optional, so the validator never inspects it | Configure two assignments in the designer and download the graph | open |
| UV-RUNTIME-01 | `{{variable}}` interpolation semantics at runtime (missing variable, nested objects, type coercion) | No local interpreter; the validator never evaluates templates | Run a flow that interpolates a saved variable and read the job output | open |

## Operating Rules

**Always:**
- Give every `saveOutputAs` a descriptive name
- Keep a variable's name identical at every point it's set and read
- Use one `Assign` node with multiple `assignments` entries rather than several single-purpose ones

**Never:**
- Reference `{{variable}}` for a name that was never set anywhere upstream -- the validator won't catch it, but the run will silently fail to interpolate
- Assume the validator checks `assignments` shape -- it's optional and unchecked, so a typo inside it only surfaces as a runtime problem
