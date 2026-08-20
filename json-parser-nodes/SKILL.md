---
name: json-parser-nodes
description: "Extract fields from JSON responses in qubi Agentic Flows with JsonParser mappings. Use when a workflow needs to pull specific fields out of an API response or other JSON data."
---

# JsonParser Nodes

> `mappings` is optional, so the validator never inspects its shape. This skill is the concrete reference for what a correct one actually looks like.

## What this skill is

`JsonParser` extracts specific fields from a JSON value (almost always a prior `Http` node's response) into named variables, using JSON path expressions. It appears 22 times across the evaluation corpus. Use this instead of `TextParser` whenever the input is already JSON -- `TextParser`'s regex approach is for free text, not structured data (see [text-parser-nodes](../text-parser-nodes/SKILL.md)).

## When to invoke

- The user needs to pull one or more specific fields out of a JSON API response
- A workflow design mentions extracting, parsing, or reading fields from JSON

## Node reference

| Field | Required | Notes |
|---|---|---|
| `name` | yes | |
| `description` | no | |
| `input` | no | Typically `{"source": "<variable>"}` naming the JSON-holding variable |
| `mappings` | no | **Optional, so the validator never inspects its shape -- see Unverified.** `[{"jsonPath": "$.field", "variable": "name"}, ...]` |

## Phase 1: One mapping per field you need

```json
{
  "type": "JsonParser",
  "name": "Extract Name and Email",
  "input": { "source": "userRaw" },
  "mappings": [
    { "jsonPath": "$.name", "variable": "userName" },
    { "jsonPath": "$.email", "variable": "userEmail" }
  ]
}
```

See [fixtures/http_json_parse.json](fixtures/http_json_parse.json) for the full Http-then-parse shape.

## Phase 2: Nested paths and array indices

`jsonPath` expressions can reach into nested objects and index arrays: `$.orders[0].total` extracts the first order's total. See [fixtures/nested_mappings.json](fixtures/nested_mappings.json).

## Phase 3: Validate

```bash
qcli flow validate <file.json>
```

`mappings` is optional and its contents are unchecked -- a typo in a `jsonPath` expression or a missing `variable` key will not surface as a validation error. Only a real run against real data reveals a bad path.

## Unverified

| ID | Claim | Why unverifiable offline | How to verify | Status |
|----|-------|---------------------------|----------------|--------|
| UV-JSONPARSER-01 | Whether `jsonPath` supports the full JSONPath spec (filters, wildcards) or only simple dotted/indexed paths | The field is optional, so the validator never inspects it | Configure a mapping with a filter expression in the designer and see if it's accepted | open |

## Operating Rules

**Always:**
- Point `input.source` at a variable that actually holds JSON (typically an `Http` node's `saveOutputAs`)
- Give every mapping a descriptive `variable` name
- Use `JsonParser`, not `TextParser`, when the input is already JSON

**Never:**
- Assume the validator catches a bad `jsonPath` -- `mappings` is unchecked, so this only surfaces at runtime
