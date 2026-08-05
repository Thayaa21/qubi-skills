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
    "input": { "source": "payload", "sessionVarName": "", "literalValue": "" },
    "saveOutputAs": "variableName"
  }
}
```

The `input` and `saveOutputAs` fields are optional on all nodes.

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
| agentId | yes | UUID — get from `qcli agents list` |
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

```json
{
  "type": "DocumentAI",
  "name": "DocumentAI",
  "operation": "extract",
  "fileVariable": "filePath",
  "saveOutputAs": "documentAi_result"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Display name |
| operation | yes | Operation type (from dropdown) |
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
| method | yes | `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD`, `OPTIONS` |
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
| automationId | yes | UUID — get from `qcli rpa list` |
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

```json
{
  "type": "HitlTask",
  "name": "HitlTask",
  "taskName": "Review Invoice",
  "taskType": "approval",
  "template": "template-uuid",
  "assignTo": "user-or-group-id",
  "saveOutputAs": "hitlResult"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Display name |
| taskName | yes | Human-readable task title |
| taskType | yes | Task category (from dropdown) |
| assignTo | yes | Who handles the task |
| template | no | Form template ID |
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
