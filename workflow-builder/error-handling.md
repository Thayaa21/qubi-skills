# Validation Error Handling

When `qcli flow validate <file>` reports errors, use this guide to fix them.

---

## Error Codes

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

### MISSING_START

**Meaning:** No node with type "Start" found.

**Fix:** Add a Start node:
```json
{ "id": "uuid", "type": "Start", "position": {"x":100,"y":200}, "data": {"type":"Start","name":"Start"} }
```

---

### MISSING_END

**Meaning:** No node with type "End" found.

**Fix:** Add an End node and connect the last processing node to it.

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

**Meaning:** A node is missing a required field in its `data` object.

**Fix:** Check the [schema-reference.md](./schema-reference.md) for which fields are required per node type and add the missing one.

Common missing fields:
- Agent: `agentId` — run `qcli agents list` to get one
- Http: `method` and `url`
- Code: `language` and `code`
- RPA: `automationId` — run `qcli rpa list` to get one
- HitlTask: `taskName`, `taskType`, `assignTo`
- TextParser: `regexPattern`

---

### DUPLICATE_NODE_ID

**Meaning:** Two nodes share the same ID.

**Fix:** Generate a new UUID for one of the duplicates.

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

**Meaning:** HTTP node has an invalid method.

**Fix:** Use one of: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS

---

### INVALID_CODE_LANGUAGE

**Meaning:** Code node has an invalid language.

**Fix:** Use one of: javascript, python

---

## Fix Order

When you get multiple errors:

1. Fix `INVALID_JSON` / `INVALID_FORMAT` first
2. Fix `MISSING_NODES` / `MISSING_EDGES`
3. Fix `MISSING_START` / `MISSING_END`
4. Fix `UNKNOWN_NODE_TYPE`
5. Fix `MISSING_REQUIRED_FIELD`
6. Fix `DUPLICATE_NODE_ID`
7. Fix edge errors

Re-validate after each batch.

---

## JSON Output

For machine-readable errors:
```bash
qcli flow validate workflow.json --json-output
```
