---
name: validation-triage
description: "Diagnose and fix every qcli flow validate error and warning code, in fix order. Use when validation failed, a downloaded workflow reports warnings, or you got a diagnostic code and don't know which skill owns it."
---

# Validation Triage

> Every code `qcli flow validate` can emit, what it means, and how to fix it -- reachable whether or not you already know which skill built the graph.

## What this skill is

The other skills each own one node type or one design pattern, and each links to `qcli flow validate` as a final step. But the code catalog itself only had one home before this skill existed: buried inside `workflow-builder`, reachable only if that skill happened to be selected first. If someone downloads a workflow a colleague built and `qcli flow validate` reports `EDGE_ID_MISMATCH`, the right skill to reach for isn't "the one that builds workflows from scratch" -- it's this one.

## When to invoke

- `qcli flow validate` printed an error or warning code and the fix isn't obvious
- A downloaded workflow (`qcli flow get`) reports warnings
- You want to know whether a code blocks `flow save` or not

## The severity contract

**Errors** set `valid=False`, exit code 1, and block `qcli flow save`. **Warnings** don't fail the exit code and don't block `flow save` -- but treat them as must-fix. A workflow with `UNREACHABLE_NODE` renders as a disconnected island on the canvas and will never execute past the detachment point; qubi will happily save it anyway.

```bash
qcli flow validate <file.json>              # human-readable
qcli flow validate <file.json> -j           # machine-readable, for scripting a fix loop
```

## Errors (block save)

| Code | Meaning | Fix |
|---|---|---|
| `FILE_NOT_FOUND` | The path passed to `flow validate` doesn't exist | Check the path |
| `INVALID_JSON` | The file isn't valid JSON | Fix the syntax error at the reported location |
| `INVALID_FORMAT` | The top-level value isn't a JSON object | Wrap in `{ "nodes": [...], "edges": [...] }` |
| `MISSING_NODES` / `MISSING_EDGES` | Top-level `nodes` or `edges` key is absent | Add the missing key (even `[]` if empty) |
| `INVALID_NODES` | `nodes` exists but isn't an array | Make it an array |
| `INVALID_NODE` | An entry in `nodes` isn't an object | Fix or remove the malformed entry |
| `INVALID_EDGE` | An entry in `edges` isn't an object | Fix or remove the malformed entry |
| `MISSING_NODE_ID` | A node has no `id` | Add a UUID-shaped id |
| `MISSING_NODE_TYPE` | A node has no `type` | Set `type` to one of the 13 real node types |
| `UNKNOWN_NODE_TYPE` | `type` isn't one of the 13 real types | Fix the casing/spelling -- see the exact list in [workflow-builder/schema-reference.md](../workflow-builder/schema-reference.md) |
| `DUPLICATE_NODE_ID` | Two nodes share an `id` | Generate a new UUID for one of them |
| `MISSING_REQUIRED_FIELD` | A node is missing a field its type requires | Add the field -- see the per-node-type skill (agent-nodes, http-nodes, etc.) |
| `INVALID_HTTP_METHOD` | `Http.method` isn't GET/POST/PUT/DELETE/PATCH | Fix the method -- see [http-nodes](../http-nodes/SKILL.md) |
| `INVALID_CODE_LANGUAGE` | `Code.language` isn't javascript/python | Fix the language -- see [code-nodes](../code-nodes/SKILL.md) (casing is tolerant: `JavaScript` passes, `typescript` doesn't) |
| `MISSING_START` / `MISSING_END` | No `Start` / `End` node in the graph | Add one |
| `MISSING_EDGE_SOURCE` / `MISSING_EDGE_TARGET` | An edge is missing `source`/`target` | Add it |
| `INVALID_EDGE_SOURCE` / `INVALID_EDGE_TARGET` | An edge references a node id that doesn't exist | Fix the id, or add the missing node |
| `SELF_LOOP` | An edge's `source` equals its `target` | Remove the edge or point it somewhere real |

## Warnings (don't block save, but fix them)

| Code | Meaning | Fix |
|---|---|---|
| `UNREACHABLE_NODE` | No path from `Start` reaches this node | Add the missing edge -- see [branch-and-converge](../branch-and-converge/SKILL.md) |
| `NO_PATH_TO_END` | No path from `Start` reaches `End` | Trace the intended route and connect it |
| `DUPLICATE_START` / `DUPLICATE_END` | More than one Start/End node | Keep exactly one, or connect every extra one meaningfully |
| `MISSING_VIEWPORT` / `MISSING_EXECUTION_MODE` | Top-level `viewport`/`executionMode` is absent | Add `{"x":0,"y":0,"zoom":1}` / `"Sequential"` |
| `MISSING_EDGE_ID` | An edge has no `id` | Add `xy-edge__{source}-{target}` |
| `EDGE_ID_MISMATCH` | An edge's `id` doesn't match `xy-edge__{source}-{target}` | Fix the id to match |
| `MISSING_POSITION` | A node has no `position` (or it's incomplete) | Add `{"x": <n>, "y": <n>}` |
| `INVALID_NODE_ID_FORMAT` | A node's `id` isn't UUID-shaped | Use a real UUID |
| `INVALID_NODE_DATA` | A node's `data` isn't an object | Set `data` to an object with at least `type` and `name` |
| `DATA_TYPE_MISMATCH` | `data.type` doesn't match the node's own `type` | Make them match |
| `UNKNOWN_DATA_FIELD` | A key in `data` isn't a recognized field for that node type | Fix a likely typo, or remove it |

## Fix order

1. Structural errors first (`INVALID_FORMAT`, `MISSING_NODES`/`MISSING_EDGES`, `INVALID_NODES`) -- nothing else can be checked until these pass
2. Per-node errors (`MISSING_NODE_ID`, `UNKNOWN_NODE_TYPE`, `MISSING_REQUIRED_FIELD`, enum errors)
3. Edge errors (`MISSING_EDGE_SOURCE`/`TARGET`, `INVALID_EDGE_SOURCE`/`TARGET`, `SELF_LOOP`)
4. `MISSING_START`/`MISSING_END`
5. Re-validate -- warnings only appear once the graph parses cleanly enough to check connectivity
6. Warnings, especially `UNREACHABLE_NODE`/`NO_PATH_TO_END`

Re-validate after every fix. Fixing one structural error often reveals the next one.

## Fixtures

[fixtures/clean_baseline.json](fixtures/clean_baseline.json) validates with zero errors and zero warnings. Every other file in `fixtures/invalid/` reproduces exactly one row of the tables above (see `fixtures/invalid/expected.json` for the exact code each one produces) -- useful as a reference for what a given code actually looks like in JSON.

## Operating Rules

**Always:**
- Fix structural errors before per-node errors -- later checks can't run until the graph parses
- Re-validate after every fix rather than batching changes
- Treat warnings as must-fix even though they don't block `flow save`

**Never:**
- Use `--skip-validate` on `flow save` to work around an error you haven't understood
- Assume a warning is safe to ignore because the exit code is 0
