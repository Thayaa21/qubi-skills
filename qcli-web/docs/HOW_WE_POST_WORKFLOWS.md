# How We Post Workflows to qubi via API

## TL;DR

We captured the exact API call that qubi's own web designer uses when you click Save. We can make the same call programmatically to inject AI-generated workflows directly into the platform — no GUI interaction needed.

**Proven:** We have a captured real save payload and a working inject script that successfully posts a workflow to the test environment.

---

## The API Endpoint

```
POST /api/v1/workflow/{workflowId}/graph
```

**Base URL:** `https://test.agenthub.qubi.com`

**Full URL example:**
```
https://test.agenthub.qubi.com/api/v1/workflow/57235110-97d2-4613-33a8-08deed4c6154/graph
```

**Auth:** Cookie-based session (after OAuth2 login)

**Content-Type:** `application/json`

---

## The Payload

The body is a JSON object with one field — `graphJson` — which is a **stringified** JSON graph:

```json
{
  "graphJson": "{\"nodes\":[...],\"edges\":[...],\"viewport\":{...},\"executionMode\":\"Sequential\"}"
}
```

Yes, it's double-encoded. The graph is JSON, serialized into a string, wrapped in another JSON object. This is how qubi's own frontend does it.

---

## What Goes Inside `graphJson`

A workflow graph with nodes, edges, viewport, and execution mode:

```json
{
  "nodes": [
    {
      "id": "uuid-v4",
      "type": "Start",
      "position": { "x": 250, "y": 200 },
      "data": { "type": "Start", "name": "Start" }
    },
    {
      "id": "uuid-v4",
      "type": "Http",
      "position": { "x": 450, "y": 200 },
      "data": {
        "type": "Http",
        "name": "Get Weather",
        "method": "GET",
        "url": "https://api.weather.com/current",
        "saveOutputAs": "weatherResult"
      }
    },
    {
      "id": "uuid-v4",
      "type": "End",
      "position": { "x": 700, "y": 200 },
      "data": { "type": "End", "name": "End" }
    }
  ],
  "edges": [
    { "id": "xy-edge__<startId>-<httpId>", "source": "<startId>", "target": "<httpId>" },
    { "id": "xy-edge__<httpId>-<endId>", "source": "<httpId>", "target": "<endId>" }
  ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "executionMode": "Sequential"
}
```

---

## Proof — Captured from the Real Platform

### 1. We intercepted a real Save operation

On **July 29, 2026**, we captured this exact request from the test environment:

```
POST https://test.agenthub.qubi.com/api/v1/workflow/57235110-97d2-4613-33a8-08deed4c6154/graph
```

The payload contained 9 nodes (Start, End, Branch, Code, DocumentAI, Http, RPA, Hitl, HitlTask) with the exact format shown above. File: `schema-extractor/output/save_payload_sample.json`

### 2. We loaded an existing workflow via GET

```
GET https://test.agenthub.qubi.com/api/v1/workflow/89b4b46f-5bd2-4b1a-0420-08ded7cab1f3/graph
```

This returned a real workflow: Start → Agent ("Hanif Test", with agentId, systemPrompt, userMessage) → End. File: `schema-extractor/output/captured_workflows.json`

### 3. We injected a workflow successfully

Our `schema-extractor/inject-workflow.js` script builds a graph (Start → Http GET httpbin.org → End), serializes it, and POSTs it to the save endpoint. It works — the workflow appears on the canvas after a page refresh.

---

## The Full Flow with Claude

```
1. Human tells Claude what workflow to build
2. Claude generates the graph JSON (nodes + edges)
3. qcli validates it locally (offline, no server needed)
4. Claude fixes any errors, re-validates
5. Human confirms: "yes, push it"
6. qcli serializes the graph and POSTs to the save endpoint
7. Workflow appears in qubi's web designer — ready to run
```

---

## What's Needed to Make This Work

| Requirement | Status |
|-------------|--------|
| Know the API endpoint | ✅ Captured from live traffic |
| Know the payload format | ✅ Captured + verified by injection |
| Build valid graphs | ✅ Schema validated with qcli |
| Authenticate | ⚠️ OAuth2 PKCE flow — needs one of: service account, browser-assisted login, or full PKCE implementation |
| Create workflows | ❌ No creation endpoint found — the workflow must already exist (created via the web UI) |

**The only blockers are auth and workflow creation.** The save/write path itself is proven.

---

## Available Node Types (What Claude Can Build)

| Type | What It Does |
|------|-------------|
| Start | Entry point (every flow needs one) |
| End | Exit point (every flow needs one) |
| Agent | Calls a qubi AI agent |
| Http | Makes an HTTP request (GET, POST, etc.) |
| Code | Runs JavaScript or Python code |
| Branch | Conditional routing |
| Assign | Set variables |
| RPA | Triggers a desktop RPA automation |
| DocumentAI | Document processing |
| Hitl | Human-in-the-loop pause |
| HitlTask | Structured human task |
| JsonParser | Parse JSON responses |
| TextParser | Regex-based text extraction |

---

## Example: What Claude Would Generate and We Would POST

**Human says:** "Build a flow that calls the weather API and stores the result"

**Claude generates:**

```json
{
  "nodes": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-111111111111",
      "type": "Start",
      "position": { "x": 100, "y": 200 },
      "data": { "type": "Start", "name": "Start" }
    },
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-222222222222",
      "type": "Http",
      "position": { "x": 350, "y": 200 },
      "data": {
        "type": "Http",
        "name": "Get Weather",
        "method": "GET",
        "url": "https://api.openweathermap.org/data/2.5/weather?q=London",
        "saveOutputAs": "weatherData"
      }
    },
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-333333333333",
      "type": "End",
      "position": { "x": 600, "y": 200 },
      "data": { "type": "End", "name": "End" }
    }
  ],
  "edges": [
    {
      "id": "xy-edge__a1b2c3d4-e5f6-7890-abcd-111111111111-a1b2c3d4-e5f6-7890-abcd-222222222222",
      "source": "a1b2c3d4-e5f6-7890-abcd-111111111111",
      "target": "a1b2c3d4-e5f6-7890-abcd-222222222222"
    },
    {
      "id": "xy-edge__a1b2c3d4-e5f6-7890-abcd-222222222222-a1b2c3d4-e5f6-7890-abcd-333333333333",
      "source": "a1b2c3d4-e5f6-7890-abcd-222222222222",
      "target": "a1b2c3d4-e5f6-7890-abcd-333333333333"
    }
  ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "executionMode": "Sequential"
}
```

**qcli validates it → passes**

**We POST it:**

```bash
qcli flow save workflow.json --workflow-id 57235110-97d2-4613-33a8-08deed4c6154
```

Which sends:

```http
POST /api/v1/workflow/57235110-97d2-4613-33a8-08deed4c6154/graph
Content-Type: application/json
Cookie: <session cookies>

{
  "graphJson": "{\"nodes\":[{\"id\":\"a1b2c3d4...\",...}],\"edges\":[...],\"viewport\":{...},\"executionMode\":\"Sequential\"}"
}
```

**Result:** The workflow appears in the web designer. Refresh the page and it's on the canvas.

---

## Next Steps to Unblock This

1. **Ask the platform team:** Does qubi support a service account or API key for AgentHub? If yes, auth becomes trivial.
2. **If no service account:** Build browser-assisted login — Playwright opens once, user logs in, we extract the cookies. Every subsequent `qcli` call uses those cookies headlessly.
3. **Workflow creation:** Currently we can only write into existing workflows. Ask: is there a `POST /api/v1/workflow` endpoint for creating new ones?

---

## Evidence Files

All captured from the live test environment on July 29, 2026:

| File | What It Contains |
|------|-----------------|
| `schema-extractor/output/save_payload_sample.json` | The exact POST body from a real Save click |
| `schema-extractor/output/captured_workflows.json` | A real workflow loaded via GET |
| `schema-extractor/output/api_calls.json` | Every API endpoint we observed |
| `schema-extractor/output/network_log.json` | Full network traffic (47 requests) |
| `schema-extractor/inject-workflow.js` | Working script that injects a workflow via API |
