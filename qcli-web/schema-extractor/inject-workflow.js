/**
 * Inject a workflow into qubi via API
 * 
 * Opens browser for you to log in, captures the auth token,
 * then injects a workflow graph directly via the API.
 * 
 * Usage:
 *   node inject-workflow.js
 *   → Log in manually
 *   → Press Enter
 *   → Script injects the workflow into an existing workflow ID
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

require('dotenv').config({ path: path.join(__dirname, '.env') });

const OUTPUT_DIR = path.join(__dirname, 'output');

function waitForEnter(prompt) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise(resolve => {
    rl.question(prompt, () => { rl.close(); resolve(); });
  });
}

function waitForInput(prompt) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise(resolve => {
    rl.question(prompt, (answer) => { rl.close(); resolve(answer.trim()); });
  });
}

// ---------------------------------------------------------------------------
// The workflow to inject — Start → HTTP (GET httpbin) → End
// ---------------------------------------------------------------------------

function buildTestWorkflow() {
  const startId = crypto.randomUUID();
  const httpId = crypto.randomUUID();
  const endId = crypto.randomUUID();

  return {
    nodes: [
      {
        id: startId,
        type: 'Start',
        position: { x: 250, y: 200 },
        data: { type: 'Start', name: 'Start' },
      },
      {
        id: httpId,
        type: 'Http',
        position: { x: 450, y: 200 },
        data: {
          type: 'Http',
          name: 'Get Httpbin',
          input: { source: 'payload', sessionVarName: '', literalValue: '' },
          method: 'GET',
          url: 'https://httpbin.org/get',
          saveOutputAs: 'httpResult',
        },
      },
      {
        id: endId,
        type: 'End',
        position: { x: 700, y: 200 },
        data: { type: 'End', name: 'End' },
      },
    ],
    edges: [
      {
        source: startId,
        target: httpId,
        id: `xy-edge__${startId}-${httpId}`,
      },
      {
        source: httpId,
        target: endId,
        id: `xy-edge__${httpId}-${endId}`,
      },
    ],
    viewport: { x: 0, y: 0, zoom: 1 },
    executionMode: 'Sequential',
  };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

(async () => {
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║  Inject Workflow via API                                     ║');
  console.log('╠══════════════════════════════════════════════════════════════╣');
  console.log('║  1. Browser opens → you log in                              ║');
  console.log('║  2. Navigate to any workflow (or create one)                 ║');
  console.log('║  3. Press Enter → script injects a test flow via API        ║');
  console.log('║  4. Refresh the page to see it on canvas                    ║');
  console.log('╚══════════════════════════════════════════════════════════════╝\n');

  let authToken = null;
  let cookies = null;

  const browser = await chromium.launch({
    headless: false,
    slowMo: 50,
    args: ['--start-maximized'],
  });

  const context = await browser.newContext({
    viewport: null,
    ignoreHTTPSErrors: true,
  });

  const page = await context.newPage();

  // Capture auth token from API calls
  page.on('request', (request) => {
    const authHeader = request.headers()['authorization'];
    if (authHeader && authHeader.startsWith('Bearer ')) {
      authToken = authHeader;
    }
    // Also grab from cookie-based auth
    const cookie = request.headers()['cookie'];
    if (cookie && !cookies) {
      cookies = cookie;
    }
  });

  await page.goto('https://test.agenthub.qubi.com/login', { waitUntil: 'domcontentloaded', timeout: 60000 });

  console.log('  Browser is open.\n');
  console.log('  1. Log in');
  console.log('  2. Open the workflow you want to inject into');
  console.log('     (The workflow ID is in the URL: /workflows/{ID}/designer)');
  console.log('');
  await waitForEnter('  >> Press Enter when you are on the workflow designer page: ');

  // Get the workflow ID from the current URL
  const currentUrl = page.url();
  const workflowIdMatch = currentUrl.match(/workflows\/([a-f0-9-]+)/i);
  let workflowId = workflowIdMatch ? workflowIdMatch[1] : null;

  if (!workflowId) {
    workflowId = await waitForInput('  Could not detect workflow ID from URL.\n  Paste the workflow ID: ');
  }

  console.log(`\n  Workflow ID: ${workflowId}`);
  console.log(`  Auth token: ${authToken ? 'captured ✓' : 'not found (will use cookies)'}`);

  // Build the workflow
  const workflow = buildTestWorkflow();
  const graphJson = JSON.stringify(workflow);
  const payload = { graphJson };

  console.log(`\n  Injecting workflow: Start → HTTP (GET httpbin.org/get) → End`);
  console.log(`  Payload size: ${JSON.stringify(payload).length} bytes`);

  // Make the API call using the page's context (cookies/auth already set)
  const apiUrl = `https://test.agenthub.qubi.com/api/v1/workflow/${workflowId}/graph`;
  
  const response = await page.evaluate(async ({ url, body, token }) => {
    const headers = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = token;
    }

    const res = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      credentials: 'include',
    });

    return {
      status: res.status,
      statusText: res.statusText,
      body: await res.text(),
    };
  }, { url: apiUrl, body: payload, token: authToken });

  console.log(`\n  Response: ${response.status} ${response.statusText}`);
  if (response.body) {
    console.log(`  Body: ${response.body.slice(0, 200)}`);
  }

  if (response.status >= 200 && response.status < 300) {
    console.log('\n  ✓ Workflow injected successfully!');
    console.log('  Refresh the page in the browser to see it on the canvas.');
  } else {
    console.log('\n  ✗ Injection failed.');
    console.log('  Response:', response.body);
  }

  // Save what we sent for reference
  const outPath = path.join(OUTPUT_DIR, 'injected_workflow.json');
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify({
    workflowId,
    apiUrl,
    sentPayload: payload,
    graphParsed: workflow,
    response: { status: response.status, body: response.body },
  }, null, 2), 'utf-8');
  console.log(`  Saved to: ${outPath}`);

  await waitForEnter('\n  >> Press Enter to close browser: ');
  await browser.close();
})();
