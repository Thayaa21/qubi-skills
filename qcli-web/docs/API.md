# qubi Agentic Flows — API Reference

Extracted from the real test environment at `https://test.agenthub.qubi.com`.

---

## Authentication

### Login Flow (OAuth2 / OpenID Connect)

The platform uses an external Identity Server with OAuth2 Authorization Code + PKCE flow.

```
1. GET  /api/login
   → Redirects to Identity Server authorize endpoint

2. Identity Server: https://test.identityserver.qubi.com/Account/Login
   Fields: Tenant, Email/UserName, Password
   App: Blazor (.NET) with MudBlazor UI

3. POST https://test.identityserver.qubi.com/api/v1/account/login
   Body: { tenant, username, password }

4. Redirect back: GET /api/callback/login/local?code=...&state=...
   → Sets session cookie / returns JWT
```

**Client ID:** `AgentHub`  
**Scopes:** `openid email profile roles api`  
**Auth method:** Cookie-based session after OAuth callback (no raw Bearer token exposed to frontend)

---

## Workflow Endpoints

### List/Search Workflows

```
POST /api/v1/workflow/search
Body: { search criteria }
Returns: Array of workflow metadata
```

### Get Workflow Graph (Load)

```
GET /api/v1/workflow/{workflowId}/graph
Returns: string (JSON-serialized graph)
```

The response is a **JSON string** containing the React Flow graph:
```json
{
  "nodes": [...],
  "edges": [...],
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "executionMode": "Sequential"
}
```

### Save Workflow Graph

```
POST /api/v1/workflow/{workflowId}/graph
Content-Type: application/json
Body: {
  "graphJson": "<serialized JSON string>"
}
```

The `graphJson` value is a **stringified** JSON object (double-encoded).

### Get Workflow Versions

```
GET /api/v1/getworkflowversionlist?workflowId={workflowId}
Returns: Array of version entries
```

### Get Workflow Variables

```
GET /api/v1/getworkflowvariablelist?workflowId={workflowId}
Returns: Array of workflow-level variables
```

---

## Supporting Endpoints

### Dashboard

```
GET /api/v1/getdashboarddata
Returns: Dashboard summary data
```

### Agents

```
GET /api/v1/getallagents
Returns: Array of available AI agents with their IDs and config
```

### RPA Automations

```
GET /api/v1/getrpaautomations
Returns: Array of available RPA automation definitions
```

### Jobs

```
POST /api/v1/job/search
Body: { search criteria }
Returns: Array of job/execution records
```

### Auth Token (refresh)

```
GET /api/auth/token
Returns: Current session token info
```

---

## Base URLs

| Environment | AgentHub | Identity Server |
|-------------|----------|-----------------|
| Test | `https://test.agenthub.qubi.com` | `https://test.identityserver.qubi.com` |

---

## Notes

- The web app is built with **Next.js** (App Router, Turbopack)
- The workflow designer uses **React Flow** (xyflow)
- Identity Server is **Blazor** (.NET) with **MudBlazor** components and **SignalR** for real-time updates
- All API calls use cookie-based authentication after the OAuth flow completes
- The `graphJson` field is double-encoded: the POST body is JSON, and the `graphJson` value inside it is a JSON string
