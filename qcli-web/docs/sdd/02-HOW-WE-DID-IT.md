# How We Did It (Web Version)

## Phase 1: Schema Discovery

We had no API documentation. The web designer is a closed Next.js app. So we reverse-engineered it.

### Tools Used
- **Playwright** (Node.js) — browser automation to drive the real UI
- **GPT-4o** (text model) — intelligent DOM navigation when selectors were unpredictable
- **Network interception** — captured every API request/response

### Process

1. Wrote a Playwright script that opens the real qubi web app
2. Logged in via the Identity Server (Blazor app with OAuth2)
3. Navigated to the Agentic Flows designer
4. Opened the node palette and dragged each of the 13 node types onto the canvas
5. Clicked each placed node to open its properties panel
6. Extracted all form fields (labels, types, placeholders)
7. Clicked Save and intercepted the POST request to capture the exact payload format
8. Opened an existing workflow to capture how a real connected workflow looks (nodes + edges)

### Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| Identity Server is Blazor (SignalR never goes idle) | Used `domcontentloaded` instead of `networkidle` |
| Login has Tenant + Username + Password (3 fields) | Added tenant to the automation |
| Hardcoded selectors break on dynamic SPAs | Used GPT-4o to read DOM and decide what to click |
| Palette items not found by GPT (too deep in DOM) | Deep DOM scan + direct text-based clicking |
| Properties panel only showing global "Auto Save" toggle | Fixed coordinate threshold + proper node selection after drag |
| Page overflowing viewport | Set `viewport: null` to use actual screen size |

## Phase 2: CLI Development

With the schema captured, we built the Python CLI:

1. `auth.py` — Handles the OAuth2 login flow against Identity Server
2. `client.py` — HTTP wrapper for all discovered API endpoints
3. `schema.py` — Local validation engine (no server needed)
4. `cli.py` + `commands/` — Click-based command structure

## Phase 3: AI Skill Authoring

Wrote skill files teaching AI agents:
- All 13 node types with exact field names and types
- The mandatory validate → confirm → save sequence
- How to interpret and fix every validation error
- Complete working examples to pattern-match from

## Phase 4: Integration Test

Confirmed the full loop works:
- AI generates workflow JSON
- `qcli flow validate` passes
- `qcli flow save` pushes to qubi
- Workflow appears on the web designer canvas
