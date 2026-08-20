# Node Type Schema Reference

Complete reference for all qubi Agentic Flows node types and their data fields.

---

## Common Fields (All Nodes)

Every node has this structure:

```json
{
  "id": "uuid-v4",
  "type": "NodeType",
  "position": { "x": 0, "y": 0 },
  "data": {
    "type": "NodeType",
    "name": "Display Name",
    "description": "",
    "input": { "source": "payload", "sessionVarName": "", "literalValue": "" },
    "saveOutputAs": "variableName"
  }
}
```

The `description`, `input`, and `saveOutputAs` fields are optional on all nodes.
Any `data` key outside a type's documented required/optional fields (plus `type`
and `description`) is treated as an unrecognised field — the validator will warn
with `UNKNOWN_DATA_FIELD`, since it's almost always a typo of a real field name.

**Input source options:** `"payload"` (previous node output), `"variable"`, `"literal"`

---

## Start

Entry point. Every workflow must have exactly one.

```json
{ "type": "Start", "name": "Start" }
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Always "Start" |

---

## End

Exit point. Every workflow must have at least one.

```json
{ "type": "End", "name": "End" }
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Always "End" |

---

## Agent

Calls an AI agent (LLM).

```json
{
  "type": "Agent",
  "name": "My Agent",
  "agentId": "uuid-from-agents-list",
  "input": { "source": "payload", "sessionVarName": "", "literalValue": "" },
  "systemPrompt": "You are a helpful assistant",
  "userMessage": "Summarize: {{inputText}}",
  "saveOutputAs": "agentResult"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Display name |
| agentId | yes | UUID — get from `qubi agents list` |
| systemPrompt | no | System instruction for the agent |
| userMessage | no | User prompt (supports `{{vars}}`) |
| saveOutputAs | no | Variable to store output |

---

## Assign

Sets variable values.

```json
{
  "type": "Assign",
  "name": "Assign",
  "assignments": [
    { "variable": "greeting", "value": "Hello World" },
    { "variable": "count", "value": "42" }
  ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Display name |
| assignments | no | Array of `{variable, value}` pairs |

---

## Branch

Conditional routing (if/else paths).

```json
{
  "type": "Branch",
  "name": "Branch",
  "conditions": [
    { "expression": "{{status}} == 'approved'", "targetNodeId": "uuid" }
  ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Display name |
| conditions | no | Array of condition objects |

Branch nodes have multiple output edges — one per condition plus a default.

---

## Code

Executes JavaScript or Python code.

```json
{
  "type": "Code",
  "name": "Code",
  "language": "javascript",
  "code": "const result = input.map(x => x * 2);\nreturn result;",
  "saveOutputAs": "codeResult"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Display name |
| language | yes | `"javascript"` or `"python"` |
| code | yes | The code to execute |
| saveOutputAs | no | Variable to store result |

The `input` variable is available in code and contains the previous node's output.

---

## DocumentAI

Document processing (OCR, extraction, classification).

<!-- UV-DOCAI-01: `operation` is a required dropdown on the designer whose
     option list was never captured. Do not invent a value ("extract" is
     not confirmed) -- ask the human, or open the node in the designer. -->

```json
{
  "type": "DocumentAI",
  "name": "DocumentAI",
  "operation": "UNVERIFIED",
  "fileVariable": "filePath",
  "saveOutputAs": "documentAi_result"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Display name |
| operation | yes | Operation type — **platform dropdown select**, not free text. The exact option list wasn't captured; ask the human which operation before inventing a value |
| fileVariable | no | Variable containing file path |
| saveOutputAs | no | Variable to store result |

---

## Http

Makes HTTP API calls.

```json
{
  "type": "Http",
  "name": "Http",
  "method": "GET",
  "url": "https://api.example.com/data/{{id}}",
  "input": { "source": "payload" },
  "saveOutputAs": "httpResult"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Display name |
| method | yes | `GET`, `POST`, `PUT`, `DELETE`, `PATCH` — this is the platform's full dropdown list, no other values are valid |
| url | yes | URL (supports `{{variable}}` interpolation) |
| saveOutputAs | no | Variable to store response |

---

## RPA

Triggers an RPA automation.

```json
{
  "type": "RPA",
  "name": "RPA",
  "automationId": "uuid-from-rpa-list",
  "saveOutputAs": "rpaResult"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Display name |
| automationId | yes | UUID — get from `qubi rpa list` |
| saveOutputAs | no | Variable to store result |

---

## Hitl (Human In The Loop — Container)

Container that holds HitlTask nodes.

```json
{ "type": "Hitl", "name": "Hitl" }
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Display name |

---

## HitlTask

Creates a task for a human to complete.

<!-- UV-HITLTASK-01: `taskType` and `assignTo` are required dropdowns whose
     option lists were never captured ("approval" below is not confirmed);
     `template` is a tenant-specific dropdown too. Ask the human, or open the
     node in the designer. -->

```json
{
  "type": "HitlTask",
  "name": "HitlTask",
  "taskName": "Review Invoice",
  "taskType": "UNVERIFIED",
  "template": "template-uuid",
  "assignTo": "user-or-group-id",
  "saveOutputAs": "hitlResult"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Display name |
| taskName | yes | Human-readable task title |
| taskType | yes | Task category — **platform dropdown select**, not free text. Ask the human for a valid value rather than inventing one |
| assignTo | yes | Who handles the task — a real user/group id from the platform, not a name you make up |
| template | no | Form template ID — **platform dropdown select** when set |
| saveOutputAs | no | Variable to store result |

---

## JsonParser

Extracts values from JSON using JSON paths.

```json
{
  "type": "JsonParser",
  "name": "JsonParser",
  "input": { "source": "payload" },
  "mappings": [
    { "jsonPath": "$.data.name", "variable": "userName" },
    { "jsonPath": "$.data.email", "variable": "userEmail" }
  ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Display name |
| mappings | no | Array of `{jsonPath, variable}` |

---

## TextParser

Extracts values from text using regex.

```json
{
  "type": "TextParser",
  "name": "TextParser",
  "input": { "source": "payload" },
  "regexPattern": "Order #(\\d+)",
  "ignoreCase": false,
  "multiline": false,
  "singleline": false,
  "trimOutput": true,
  "fallbackValue": "unknown",
  "outputMappings": [
    { "group": 1, "variable": "orderId" }
  ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Display name |
| regexPattern | yes | Regular expression |
| ignoreCase | no | Default false |
| multiline | no | Default false |
| singleline | no | Dot matches newline. Default false |
| trimOutput | no | Trim whitespace. Default false |
| fallbackValue | no | Value if no match |
| outputMappings | no | Capture group → variable mappings |

---

## Edge Format

```json
{
  "id": "xy-edge__{{sourceId}}-{{targetId}}",
  "source": "source-node-uuid",
  "target": "target-node-uuid"
}
```

Edge IDs follow the pattern: `xy-edge__` + source UUID + `-` + target UUID.
