---
name: code-nodes
description: "Run inline JavaScript or Python in a qubi Agentic Flow Code node. Use when a workflow needs custom transformation logic that no other node type covers."
---

# Code Nodes

> The designer's dropdown shows `JavaScript`/`Python` in TitleCase; the validator lowercases before checking. This skill documents that gap so nobody "fixes" a casing difference that was never actually broken.

## What this skill is

`Code` runs an inline script -- 105 instances across the evaluation corpus, the third most-used node type. Its only real trap is `language`, and it's a subtler one than it first looks: the designer's captured dropdown offers `JavaScript`/`Python` (TitleCase), but the graph JSON's canonical values are lowercase (`javascript`/`python`). The validator was checked directly and is casing-tolerant -- it lowercases before comparing, so `"JavaScript"` passes. Still, write lowercase: it's the format the schema documents everywhere else, and relying on undocumented leniency is fragile.

## When to invoke

- The user's workflow needs a transformation, calculation, or logic step no other node type covers
- `qubi flow validate` reports `INVALID_CODE_LANGUAGE`

## Node reference

| Field | Required | Notes |
|---|---|---|
| `name` | yes | |
| `language` | yes | `javascript` or `python` (case-tolerant, but write lowercase) |
| `code` | yes | The script body |
| `description` | no | |
| `input` | no | The previous node's output is available as `input` inside the script |
| `saveOutputAs` | no | |

## Phase 1: JavaScript

```json
{ "type": "Code", "name": "Format Message", "language": "javascript",
  "code": "return `Order ${input.orderId} total: $${input.orderTotal}`;" }
```

See [fixtures/js_transform.json](fixtures/js_transform.json).

## Phase 2: Python

```json
{ "type": "Code", "name": "Calculate Total", "language": "python",
  "code": "return input['subtotal'] + input['tax']" }
```

See [fixtures/python_transform.json](fixtures/python_transform.json). Note the return-value convention is the same across both languages: the script's return value becomes the node's output, available to `saveOutputAs` and to downstream `{{variable}}` interpolation.

## Phase 3: Validate

```bash
qubi flow validate <file.json>
```

A language that isn't `javascript`/`python` in any casing (e.g. `typescript`) fails with `INVALID_CODE_LANGUAGE` -- see [fixtures/invalid/invalid_code_language.json](fixtures/invalid/invalid_code_language.json). A non-string `language` value fails the same way rather than crashing.

## Operating Rules

**Always:**
- Write `language` as lowercase `javascript`/`python`, even though the validator tolerates other casing
- Return the value you want stored -- there's no separate "output" field

**Never:**
- Use a language other than javascript/python -- there is no third option
- Assume `Code` can call out to the network or the filesystem -- if the workflow needs that, use `Http` instead
