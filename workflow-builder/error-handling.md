# Validation Error Handling

When `qubi flow validate <file>` reports errors or warnings, use this guide to fix them.

**Errors** set `valid: false` and exit code 1 — `flow save` refuses to proceed past
them (without `--skip-validate`). **Warnings** don't fail the exit code, but mean
the graph will misbehave on the canvas or do nothing useful at runtime, so fix them
too before asking the human to save.

---

## Errors

### INVALID_FORMAT

**Meaning:** File is not a valid JSON object.

**Fix:** Ensure the file is valid JSON with `{ "nodes": [...], "edges": [...] }` structure.

---

### INVALID_JSON

**Meaning:** File has JSON syntax errors.

**Fix:** Check for missing commas, unclosed braces, or invalid characters.

---

### MISSING_NODES / MISSING_EDGES

**Meaning:** Top-level `nodes` or `edges` array is missing.

**Fix:** Add the missing array:
```json
{ "nodes": [...], "edges": [], "viewport": {"x":0,"y":0,"zoom":1}, "executionMode": "Sequential" }
```

---

### INVALID_NODES

**Meaning:** The top-level `nodes` key exists but isn't an array.

**Fix:** Make `nodes` a JSON array `[...]`.

---

### INVALID_NODE

**Meaning:** An entry in the `nodes` array isn't a JSON object (e.g. a string or number landed there).

**Fix:** Ensure every element of `nodes` is a `{ ... }` object.

---

### MISSING_NODE_ID

**Meaning:** A node has no `id` field.

**Fix:** Add a UUID-shaped id.

---

### DUPLICATE_NODE_ID

**Meaning:** Two nodes share the same ID.

**Fix:** Generate a new UUID for one of the duplicates.

---

### MISSING_NODE_TYPE

**Meaning:** A node has no `type` field, so its schema can't be checked.

**Fix:** Set `type` to one of the 13 valid node types.

---

### UNKNOWN_NODE_TYPE

**Meaning:** A node has a type that doesn't exist in qubi.

**Fix:** Use only these types: Start, End, Agent, Assign, Branch, Code, DocumentAI, Http, RPA, Hitl, HitlTask, JsonParser, TextParser

Common mistakes:
- `HTTP` → should be `Http`
- `HumanInTheLoop` → should be `Hitl`
- `HITLTask` → should be `HitlTask`

---

### MISSING_REQUIRED_FIELD

**Meaning:** A node is missing a required field in its `data` object. This also fires
if `data` is present but empty, `null`, or not an object — the required fields are
still required, so check [schema-reference.md](./schema-reference.md).

**Fix:** Check [schema-reference.md](./schema-reference.md) for which fields are required per node type and add the missing one.

Common missing fields:
- Agent: `agentId` — run `qubi agents list` to get one
- Http: `method` and `url`
- Code: `language` and `code`
- RPA: `automationId` — run `qubi rpa list` to get one
- HitlTask: `taskName`, `taskType`, `assignTo`
- TextParser: `regexPattern`

---

### MISSING_EDGE_SOURCE / MISSING_EDGE_TARGET

**Meaning:** An edge is missing its `source` or `target` field entirely.

**Fix:** Add the missing field, pointing at a real node `id`.

---

### INVALID_EDGE_SOURCE / INVALID_EDGE_TARGET

**Meaning:** An edge references a node ID that doesn't exist.

**Fix:** Ensure edge `source` and `target` match actual node `id` values.

---

### SELF_LOOP

**Meaning:** An edge connects a node to itself.

**Fix:** Remove the self-referencing edge or fix the target.

---

### INVALID_HTTP_METHOD

**Meaning:** HTTP node has an invalid method — either not in the allowed set, or
not a string at all (a number or boolean landed in `method`).

**Fix:** Use one of: GET, POST, PUT, DELETE, PATCH. (`HEAD`/`OPTIONS` are not
options in the platform's Method dropdown.)

---

### INVALID_CODE_LANGUAGE

**Meaning:** Code node has an invalid language, or `language` isn't a string.

**Fix:** Use one of: javascript, python

---

### FILE_NOT_FOUND

**Meaning:** The path passed to `qubi flow validate` doesn't exist.

**Fix:** Check the path/filename.

---

## Warnings

These do not block validation (exit code stays 0) but should be fixed before
asking the human to save — they describe a graph that passes the structural
check yet won't do what was intended.

### INVALID_NODE_DATA

**Meaning:** A node's `data` field isn't a JSON object (e.g. `null`). Required-field
checks still ran against an empty object, so you'll likely see MISSING_REQUIRED_FIELD
alongside this.

**Fix:** Set `data` to an object with at least `type` and `name`.

---

### DATA_TYPE_MISMATCH

**Meaning:** `data.type` doesn't match the node's own `type` field. The designer
reads both; if they disagree the platform's behavior is undefined.

**Fix:** Set `data.type` to the same value as `type`.

---

### UNREACHABLE_NODE

**Meaning:** No path of edges connects Start to this node. It exists in the
graph but will never run.

**Fix:** Add an edge connecting it into the flow, or delete it if unused.

---

### NO_PATH_TO_END

**Meaning:** No path of edges connects this node to an End node. The flow will
stall on this branch.

**Fix:** Add an outgoing edge so execution can reach End.

---

### DUPLICATE_START / DUPLICATE_END

**Meaning:** More than one Start or End node exists.

**Fix:** Keep exactly one of each; remove or repurpose the extras.

---

### INVALID_NODE_ID_FORMAT

**Meaning:** A node `id` isn't UUID-shaped (e.g. `"start1"`).

**Fix:** Use a UUID-shaped id, e.g. from React Flow's generation pattern.

---

### MISSING_EDGE_ID / EDGE_ID_MISMATCH

**Meaning:** An edge has no `id`, or its `id` doesn't match `xy-edge__{source}-{target}`.

**Fix:** Set the edge's `id` to `xy-edge__{source}-{target}`.

---

### MISSING_VIEWPORT / MISSING_EXECUTION_MODE

**Meaning:** The top-level graph is missing `viewport` or `executionMode`.

**Fix:** Add `"viewport": {"x":0,"y":0,"zoom":1}` and/or `"executionMode": "Sequential"`.

---

### MISSING_POSITION

**Meaning:** A node has no `position` (or it's missing `x`/`y`).

**Fix:** Add `"position": {"x": <number>, "y": <number>}`.

---

### UNKNOWN_DATA_FIELD

**Meaning:** A key in `data` isn't one of that node type's required/optional
fields. Almost always a typo (e.g. `saveOutputas` instead of `saveOutputAs`) —
the field will simply be ignored by the platform, not error.

**Fix:** Rename to the correct field name (the warning suggests one if it's a
close match), or remove it if it's genuinely unused.

---

## Fix Order

When you get multiple errors and warnings:

1. Fix `INVALID_JSON` / `INVALID_FORMAT` first
2. Fix `MISSING_NODES` / `MISSING_EDGES` / `INVALID_NODES` / `INVALID_NODE`
3. Fix `MISSING_START` / `MISSING_END`
4. Fix `UNKNOWN_NODE_TYPE` / `MISSING_NODE_TYPE`
5. Fix `MISSING_REQUIRED_FIELD` / `INVALID_NODE_DATA`
6. Fix `DUPLICATE_NODE_ID`
7. Fix edge errors (`MISSING_EDGE_SOURCE/TARGET`, `INVALID_EDGE_SOURCE/TARGET`, `SELF_LOOP`)
8. Fix remaining warnings (`DATA_TYPE_MISMATCH`, `UNREACHABLE_NODE`, `NO_PATH_TO_END`,
   `UNKNOWN_DATA_FIELD`, ID/edge-id/canvas-key warnings)

Re-validate after each batch. Stop only when both `error_count` and
`warning_count` are 0.

---

## JSON Output

For machine-readable errors:
```bash
qubi flow validate workflow.json --json-output
```

Shape:
```json
{
  "valid": true,
  "node_count": 3,
  "edge_count": 2,
  "error_count": 0,
  "warning_count": 0,
  "errors": [],
  "warnings": []
}
```
Each entry in `errors`/`warnings` has `code`, `message`, and optionally
`node_id`, `node_name`, `field`, `suggestion`.
