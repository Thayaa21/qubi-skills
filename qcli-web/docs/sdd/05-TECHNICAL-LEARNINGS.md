# Technical Learnings (Web Version)

## 1. Blazor + SignalR Breaks Standard Waits

**Problem:** Playwright's `waitUntil: 'networkidle'` never resolves on the Identity Server because Blazor maintains a permanent SignalR WebSocket connection (`_blazor?id=...`) that continuously sends/receives messages.

**Solution:** Use `waitUntil: 'domcontentloaded'` then explicitly wait for specific form elements to appear.

**Lesson:** Any Blazor/.NET web app with SignalR will have this issue. Always use element-based waits, not network-based.

## 2. React Flow Graph Format

**Discovery:** The workflow designer uses React Flow (xyflow). The save format is:

```json
POST /api/v1/workflow/{id}/graph
{ "graphJson": "<stringified JSON>" }
```

The `graphJson` value is double-encoded — it's a JSON string inside a JSON body. When loading, the GET response returns the same string that needs to be parsed twice.

**Lesson:** Always check if API payloads have nested stringified JSON. It's common in .NET backends that store graph data as a serialized column.

## 3. OAuth2 Multi-Tenant Auth

**Discovery:** The login flow involves:
1. AgentHub redirects to Identity Server's authorize endpoint
2. Identity Server has a separate login form (Tenant + Username + Password)
3. After login, redirect back with auth code
4. AgentHub exchanges code for session

**Challenge for CLI:** We can't easily follow browser redirects. The workaround is to hit the Identity Server's login API directly, but cookie handling requires careful session management.

**Lesson:** Multi-tenant OAuth2 with a Blazor Identity Server is not standard. Each deployment may have its own quirks.

## 4. GPT-4o for DOM Navigation (Mixed Results)

**What worked:**
- Finding "Agentic Flows" link in the sidebar (returned correct MUI selector)
- Identifying button-like elements from text content

**What didn't work:**
- Finding palette items (DOM was too deep/complex for the 15k char context limit)
- Identifying canvas-rendered elements (React Flow nodes aren't in standard DOM)
- Login form (Blazor renders form elements asynchronously after hydration)

**Lesson:** GPT-4o text navigation is useful for simple/predictable UIs but breaks down with:
- Canvas-rendered content (WebGL, SVG, React Flow)
- Blazor apps (late hydration, no standard form elements initially)
- Very deep DOM trees that exceed context limits

**Better approach:** Deep DOM scanning with direct element matching (by text content) + coordinate-based clicking as fallback.

## 5. Drag-and-Drop in Playwright

**Working approach:**
```javascript
await page.mouse.move(sourceX, sourceY);
await sleep(300);
await page.mouse.down();
await sleep(300);
await page.mouse.move(targetX, targetY, { steps: 20 });
await sleep(300);
await page.mouse.up();
```

**Key:** The `{ steps: 20 }` parameter is critical — without intermediate steps, many drag-and-drop frameworks (React DnD, react-beautiful-dnd) don't register the drag.

**Lesson:** Always use stepped mouse movements for drag-and-drop. Single-point teleportation doesn't trigger drag events.

## 6. Viewport Size Matters

**Problem:** Setting viewport to 2560x1440 on a 1080p monitor causes the browser to render offscreen. The page appears as a tiny corner or white screen.

**Solution:** `viewport: null` with `--start-maximized` tells Playwright to use the actual window size.

**Lesson:** For headed (visible) browser automation, always match the viewport to the actual display resolution.

## 7. Properties Panel Detection

**Problem:** After dragging a node onto the canvas, clicking it should open the properties panel on the right. But the script was capturing global toolbar elements (like "Auto Save" toggle) instead of node-specific fields.

**Solution:** Filter by x-coordinate — only extract inputs on the right half of the screen (the properties panel area). Also filter out known global elements by label.

**Lesson:** In panel-based UIs, always use spatial filtering to distinguish which panel's content you're reading.

## 8. The Palette is Behind a Toggle

**Discovery:** The node palette (Start, End, Agent, etc.) is not always visible. It's behind a circular toggle button (blue +/- icon) in the top-left corner of the canvas.

**Lesson:** Always capture a screenshot before attempting element extraction. What you see in the browser may differ from what the DOM shows if panels are collapsed/hidden.

## 9. Session Conflicts

**Problem:** After Playwright logs in via the Identity Server, the user's existing browser session (in Brave/Chrome) becomes invalid — the page won't load properly.

**Cause:** The Identity Server likely only maintains one active session per user. Playwright's Chromium login invalidated the existing session.

**Solution:** Log out and back in from the regular browser. Or use a different test account for automation.

**Lesson:** Automated browser testing can invalidate concurrent sessions. Use dedicated test accounts.

## 10. API Surface Discovery via Network Tab

By simply navigating the app normally and capturing all `/api/` calls, we discovered the entire API surface without any documentation:

```
GET  /api/v1/getdashboarddata
POST /api/v1/workflow/search
GET  /api/v1/workflow/{id}/graph
POST /api/v1/workflow/{id}/graph
GET  /api/v1/getworkflowversionlist?workflowId=...
GET  /api/v1/getworkflowvariablelist?workflowId=...
GET  /api/v1/getallagents
GET  /api/v1/getrpaautomations
POST /api/v1/job/search
GET  /api/auth/token
```

**Lesson:** Network interception is the fastest way to reverse-engineer an undocumented API. Capture everything, filter later.
