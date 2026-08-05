# qubi Agentic Flows — Graph Schema

The workflow graph format used by qubi's web designer (React Flow based).

---

## Top-Level Structure

```json
{
  "nodes": [ ... ],
  "edges": [ ... ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "executionMode": "Sequential"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `nodes` | array | All workflow nodes |
| `edges` | array | Connections between nodes |
| `viewport` | object | Canvas pan/zoom state |
| `executionMode` | string | `"Sequential"` (may support parallel in future) |

---

## Node Structure

```json
{
  "id": "uuid-v4",
  "type": "NodeType",
  "position": { "x": 250, "y": 200 },
  "data": {
    "type": "NodeType",
    "name": "Display Name",
    ...node-specific fields
  },
  "measured": { "width": 140, "height": 59 },
  "selected": false,
  "dragging": false
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | UUID v4, unique per node |
| `type` | string | Node type identifier (see below) |
| `position` | `{x, y}` | Canvas coordinates |
| `data` | object | All node configuration (type-specific) |
| `measured` | `{width, height}` | Rendered size in pixels |
| `selected` | boolean | UI state |
| `dragging` | boolean | UI state |

---

## Edge Structure

```json
{
  "id": "xy-edge__{sourceId}-{targetId}",
  "source": "source-node-uuid",
  "target": "target-node-uuid"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Format: `xy-edge__{sourceId}-{targetId}` |
| `source` | string | UUID of the source node |
| `target` | string | UUID of the target node |

Edge IDs follow the pattern: `xy-edge__` + source UUID + `-` + target UUID.

---

## Node Types & Their Data Fields

### Start

```json
{
  "type": "Start",
  "name": "Start"
}
```

Minimal node — just a name. Entry point of the workflow.

---

### End

```json
{
  "type": "End",
  "name": "End"
}
```

Minimal node — just a name. Exit point of the workflow.

---

### Agent

```json
{
  "type": "Agent",
  "name": "My Agent Call",
  "agentId": "uuid-of-agent",
  "input": {
    "source": "payload",
    "sessionVarName": "",
    "literalValue": ""
  },
  "systemPrompt": "You are a helpful assistant...",
  "userMessage": "Summarize the following: {{input}}",
  "saveOutputAs": "agentResult"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Display name |
| `agentId` | string | yes | UUID of agent from `/api/v1/getallagents` |
| `input.source` | string | no | `"payload"` or `"variable"` or `"literal"` |
| `input.sessionVarName` | string | no | Variable name if source is variable |
| `input.literalValue` | string | no | Literal value if source is literal |
| `systemPrompt` | string | no | System prompt for the agent |
| `userMessage` | string | no | User message / prompt |
| `saveOutputAs` | string | no | Variable name to store output |

---

### Assign

```json
{
  "type": "Assign",
  "name": "Assign",
  "assignments": [
    { "variable": "myVar", "value": "hello world" }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Display name |
| `assignments` | array | no | List of `{variable, value}` pairs |

---

### Branch

```json
{
  "type": "Branch",
  "name": "Branch",
  "conditions": [...]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Display name |
| `conditions` | array | no | Branch conditions (multiple output paths) |

---

### Code

```json
{
  "type": "Code",
  "name": "Code",
  "language": "javascript",
  "code": "return input.toUpperCase();",
  "saveOutputAs": "codeResult"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Display name |
| `language` | string | yes | `"javascript"` or `"python"` |
| `code` | string | yes | The code to execute |
| `saveOutputAs` | string | no | Variable to store result |

---

### DocumentAI

```json
{
  "type": "DocumentAI",
  "name": "DocumentAI",
  "operation": "extract",
  "fileVariable": "filePath",
  "saveOutputAs": "documentAi_result"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Display name |
| `operation` | string | yes | Operation type (select from available) |
| `fileVariable` | string | no | Variable holding the file path |
| `saveOutputAs` | string | no | Variable to store result |

---

### Http

```json
{
  "type": "Http",
  "name": "Http",
  "method": "GET",
  "url": "https://api.example.com/users/{{userId}}",
  "input": {
    "source": "payload",
    "sessionVarName": "",
    "literalValue": ""
  },
  "saveOutputAs": "httpResult"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Display name |
| `method` | string | yes | `GET`, `POST`, `PUT`, `DELETE`, `PATCH` |
| `url` | string | yes | URL with optional `{{variable}}` interpolation |
| `input.source` | string | no | Input source for request body |
| `saveOutputAs` | string | no | Variable to store response |

---

### RPA

```json
{
  "type": "RPA",
  "name": "RPA",
  "automationId": "uuid-of-automation",
  "saveOutputAs": "rpaResult"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Display name |
| `automationId` | string | yes | UUID from `/api/v1/getrpaautomations` |
| `saveOutputAs` | string | no | Variable to store result |

---

### Hitl (Human In The Loop — container)

```json
{
  "type": "Hitl",
  "name": "Hitl"
}
```

Container node that holds HITL Task nodes. Minimal configuration.

---

### HitlTask

```json
{
  "type": "HitlTask",
  "name": "HitlTask",
  "taskName": "Review Document",
  "taskType": "approval",
  "template": "template-id",
  "assignTo": "user-or-group-id",
  "saveOutputAs": "hitlResult"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Display name |
| `taskName` | string | yes | Human-readable task name |
| `taskType` | string | yes | Type of task (select) |
| `template` | string | no | Template ID (select) |
| `assignTo` | string | yes | Who to assign the task to |
| `saveOutputAs` | string | no | Variable to store result |

---

### JsonParser

```json
{
  "type": "JsonParser",
  "name": "JsonParser",
  "input": { "source": "payload" },
  "mappings": [
    { "jsonPath": "$.data.name", "variable": "userName" }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Display name |
| `input.source` | string | no | Input source |
| `mappings` | array | no | JSON path → variable mappings |

---

### TextParser

```json
{
  "type": "TextParser",
  "name": "TextParser",
  "input": { "source": "payload" },
  "regexPattern": "Order #(\\d+)",
  "ignoreCase": false,
  "multiline": false,
  "singleline": false,
  "trimOutput": false,
  "fallbackValue": "",
  "outputMappings": [
    { "group": 1, "variable": "orderId" }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Display name |
| `input.source` | string | no | Input source |
| `regexPattern` | string | yes | Regular expression |
| `ignoreCase` | boolean | no | Regex flag |
| `multiline` | boolean | no | Regex flag |
| `singleline` | boolean | no | Dot matches newline |
| `trimOutput` | boolean | no | Trim whitespace from result |
| `fallbackValue` | string | no | Value if no match |
| `outputMappings` | array | no | Capture group → variable mappings |

---

## Common Fields (All Node Types)

Every node has these base fields in `data`:

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Same as the node's `type` field |
| `name` | string | Display name |
| `input` | object | Optional: `{ source, sessionVarName, literalValue }` |
| `saveOutputAs` | string | Optional: variable name to store node output |

---

## Variable Interpolation

Variables are referenced using double-brace syntax: `{{variableName}}`

Example URL: `https://api.example.com/users/{{userId}}`

---

## Example: Complete Workflow

```json
{
  "nodes": [
    {
      "id": "f4ca28f9-caec-4dff-9f50-22488fdfff11",
      "type": "Start",
      "position": { "x": 248, "y": 194 },
      "data": { "type": "Start", "name": "Start" }
    },
    {
      "id": "9c162b3d-241a-4844-965a-4aa7610028d8",
      "type": "Agent",
      "position": { "x": 382, "y": 190 },
      "data": {
        "type": "Agent",
        "name": "Hanif Test",
        "agentId": "e9af665c-6bd1-4644-6333-08dee4aa9ecc",
        "input": { "source": "payload", "sessionVarName": "", "literalValue": "" },
        "systemPrompt": "Output a random quote",
        "userMessage": "Output a random quote",
        "saveOutputAs": "newVariable"
      }
    },
    {
      "id": "fb806082-ba85-464d-bdf8-8a0bccc5195c",
      "type": "End",
      "position": { "x": 628, "y": 297 },
      "data": { "type": "End", "name": "End" }
    }
  ],
  "edges": [
    {
      "source": "f4ca28f9-caec-4dff-9f50-22488fdfff11",
      "target": "9c162b3d-241a-4844-965a-4aa7610028d8",
      "id": "xy-edge__f4ca28f9-caec-4dff-9f50-22488fdfff11-9c162b3d-241a-4844-965a-4aa7610028d8"
    },
    {
      "source": "9c162b3d-241a-4844-965a-4aa7610028d8",
      "target": "fb806082-ba85-464d-bdf8-8a0bccc5195c",
      "id": "xy-edge__9c162b3d-241a-4844-965a-4aa7610028d8-fb806082-ba85-464d-bdf8-8a0bccc5195c"
    }
  ],
  "viewport": { "x": -111, "y": -30, "zoom": 1.56 },
  "executionMode": "Sequential"
}
```

This workflow: **Start → Agent (outputs a random quote) → End**
