# Workflow Examples

Complete, working examples of qubi Agentic Flows workflows.

---

## Example 1: Simple Agent Call

Start → Agent → End. Calls an AI agent to generate a random quote.

<!-- UV-AGENT-01: agentId below is a real captured session value ("Hanif Test"
     agent, schema-extractor/output/captured_workflows.json), not invented --
     but agentIds are tenant-specific, so treat it as an example shape only.
     Always get the real one for the human's tenant from `qubi agents list`. -->

```json
{
  "nodes": [
    {
      "id": "f4ca28f9-caec-4dff-9f50-22488fdfff11",
      "type": "Start",
      "position": { "x": 250, "y": 200 },
      "data": { "type": "Start", "name": "Start" }
    },
    {
      "id": "9c162b3d-241a-4844-965a-4aa7610028d8",
      "type": "Agent",
      "position": { "x": 450, "y": 200 },
      "data": {
        "type": "Agent",
        "name": "Quote Generator",
        "agentId": "e9af665c-6bd1-4644-6333-08dee4aa9ecc",
        "input": { "source": "payload", "sessionVarName": "", "literalValue": "" },
        "systemPrompt": "Output a random quote",
        "userMessage": "Output a random quote",
        "saveOutputAs": "quoteResult"
      }
    },
    {
      "id": "fb806082-ba85-464d-bdf8-8a0bccc5195c",
      "type": "End",
      "position": { "x": 700, "y": 200 },
      "data": { "type": "End", "name": "End" }
    }
  ],
  "edges": [
    {
      "id": "xy-edge__f4ca28f9-caec-4dff-9f50-22488fdfff11-9c162b3d-241a-4844-965a-4aa7610028d8",
      "source": "f4ca28f9-caec-4dff-9f50-22488fdfff11",
      "target": "9c162b3d-241a-4844-965a-4aa7610028d8"
    },
    {
      "id": "xy-edge__9c162b3d-241a-4844-965a-4aa7610028d8-fb806082-ba85-464d-bdf8-8a0bccc5195c",
      "source": "9c162b3d-241a-4844-965a-4aa7610028d8",
      "target": "fb806082-ba85-464d-bdf8-8a0bccc5195c"
    }
  ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "executionMode": "Sequential"
}
```

---

## Example 2: HTTP Call + JSON Parse

Start → HTTP (GET) → JsonParser → End

```json
{
  "nodes": [
    {
      "id": "a1000000-0000-0000-0000-000000000001",
      "type": "Start",
      "position": { "x": 100, "y": 200 },
      "data": { "type": "Start", "name": "Start" }
    },
    {
      "id": "a2000000-0000-0000-0000-000000000002",
      "type": "Http",
      "position": { "x": 300, "y": 200 },
      "data": {
        "type": "Http",
        "name": "Fetch Users",
        "method": "GET",
        "url": "https://jsonplaceholder.typicode.com/users/1",
        "saveOutputAs": "apiResponse"
      }
    },
    {
      "id": "a3000000-0000-0000-0000-000000000003",
      "type": "JsonParser",
      "position": { "x": 550, "y": 200 },
      "data": {
        "type": "JsonParser",
        "name": "Extract Name",
        "input": { "source": "payload" },
        "mappings": [
          { "jsonPath": "$.name", "variable": "userName" },
          { "jsonPath": "$.email", "variable": "userEmail" }
        ]
      }
    },
    {
      "id": "a4000000-0000-0000-0000-000000000004",
      "type": "End",
      "position": { "x": 800, "y": 200 },
      "data": { "type": "End", "name": "End" }
    }
  ],
  "edges": [
    { "id": "xy-edge__a1000000-0000-0000-0000-000000000001-a2000000-0000-0000-0000-000000000002", "source": "a1000000-0000-0000-0000-000000000001", "target": "a2000000-0000-0000-0000-000000000002" },
    { "id": "xy-edge__a2000000-0000-0000-0000-000000000002-a3000000-0000-0000-0000-000000000003", "source": "a2000000-0000-0000-0000-000000000002", "target": "a3000000-0000-0000-0000-000000000003" },
    { "id": "xy-edge__a3000000-0000-0000-0000-000000000003-a4000000-0000-0000-0000-000000000004", "source": "a3000000-0000-0000-0000-000000000003", "target": "a4000000-0000-0000-0000-000000000004" }
  ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "executionMode": "Sequential"
}
```

---

## Example 3: Code Processing

Start → Assign (set input) → Code (transform) → End

```json
{
  "nodes": [
    {
      "id": "b1000000-0000-0000-0000-000000000001",
      "type": "Start",
      "position": { "x": 100, "y": 200 },
      "data": { "type": "Start", "name": "Start" }
    },
    {
      "id": "b2000000-0000-0000-0000-000000000002",
      "type": "Assign",
      "position": { "x": 300, "y": 200 },
      "data": {
        "type": "Assign",
        "name": "Set Input",
        "assignments": [
          { "variable": "names", "value": "[\"Alice\", \"Bob\", \"Charlie\"]" }
        ]
      }
    },
    {
      "id": "b3000000-0000-0000-0000-000000000003",
      "type": "Code",
      "position": { "x": 550, "y": 200 },
      "data": {
        "type": "Code",
        "name": "Format Names",
        "language": "javascript",
        "code": "const names = JSON.parse(input.names);\nreturn names.map(n => n.toUpperCase()).join(', ');",
        "saveOutputAs": "formattedNames"
      }
    },
    {
      "id": "b4000000-0000-0000-0000-000000000004",
      "type": "End",
      "position": { "x": 800, "y": 200 },
      "data": { "type": "End", "name": "End" }
    }
  ],
  "edges": [
    { "id": "xy-edge__b1000000-0000-0000-0000-000000000001-b2000000-0000-0000-0000-000000000002", "source": "b1000000-0000-0000-0000-000000000001", "target": "b2000000-0000-0000-0000-000000000002" },
    { "id": "xy-edge__b2000000-0000-0000-0000-000000000002-b3000000-0000-0000-0000-000000000003", "source": "b2000000-0000-0000-0000-000000000002", "target": "b3000000-0000-0000-0000-000000000003" },
    { "id": "xy-edge__b3000000-0000-0000-0000-000000000003-b4000000-0000-0000-0000-000000000004", "source": "b3000000-0000-0000-0000-000000000003", "target": "b4000000-0000-0000-0000-000000000004" }
  ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "executionMode": "Sequential"
}
```

---

## Patterns to Follow

### Linear Flow
```
Start → [Node A] → [Node B] → End
```
Every node connects to the next via an edge. Always start with Start, end with End.

### ID Convention
Use UUID v4 for all node IDs. Edge IDs follow: `xy-edge__{{sourceId}}-{{targetId}}`

### Position Layout
Space nodes horizontally with ~200px gaps:
- Start: x=100
- First processing node: x=300
- Second: x=550
- End: x=800

All at the same y (200) for a clean horizontal layout.
