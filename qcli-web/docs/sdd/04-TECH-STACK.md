# Tech Stack (Web Version)

## qcli CLI Tool

| Component | Technology | Why |
|-----------|-----------|-----|
| Language | Python 3.12 | Universal, easy to install, team knows it |
| CLI Framework | Click 8.x | Mature, subcommand routing, auto-help |
| HTTP Client | Requests 2.x | Standard Python HTTP library |
| Validation | Custom (schema.py) | No external deps needed for validation |
| Auth Storage | JSON file (~/.qcli/session.json) | Simple, no keychain complexity for POC |
| Package Format | pip installable (setup.py) | Standard Python distribution |

## qubi Web Platform (What We're Talking To)

| Component | Technology | How We Know |
|-----------|-----------|-------------|
| Frontend | Next.js (App Router, Turbopack) | `_next/static/chunks/turbopack-*.js` in network |
| Workflow Canvas | React Flow (xyflow) | "React Flow" watermark visible, node/edge format matches |
| UI Library | Material UI (MUI) | `MuiBox`, `mui-*` class names in DOM |
| Backend API | .NET (ASP.NET Core) | API patterns, Identity Server integration |
| Identity Server | Blazor (.NET) + MudBlazor | `_blazor`, `_framework/blazor.web.js`, MudBlazor CSS |
| Real-time | SignalR (WebSocket) | Persistent `_blazor?id=` connections |
| Auth Protocol | OAuth2 + PKCE | `code_challenge`, `response_type=code` in auth URLs |
| Icons | Material Symbols (Google Fonts) | Font requests in network |

## Schema Extraction Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Playwright | 1.62.0 | Browser automation to drive real UI |
| Node.js | 22.16.0 | Runtime for Playwright scripts |
| OpenAI (GPT-4o) | API | Intelligent DOM navigation |
| dotenv | 16.x | Environment variable loading |

## Development Environment

| Tool | Purpose |
|------|---------|
| Kiro IDE | Development environment (VS Code based) |
| Windows 11 | Target OS |
| PowerShell | Shell |
| Git | Version control |

## Key Technical Facts

- **No AI in the CLI** — qcli is 100% deterministic, zero LLM calls
- **All intelligence in the Skill** — AI agents read markdown files to learn the schema
- **Cookie-based auth** — not Bearer tokens (follows qubi's web session pattern)
- **Double-encoded JSON** — the save API expects `{ "graphJson": "<string>" }` where the string is JSON
- **UUID v4 for node IDs** — standard format, generated client-side
- **Edge ID pattern** — `xy-edge__{{sourceId}}-{{targetId}}`
