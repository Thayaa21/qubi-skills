---
name: text-parser-nodes
description: "Extract structured values from free text in qubi Agentic Flows with TextParser -- regex patterns, capture-group mappings, and fallbacks. Use when a workflow needs to pull a value out of an email, log line, or unstructured text response."
---

# TextParser Nodes

> TextParser has eight optional fields and almost none of them get exercised in real workflows. This skill is the reference for the ones that get skipped.

## What this skill is

`TextParser` runs a regex against a text input and pulls out one or more capture groups. It appears only 9 times across the 100-workflow evaluation corpus (8 workflows), and its optional-field surface -- `ignoreCase`, `multiline`, `singleline`, `trimOutput`, `fallbackValue`, `outputMappings` -- is the least-exercised of any node type in the schema. Use `JsonParser` instead if the input is actually JSON; `TextParser` is for free text a JSON parser can't touch (email bodies, log lines, PO numbers embedded in prose).

## When to invoke

- The user needs to pull a value out of unstructured text with a regex -- a PO number, an amount, an error code, a reference id
- The user mentions capture groups, regex extraction, or parsing free text (as opposed to JSON)
- `qcli flow validate` reports `MISSING_REQUIRED_FIELD` on a `TextParser` node

## Node reference

| Field | Required | Notes |
|---|---|---|
| `name` | yes | |
| `regexPattern` | yes | |
| `description` | no | |
| `input` | no | |
| `ignoreCase` | no | boolean |
| `multiline` | no | boolean -- `^`/`$` match at line boundaries |
| `singleline` | no | boolean -- `.` matches newlines too |
| `trimOutput` | no | boolean -- trims whitespace from each captured value |
| `fallbackValue` | no | Used when the pattern doesn't match |
| `outputMappings` | no | `[{"group": <int>, "variable": "<name>"}, ...]` -- maps capture groups to variables |

## Phase 1: Write the pattern, then map its groups

Every group you intend to use downstream needs an entry in `outputMappings`. See [fixtures/regex_capture_groups.json](fixtures/regex_capture_groups.json): a single-group pattern (`PO[- ]?(\d{6,8})`) mapped to `poNumber`, with `ignoreCase: true` since PO numbers may appear as `PO-123456` or `po-123456`.

```json
{
  "type": "TextParser",
  "name": "Extract PO Number",
  "regexPattern": "PO[- ]?(\\d{6,8})",
  "ignoreCase": true,
  "outputMappings": [{ "group": 1, "variable": "poNumber" }]
}
```

Remember: this is JSON, so backslashes in the pattern must be escaped (`\\d`, not `\d`).

## Phase 2: Use the flag fields deliberately, not by omission

Don't just skip `multiline`/`singleline`/`trimOutput`/`fallbackValue` because they're optional -- they change matching behavior in ways that are easy to get subtly wrong:

- `multiline: true` if the text spans multiple lines and the pattern uses `^`/`$` anchors
- `singleline: true` if `.` needs to match across newlines (e.g. extracting a multi-line block)
- `trimOutput: true` almost always -- captured text often carries leading/trailing whitespace
- `fallbackValue` whenever a downstream node reads the variable unconditionally, so a non-match doesn't propagate `undefined`

See [fixtures/multiline_with_fallback.json](fixtures/multiline_with_fallback.json) for a worked example extracting an error code from a multi-line log block, with a fallback for the no-match case.

## Phase 3: Validate

```bash
qcli flow validate <file.json>
```

Missing `regexPattern` produces `MISSING_REQUIRED_FIELD` -- see [fixtures/invalid/textparser_no_pattern.json](fixtures/invalid/textparser_no_pattern.json).

## Unverified

| ID | Claim | Why unverifiable offline | How to verify | Status |
|----|-------|---------------------------|----------------|--------|
| UV-TEXTPARSER-01 | The exact shape of `outputMappings` entries beyond `group`/`variable` | The field is optional, so the validator never inspects it | Configure a capture-group mapping in the designer and download the graph | open |

## Operating Rules

**Always:**
- Escape backslashes in `regexPattern` (it's JSON)
- Map every capture group you intend to use in `outputMappings`
- Set `fallbackValue` when the extracted variable is read unconditionally downstream
- Set `trimOutput: true` unless the surrounding whitespace is meaningful

**Never:**
- Use `TextParser` on input that's actually JSON -- use `JsonParser` instead
- Assume a pattern matches without a `fallbackValue` to catch the case where it doesn't
