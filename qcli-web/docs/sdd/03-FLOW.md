# The Flow — How It All Works Together (Web Version)

## End-to-End Workflow Creation Flow

```
Human: "Build a workflow that calls an API and parses the response"
  │
  ▼
AI Agent reads SKILL.md → knows Http, JsonParser node types
  │
  ▼
AI Agent generates workflow.json:
  {
    nodes: [Start, Http (GET), JsonParser, End],
    edges: [Start→Http, Http→JsonParser, JsonParser→End]
  }
  │
  ▼
qcli flow validate workflow.json
  │
  ├── PASS → continue
  │
  └── FAIL → AI reads error, fixes, re-validates
  │
  ▼
AI asks: "Ready to save this to qubi?"
  │
  ▼
Human says: "Yes"
  │
  ▼
qcli flow save workflow.json --workflow-id <id>
  │
  ▼
AI asks: "Ready to run?"
  │
  ▼
qcli flow run <id>
  │
  ▼
Workflow executes on qubi platform
```

## Data Flow

```
workflow.json (local file)
    │
    │ qcli flow validate
    ▼
schema.py checks:
  - JSON valid?
  - Has Start + End?
  - All node types known?
  - Required fields present?
  - Edges reference real nodes?
    │
    │ qcli flow save
    ▼
client.py sends:
  POST /api/v1/workflow/{id}/graph
  Body: { "graphJson": "<stringified JSON>" }
    │
    │ qubi server
    ▼
Workflow appears on web designer canvas
    │
    │ qcli flow run
    ▼
Job created → workflow executes
```

## Authentication Flow

```
User runs: qcli login
    │
    ▼
Prompts: Identity Server URL, Tenant, Username, Password
    │
    ▼
POST https://test.identityserver.qubi.com/api/v1/account/login
  Body: { tenantName, userNameOrEmail, password }
    │
    ▼
Receives session cookies
    │
    ▼
Stores at ~/.qcli/session.json
    │
    ▼
All subsequent API calls use these cookies
```

## Validation Error Fix Loop

```
qcli flow validate workflow.json
    │
    ├── MISSING_START → AI adds Start node
    ├── UNKNOWN_NODE_TYPE → AI fixes the type name
    ├── MISSING_REQUIRED_FIELD → AI adds the field
    ├── INVALID_EDGE_TARGET → AI fixes edge references
    │
    ▼
AI re-runs: qcli flow validate workflow.json
    │
    ▼
PASS → proceed to save
```

## The Human Gates

The AI **never** proceeds past these without explicit human confirmation:

1. **Before saving** — "Ready to save this workflow to qubi?"
2. **Before running** — "Ready to execute this workflow?"
3. **When agent/RPA ID needed** — "Which agent should I use? Here are the available ones: ..."

These gates ensure humans stay in control of what goes into the production environment.
