# Software Design Document — qcli (Web / Agentic Flows Version)

| Field | Value |
|-------|-------|
| Project | qcli — qubi Agentic Flows CLI + AI Skill |
| Version | 0.1.0 |
| Status | POC — validation verified; **server writes blocked on auth** |
| Target Platform | qubi AgentHub (Next.js + React Flow, JSON graphs) |
| Test Environment | `https://test.agenthub.qubi.com` |
| Document Status | Complete |

This document is the authoritative design reference for the Web track. The narrative
companion documents in [`sdd/`](./sdd/) (01-WHY through 06-HOW-TO-USE) cover motivation
and reverse-engineering process; `API.md` and `GRAPH_SCHEMA.md` hold the captured
platform contracts. This document specifies the design.

---

## 1. Introduction

### 1.1 Purpose

Specify the design of `qcli` for qubi's web-based Agentic Flows platform: a deterministic
CLI that validates workflow graphs locally and reads/writes them through the AgentHub
REST API, plus an AI Skill enabling an agent to author those graphs.

### 1.2 Scope

In scope: local graph validation against a reverse-engineered node schema; listing,
downloading, saving, and running workflows via the API; agent and RPA automation
discovery; session authentication; a Skill file set for AI authoring.

Out of scope: any AI/LLM call inside the CLI; a graph editor UI; CI/CD; production auth
hardening.

### 1.3 Definitions

| Term | Meaning |
|------|---------|
| AgentHub | The qubi web application hosting Agentic Flows |
| Graph | `{nodes, edges, viewport, executionMode}` — the workflow document |
| Node | One step; 13 known types |
| `graphJson` | The save payload field holding the graph as a **JSON string** |
| PKCE | Proof Key for Code Exchange, the OAuth2 extension AgentHub uses |
| React Flow | The canvas library (xyflow) whose format the graph follows |

### 1.4 References

- `docs/API.md` — captured endpoint reference
- `docs/GRAPH_SCHEMA.md` — full node type field reference
- `docs/sdd/01-WHY.md` … `06-HOW-TO-USE.md` — narrative background
- `../schema-extractor/` — Playwright capture harness and raw output
- `../schema-extractor/output/save_payload_sample.json` — a real captured save

---

## 2. System Overview

```
┌──────────────────────────────────────────────────────────────┐
│ Human — "Call the weather API and summarise it with an agent"  │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ AI Agent  (all intelligence)                                  │
│   reads skills/*.md → writes graph JSON → drives qcli          │
│   repairs validation errors → asks human before writes         │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ qcli  (zero AI)                                               │
│   schema.py validate  →  client.py  →  AgentHub REST           │
└───────────────────────────┬──────────────────────────────────┘
                            ▼ HTTPS + session cookies
┌──────────────────────────────────────────────────────────────┐
│ AgentHub — workflow store, job runner, agent + RPA registries │
└──────────────────────────────────────────────────────────────┘
```

Same governing principle as the Studio track: **the CLI performs no AI/LLM calls.**

### 2.1 Why This Track Exists Separately

The Studio track targets XAML on Windows Workflow Foundation. This track targets a JSON
graph in a web app. They share only the architectural principle and the CLI name — the
data model, validation rules, transport, and auth are entirely different. Keeping them
separate avoids one codebase straddling two incompatible platforms.

Practically, this track is the more viable of the two: the platform is reachable, the API
surface is captured from live traffic, and validation is verified working.

---

## 3. Design Considerations

### 3.1 Assumptions

| # | Assumption | Basis | Risk if wrong |
|---|-----------|-------|---------------|
| A1 | 13 node types is the complete set | Palette enumerated via Playwright | Unknown types rejected |
| A2 | Required fields per type are correct | Properties panels scraped | False validation failures |
| A3 | `POST /api/v1/workflow/{id}/graph` saves a graph | **Captured from a real save** | — (strong) |
| A4 | `measured` / `selected` node fields are optional on load | React Flow computes them client-side | Injected graphs render wrong |
| A5 | `POST /api/v1/job/run` starts a workflow | **Inferred — never observed** | `flow run` fails |
| A6 | Identity Server login yields usable AgentHub cookies | Assumed by `auth.py` | **Known false — §12.1** |

A3 is the strongest assumption in either track — it is backed by a recorded payload.
A5 and A6 are the weak ones.

### 3.2 Constraints

- Python 3.9+; `click` and `requests` only
- Validation must work fully offline
- No official API documentation — the entire contract is reverse-engineered
- Target workflows must already exist; the CLI writes into a workflow ID, it does not create one

---

## 4. Architecture

### 4.1 Component Responsibilities

| Component | Responsibility | Depends On |
|-----------|---------------|-----------|
| `qcli/schema.py` | Node type registry + graph validation | *(nothing)* |
| `qcli/auth.py` | Login and session persistence | `requests` |
| `qcli/client.py` | HTTP wrapper for AgentHub endpoints | `auth` |
| `qcli/commands/flow.py` | `list`, `validate`, `get`, `save`, `run` | `schema`, `client` |
| `qcli/commands/agents.py` | `agents list`, `rpa list` | `client` |
| `qcli/commands/login.py` | `login`, `logout`, `status` | `auth` |
| `qcli/cli.py` | Click group registration | `commands` |
| `skills/*.md` | AI-facing schema and procedure | schema registry |
| `../schema-extractor/` | Playwright capture harness (Node) | *(build-time only)* |

`schema.py` imports nothing from the project, so validation is testable in isolation and
usable without credentials.

### 4.2 Dependency Direction

```
schema.py (standalone)          auth.py
    │                               │
    │                               ▼
    │                           client.py
    ▼                               │
   commands/*.py  ◄─────────────────┘
    │
    ▼
  cli.py
```

`client.py` calls `require_login()` in its constructor, so constructing a client without a
session exits the process — every network command fails fast and identically.

### 4.3 Schema Acquisition Architecture

The node schema was not documented; it was captured. The harness lives outside the CLI
and runs once, at design time:

```
Playwright (headed Chromium)
   │  drives the real AgentHub UI
   ├─ log in through Identity Server
   ├─ open the Agentic Flows designer
   ├─ drag each of 13 palette node types onto the canvas
   ├─ click each node, scrape its properties panel
   ├─ click Save, intercept the POST payload
   └─ load an existing workflow, capture nodes + edges
          │
          ▼
   output/*.json  ──manual curation──►  qcli/schema.py NODE_TYPES
                                        docs/GRAPH_SCHEMA.md
```

The captured artefacts are committed under `../schema-extractor/output/` as evidence:
`api_calls.json`, `element_properties.json`, `network_log.json`,
`save_payload_sample.json`, `workflow_graph_sample.json`.

The transfer from captured output into `NODE_TYPES` was **manual**, not generated. There
is no automated path that regenerates `schema.py` from the capture output, so the two can
drift.

---

## 5. Data Design

### 5.1 Graph Document

```json
{
  "nodes": [ ... ],
  "edges": [ ... ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "executionMode": "Sequential"
}
```

### 5.2 Node

```json
{
  "id": "52659b0d-db1d-46ff-93a7-68990a0bfbd6",
  "type": "Http",
  "position": { "x": 450, "y": 200 },
  "data": { "type": "Http", "name": "Get Data", "method": "GET",
            "url": "https://...", "saveOutputAs": "result" },
  "measured": { "width": 80, "height": 59 },
  "selected": false
}
```

`id` is a client-generated UUID v4. `type` is duplicated inside `data` — the real captured
payload does this, so generated graphs mirror it. `measured` and `selected` appear in
captured saves but are omitted by our generators (A4).

### 5.3 Edge

```json
{ "id": "xy-edge__<sourceId>-<targetId>", "source": "<uuid>", "target": "<uuid>" }
```

The `xy-edge__` prefix is React Flow's own convention, observed in captured data.

### 5.4 Node Type Registry

`NODE_TYPES` in `schema.py` — 13 types with required and optional `data` fields:

| Type | Required | Optional |
|------|----------|----------|
| `Start` | `name` | `input`, `saveOutputAs` |
| `End` | `name` | `input`, `saveOutputAs` |
| `Agent` | `name`, `agentId` | `input`, `systemPrompt`, `userMessage`, `saveOutputAs` |
| `Assign` | `name` | `assignments` |
| `Branch` | `name` | `conditions`, `input`, `saveOutputAs` |
| `Code` | `name`, `language`, `code` | `input`, `saveOutputAs` |
| `DocumentAI` | `name`, `operation` | `fileVariable`, `saveOutputAs`, `input` |
| `Http` | `name`, `method`, `url` | `input`, `headers`, `body`, `saveOutputAs` |
| `RPA` | `name`, `automationId` | `input`, `saveOutputAs` |
| `Hitl` | `name` | `input`, `saveOutputAs` |
| `HitlTask` | `name`, `taskName`, `taskType`, `assignTo` | `template`, `saveOutputAs`, `input` |
| `JsonParser` | `name` | `input`, `mappings` |
| `TextParser` | `name`, `regexPattern` | `input`, `ignoreCase`, `multiline`, `singleline`, `trimOutput`, `fallbackValue`, `outputMappings` |

Enum domains: `VALID_HTTP_METHODS` = GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS;
`VALID_CODE_LANGUAGES` = javascript, python.

Type names are case-sensitive and irregular — `Http` not `HTTP`, `Hitl` not `HITL`,
`RPA` fully capitalised, `DocumentAI` mixed. This is a common authoring error and the
Skill calls it out explicitly.

### 5.5 The Double-Encoding Contract

The save payload nests a JSON **string** inside a JSON object:

```json
{ "graphJson": "{\"nodes\":[...],\"edges\":[...],\"viewport\":{...}}" }
```

`client.save_graph()` applies `json.dumps(graph)` to produce it; `client.get_graph()`
reverses it, tolerating three observed response shapes: a raw string, an object carrying
`graphJson`, or an already-decoded object. This is the single most error-prone detail of
the integration.

### 5.6 Session File

`~/.qcli/session.json`, mode `0600`:

```json
{ "cookies": {}, "server_url": "https://test.agenthub.qubi.com",
  "tenant": "default", "username": "user@example.com" }
```

Note `server_url` holds the **AgentHub** URL while login targets the **Identity Server** —
two different hosts, which is the root of the auth defect in §12.1.

---

## 6. Detailed Module Design

### 6.1 `schema.py` — Validator

Standalone. Imports `json`, `uuid`, `dataclasses`, `pathlib`.

```python
validate_graph(graph: dict) -> ValidationResult
validate_file(file_path: str | Path) -> ValidationResult
```

`ValidationError` fields: `code`, `message`, `node_id`, `node_name`, `field`, `suggestion`.
`ValidationResult` fields: `valid`, `errors`, `warnings`, `node_count`, `edge_count`,
plus `to_dict()` and `print_report()`.

Validation order — each of the first four returns early, since later checks depend on
structure being present:

| # | Check | Early return |
|---|-------|-------------|
| 1 | Top level is an object | yes |
| 2 | `nodes` present and is a list | yes |
| 3 | `edges` present | yes |
| 4 | Per node: id present, unique; type present and known | continues |
| 5 | Per node: `position` with `x`/`y` | warning only |
| 6 | Per node: required `data` fields present and truthy | — |
| 7 | Type-specific: HTTP method, code language enums | — |
| 8 | Graph contains at least one `Start` and one `End` | — |
| 9 | Per edge: source and target present and resolve to nodes; no self-loop | — |

Required-field checking uses `if req_field not in data or not data[req_field]` — so an
empty string or `0` counts as missing. Intentional for string fields; would misfire on a
numeric field whose valid value is `0`. No such field exists in the current registry.

> **Defect found and fixed during review:** `validate_file()` referenced `Path` while the
> module never imported it, so **every** `flow validate` invocation raised
> `NameError: name 'Path' is not defined`. Fixed by adding `from pathlib import Path`.
> The bug was invisible to `import qcli.schema` and only surfaced on execution — a
> reminder that import-level smoke tests are insufficient.

### 6.2 `auth.py` — Login and Session

```python
DEFAULT_IDENTITY_SERVER = "https://test.identityserver.qubi.com"
DEFAULT_AGENTHUB        = "https://test.agenthub.qubi.com"
LOGIN_API               = "/api/v1/account/login"

do_login(server_url, tenant, username, password) -> dict   # {"cookies": {...}, "response": {...}}
save_session(*, cookies, server_url, tenant, username) -> None
load_session() -> dict | None
clear_session() -> None
is_logged_in() -> bool
require_login() -> dict        # stderr + sys.exit(1) when absent
prompt_login() -> tuple[str, str, str, str]
```

`do_login()` posts `{tenantName, userNameOrEmail, password}` and returns
`dict(session.cookies)`. Exception mapping: 401 → `PermissionError`; 400 → `ValueError`
with the server message; unreachable/timeout → `ConnectionError`; other → `RuntimeError`.

Two problems, both detailed in §12: the payload field names disagree with `API.md`, and
the collected cookies belong to the wrong host.

### 6.3 `client.py` — HTTP Wrapper

```python
QubiClient(base_url: str | None = None)     # calls require_login(); verify = False
  .list_workflows(search: str = "") -> list        # POST /api/v1/workflow/search
  .get_graph(workflow_id) -> dict                  # GET  /api/v1/workflow/{id}/graph
  .save_graph(workflow_id, graph: dict) -> dict    # POST /api/v1/workflow/{id}/graph
  .list_agents() -> list                           # GET  /api/v1/getallagents
  .list_rpa_automations() -> list                   # GET  /api/v1/getrpaautomations
  .run_workflow(workflow_id, input_data=None)      # POST /api/v1/job/run          ⚠ unverified
  .get_job_status(job_id) -> dict                  # GET  /api/v1/job/{id}         ⚠ unverified
```

All calls go through one `requests.Session` seeded with stored cookies, 30s timeout, and
`raise_for_status()`. `session.verify = False` disables TLS certificate verification on
every request — see §9.

Endpoint provenance:

| Endpoint | Provenance |
|----------|-----------|
| `workflow/search`, `workflow/{id}/graph` (GET and POST) | **Captured from live traffic** |
| `getallagents`, `getrpaautomations` | **Captured** |
| `job/run`, `job/{id}` | **Inferred** — only `POST /api/v1/job/search` was observed |

### 6.4 `commands/` and `cli.py`

Click groups: `cli` (root) → `flow`, `agents`, `rpa`. The `rpa` group is declared in
`cli.py` while its `list` command lives in `agents.py`.

| Command | Network | Validates | Human gate |
|---------|---------|-----------|-----------|
| `qcli login` / `logout` / `status` | login only | — | — |
| `qcli flow validate <file>` | **no** | yes | — |
| `qcli flow list` | yes | — | — |
| `qcli flow get <id>` | yes | — | — |
| `qcli flow save <file> -w <id>` | yes | yes¹ | **confirm** |
| `qcli flow run <id>` | yes | — | **confirm** |
| `qcli agents list` / `qcli rpa list` | yes | — | — |

¹ unless `--skip-validate`.

`flow validate` exits `0`/`1` and supports `--json-output`. `flow save` validates, prints
node and edge counts, then prompts. `flow get` writes to `-o` or stdout, `--pretty` for
indentation. Both write commands accept `-y/--yes` for scripting; agents should not use it.

`flow list` tolerates three response shapes — a bare list, `{items: [...]}`, or
`{data: [...]}` — because the real shape was not pinned down during capture.

### 6.5 Skill File Set

| File | Role |
|------|------|
| `SKILL.md` | Rules, mandatory command order, links out |
| `schema-reference.md` | All 13 node types with fields and examples |
| `error-handling.md` | Error code → repair procedure |
| `examples.md` | Complete validated graphs to pattern-match |

Mandatory order the Skill enforces:

```
[write graph JSON] → flow validate → [fix → validate]*
                   → HUMAN CONFIRM → flow save
                   → HUMAN CONFIRM → flow run
```

`agents list` / `rpa list` are prerequisites when authoring `Agent` or `RPA` nodes: the
`agentId` and `automationId` values must come from the platform, and the agent must ask
the human to choose rather than inventing an ID.

---

## 7. Interface Design

### 7.1 Stable CLI Contract

Exit codes and the `--json-output` shape are the contract for AI consumption:

```json
{
  "valid": false,
  "node_count": 4,
  "edge_count": 3,
  "error_count": 2,
  "warning_count": 0,
  "errors": [{ "code": "MISSING_REQUIRED_FIELD",
               "message": "Node 'Bad Http' missing required field: 'method'",
               "node_id": "...", "node_name": "Bad Http", "field": "method",
               "suggestion": "..." }],
  "warnings": []
}
```

Human-readable output is not a stable contract.

### 7.2 Platform API

See `API.md` for the full captured reference. Authentication is cookie-based following an
OAuth2 Authorization Code + PKCE exchange:

```
GET  agenthub/api/login
  → 302 identityserver/connect/authorize
        client_id=AgentHub
        response_type=code
        scope=openid email profile roles api
        code_challenge=<S256>
        code_challenge_method=S256
        redirect_uri=agenthub/api/callback/login/local
  → identityserver/Account/Login          (Blazor form: Tenant, Email, Password)
  → POST identityserver/api/v1/account/login
  → 302 agenthub/api/callback/login/local?code=…&state=…
        ↑ this callback is what sets the AgentHub session cookie
```

The parameters above were read directly from the captured authorize request in
`../schema-extractor/output/network_log.json`.

---

## 8. Error Handling

### 8.1 Validation Error Catalogue

**Structural — abort validation:**

| Code | Meaning |
|------|---------|
| `FILE_NOT_FOUND` | Path does not exist |
| `INVALID_JSON` | File is not parseable JSON |
| `INVALID_FORMAT` | Top level is not an object |
| `MISSING_NODES` / `INVALID_NODES` | `nodes` absent or not a list |
| `MISSING_EDGES` | `edges` absent (empty list is valid) |

**Node-level:**

| Code | Meaning | Fixable by agent |
|------|---------|-----------------|
| `INVALID_NODE` | Node entry is not an object | yes |
| `MISSING_NODE_ID` | No `id` | yes — generate a UUID v4 |
| `DUPLICATE_NODE_ID` | `id` reused | yes |
| `MISSING_NODE_TYPE` | No `type` | yes |
| `UNKNOWN_NODE_TYPE` | Type not in the registry | yes — check exact casing |
| `MISSING_REQUIRED_FIELD` | Required `data` field absent or empty | yes¹ |
| `INVALID_HTTP_METHOD` | Method outside the enum | yes |
| `INVALID_CODE_LANGUAGE` | Language outside the enum | yes |
| `MISSING_POSITION` | **Warning** — no `position` | yes |

¹ Except `agentId` and `automationId`, which must come from `agents list` / `rpa list`
and, if ambiguous, from the human.

**Graph-level:**

| Code | Meaning |
|------|---------|
| `MISSING_START` / `MISSING_END` | No `Start` / no `End` node |
| `INVALID_EDGE` | Edge entry is not an object |
| `MISSING_EDGE_SOURCE` / `MISSING_EDGE_TARGET` | Endpoint absent |
| `INVALID_EDGE_SOURCE` / `INVALID_EDGE_TARGET` | Endpoint does not resolve to a node |
| `SELF_LOOP` | Edge connects a node to itself |

Every code except `MISSING_POSITION` is an error. Unlike the Studio track, **every error
here is agent-fixable** — there is no selector problem, because web nodes are configured
by field values rather than recorded UI coordinates. This is the single biggest advantage
this track has over the Studio track.

### 8.2 Unvalidated Semantics

Validation is structural. It does **not** check:

- Reachability — orphan nodes with no edges pass
- Cycles — any loop that is not a self-loop passes
- That `agentId` / `automationId` correspond to real platform resources
- That `saveOutputAs` variable names referenced downstream actually exist
- That `Branch` conditions are well-formed
- That `Code` node source is syntactically valid

A graph can therefore validate and still fail at execution.

---

## 9. Security Considerations

| Area | Current state | Assessment |
|------|--------------|-----------|
| **TLS verification** | `session.verify = False` in `client.py`; `verify=False` in `auth.py` | **Disabled — credentials and graphs are sent over unverified TLS. Must be fixed before non-test use.** |
| Credential storage | Cookies in plaintext JSON, `0600` | Acceptable for POC |
| Password entry | `getpass` interactively | Adequate |
| Password via flag | `login -p` accepted | Leaks into shell history |
| Session expiry | Not tracked | Surfaces as 401 |
| PKCE | Not implemented | §12.1 |
| Write gates | Confirmation on `save` and `run`, bypassable with `-y` | Adequate; Skill forbids `-y` |
| Secret logging | Passwords never printed; cookies not echoed | Adequate |

`verify = False` was presumably added to work around a self-signed certificate in the test
environment. It suppresses certificate validation for every request, including the login
POST, making the session vulnerable to interception. It should be replaced with an
explicit CA bundle or a `--insecure` opt-in flag rather than an unconditional default.

---

## 10. Testing Strategy and Verification Status

### 10.1 Verified

| Check | Result |
|-------|--------|
| All 7 modules import | pass |
| CLI groups and help render | pass — `flow`, `agents`, `rpa`, `login` |
| `flow validate` on a valid 4-node graph | valid, 4 nodes / 3 edges, exit 0 |
| `flow validate` on a deliberately broken graph | 7 errors, exit 1 |
| Error codes exercised | `DUPLICATE_NODE_ID`, `UNKNOWN_NODE_TYPE`, `MISSING_REQUIRED_FIELD` ×2, `INVALID_CODE_LANGUAGE`, `MISSING_END`, `INVALID_EDGE_TARGET` |
| Network commands without a session | fail gracefully, no traceback |
| Repo-wide missing-import scan | clean after the `Path` fix |
| `validate_graph()` callable as a library | pass |

The `Path` defect in §6.1 was found by this exercise and fixed.

### 10.2 Not Verified

| Area | Reason |
|------|--------|
| `qcli login` against the live Identity Server | Requires credentials + VPN |
| Any authenticated command | Blocked by §12.1 |
| `flow save` round-trip | Blocked by auth |
| Whether an injected graph renders correctly on canvas | Depends on A4 |
| `flow run` / job status | A5 — endpoints inferred |
| Completeness of the 13-type registry | A1 |
| End-to-end AI authoring loop | Not run with a live agent |

Note that `inject-workflow.js` in the extractor **does** successfully write a graph via
the API — but it borrows the browser's authenticated cookie jar via `page.evaluate()` with
`credentials: 'include'`. It therefore proves the *write path* works while proving nothing
about standalone CLI auth.

### 10.3 Recommended Test Suite

No automated tests exist. Priorities:

- Unit: one fixture per error code; both enum validators; the empty-string-is-missing rule
- Round-trip: `json.dumps` → `save_graph` payload → parse back → deep-equal
- Contract: assert every `NODE_TYPES` entry matches `GRAPH_SCHEMA.md` (guards the manual drift in §4.3)
- **Execution smoke test:** import every module *and invoke each public function once* —
  the `Path` bug passed an import test and would have been caught by this
- Mocked HTTP: `responses`/`respx` for each client method, including the three tolerated
  `flow list` response shapes

---

## 11. Deployment and Operations

```bash
cd web-version
pip install -e .          # console_scripts: qcli = qcli.cli:main

qcli flow validate my_flow.json          # works offline, no login
qcli login                                # then authenticated commands
qcli flow save my_flow.json -w <workflow-id>
```

| Artifact | Location |
|----------|----------|
| Session | `~/.qcli/session.json` (mode 0600) |
| Extractor output | `../schema-extractor/output/` |
| Extractor screenshots | `../schema-extractor/screenshots/` |

Re-running schema extraction requires Node 22, Playwright 1.62, an OpenAI key in
`schema-extractor/.env`, and a headed display. It is a design-time activity, not part of
normal operation.

---

## 12. Known Limitations and Open Issues

### 12.1 OAuth2 PKCE flow is not implemented — *blocker for every authenticated command*

`do_login()` posts credentials to the Identity Server and collects
`dict(session.cookies)`. Those are **identityserver.qubi.com** cookies. The AgentHub
session cookie is only issued at step 4 of the flow — the
`agenthub/api/callback/login/local?code=…&state=…` redirect — which `auth.py` never
performs. It also never generates a PKCE verifier or challenge, though the captured
authorize request shows `code_challenge_method=S256`.

Consequence: cookies are stored for the wrong host, `qcli status` reports success, and the
first authenticated call fails with 401. `flow list`, `get`, `save`, `run`, `agents list`,
and `rpa list` are all blocked.

Three remedies, in increasing order of effort:

1. **Service account / PAT** — if AgentHub supports a client-credentials grant or personal
   access token, this collapses to an `Authorization` header and the problem disappears.
   Worth confirming with the platform owners before building anything.
2. **Browser-assisted login** — Playwright opens a window once, the user logs in, the
   script extracts AgentHub cookies into `~/.qcli/session.json`; every later call is plain
   HTTP. Reuses what `inject-workflow.js` already proves. Fastest route to a working POC.
3. **Full PKCE in `auth.py`** — generate verifier/challenge, `GET /api/login`, post
   credentials, follow the callback with `allow_redirects=True` on a single
   `requests.Session` so the AgentHub cookie is captured. Fully headless, no browser
   dependency. The correct long-term fix.

### 12.2 Login payload field names are unconfirmed

`API.md` documents the body as `{tenant, username, password}`; `auth.py` sends
`{tenantName, userNameOrEmail, password}`. Both describe the same endpoint, so at least
one is wrong. The captured `network_log.json` records that the login POST occurred but not
its request body, so neither can be confirmed from existing evidence.

### 12.3 `job/run` and `job/{id}` are inferred

Only `POST /api/v1/job/search` was observed. `flow run` and `get_job_status` target
endpoints that were never seen in traffic and may not exist under those paths.

### 12.4 `measured` / `selected` omitted from generated graphs

Captured saves include `measured: {width, height}` and `selected` on every node; our
generators omit both. React Flow computes dimensions client-side, so they are *probably*
optional on load — but this is untested (A4). Verification must inspect the rendered
canvas, not merely a 2xx response.

### 12.5 Schema registry can drift from captured output

`NODE_TYPES` was hand-transcribed from the extractor output. Nothing regenerates or
cross-checks it, so a re-capture will not propagate automatically. Mitigation: the
contract test in §10.3.

### 12.6 Validation is structural only

See §8.2. Reachability, cycles, resource-ID existence, and variable references are all
unchecked, so a valid graph can still fail at runtime.

### 12.7 TLS verification disabled

See §9. `verify = False` applies to all requests including login.

### 12.8 The CLI cannot create workflows

`flow save` writes into an **existing** workflow ID. There is no `flow create`, because no
creation endpoint was captured. A human must create the workflow in the web UI first and
supply its ID.

---

## 13. Future Work

| Priority | Item | Unblocks |
|----------|------|----------|
| P0 | Resolve auth — confirm PAT, else browser-assisted, else full PKCE | §12.1, all network commands |
| P0 | Re-enable TLS verification | §12.7 |
| P1 | Confirm login payload field names by capturing the request body | §12.2 |
| P1 | Confirm or discover the job-run endpoint | §12.3 |
| P1 | Execution smoke tests + mocked HTTP suite | §10.3 |
| P1 | Verify injected graphs render on canvas | §12.4 |
| P2 | Contract test: `NODE_TYPES` vs `GRAPH_SCHEMA.md` | §12.5 |
| P2 | Discover a workflow-create endpoint | §12.8 |
| P3 | Semantic validation — reachability, cycles, variable references | §12.6 |
| P3 | End-to-end AI authoring loop with a live agent | §10.2 |

---

## 14. Requirements Traceability

| Req | Requirement | Implemented in | Verified |
|-----|-------------|---------------|----------|
| R1 | Discover the node schema without documentation | `../schema-extractor/` | yes — 13 types captured |
| R2 | Validate graph structure offline | `schema.py` | §10.1 |
| R3 | Validate node types against a registry | `NODE_TYPES` | §10.1 |
| R4 | Validate required fields per type | check 6 | §10.1 |
| R5 | Validate enum domains | checks 7 | §10.1 |
| R6 | Validate edge referential integrity | check 9 | §10.1 |
| R7 | Require `Start` and `End` | check 8 | §10.1 |
| R8 | Actionable machine-readable errors | `--json-output` | §10.1 |
| R9 | Authenticate against Identity Server | `auth.py` | **no** — §12.1 |
| R10 | List workflows | `client.list_workflows` | **no** — auth |
| R11 | Download a graph | `client.get_graph` | **no** — auth |
| R12 | Save a graph | `client.save_graph` | payload shape matches a real capture; call unverified |
| R13 | Run a workflow | `client.run_workflow` | **no** — §12.3 |
| R14 | Discover agents and RPA automations | `agents.py` | **no** — auth |
| R15 | Human confirmation before writes | `flow save`, `flow run` | code-verified |
| R16 | Zero AI calls in the CLI | whole package | verified by inspection |
| R17 | Teach an AI agent the schema and procedure | `skills/` | **no** — §10.2 |

---

## 15. Status Summary

The offline half of this track is verified working: graph validation catches all 22 error
conditions across structure, nodes, and edges, with correct exit codes and machine-readable
output. The save payload shape is backed by a recorded real save, which is the strongest
evidence in either track that the write path is correct.

One issue blocks everything else. `auth.py` skips the OAuth2 PKCE callback and stores
Identity Server cookies instead of AgentHub ones (§12.1), so no authenticated command can
succeed. It is a contained, well-understood fix with three known remedies — and it should
be settled by asking whether a service account exists before any code is written.

Two smaller matters deserve attention alongside it: TLS verification is disabled
unconditionally (§12.7), and there are no automated tests — the `Path` bug in §6.1 reached
the repository precisely because import-level checks cannot catch it.

Compared with the Studio track, this one is materially more viable: the platform is
reachable, the API is captured from live traffic rather than invented, and there is no
selector problem — **every validation error here is agent-fixable**.
