/**
 * Capture Existing Workflow — Just opens browser, you navigate, it captures.
 * 
 * This captures:
 *   1. The GET /api/v1/workflow/{id}/graph response (how a saved workflow looks)
 *   2. Any save/update requests you trigger
 * 
 * Usage:
 *   node capture-workflow.js
 *   → Browser opens
 *   → You log in, open an EXISTING workflow with connections
 *   → Press Enter
 *   → Script dumps the workflow graph JSON
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

(async () => {
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║  Capture Existing Workflow Graph                             ║');
  console.log('╠══════════════════════════════════════════════════════════════╣');
  console.log('║  1. Browser opens                                           ║');
  console.log('║  2. YOU: Log in → open an existing workflow with connections ║');
  console.log('║  3. Press Enter here                                        ║');
  console.log('║  4. Script captures the workflow graph                      ║');
  console.log('╚══════════════════════════════════════════════════════════════╝\n');

  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const capturedGraphs = [];
  const capturedSaves = [];
  const allApiCalls = [];

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

  // Capture all API responses
  page.on('response', async (response) => {
    const url = response.url();
    const method = response.request().method();
    
    if (!url.includes('/api/') || url.includes('_blazor')) return;

    allApiCalls.push({ method, url, status: response.status() });

    try {
      const ct = response.headers()['content-type'] || '';
      if (!ct.includes('json')) return;

      const body = await response.json();

      // Capture graph GET responses (loading a workflow)
      if (url.includes('/graph') && method === 'GET') {
        console.log(`\n  [CAPTURED] GET ${url}`);
        console.log(`    Response size: ${JSON.stringify(body).length} bytes`);
        capturedGraphs.push({
          url,
          method: 'GET',
          timestamp: new Date().toISOString(),
          data: body,
        });
      }

      // Capture graph POST/PUT responses (saving a workflow)
      if (url.includes('/graph') && (method === 'POST' || method === 'PUT')) {
        const postData = response.request().postData();
        console.log(`\n  [CAPTURED] ${method} ${url}`);
        console.log(`    Request body: ${postData?.length || 0} bytes`);
        capturedSaves.push({
          url,
          method,
          timestamp: new Date().toISOString(),
          requestBody: postData ? JSON.parse(postData) : null,
          responseBody: body,
        });
      }

      // Also capture workflow search results
      if (url.includes('workflow/search') && method === 'POST') {
        console.log(`  [API] Workflow list loaded (${JSON.stringify(body).length} bytes)`);
      }

    } catch (_) {}
  });

  // Also capture save request bodies
  page.on('request', (request) => {
    const url = request.url();
    const method = request.method();
    if ((method === 'POST' || method === 'PUT') && url.includes('/graph')) {
      const body = request.postData();
      if (body) {
        console.log(`\n  [SAVE REQUEST] ${method} ${url} (${body.length} bytes)`);
        capturedSaves.push({
          url,
          method,
          timestamp: new Date().toISOString(),
          requestBody: JSON.parse(body),
        });
      }
    }
  });

  await page.goto('https://test.agenthub.qubi.com/login', { waitUntil: 'domcontentloaded', timeout: 60000 });

  console.log('  Browser is open.\n');
  console.log('  Instructions:');
  console.log('    1. Log in');
  console.log('    2. Go to Agentic Flows / Workflows');
  console.log('    3. Open an EXISTING workflow that has nodes + connections');
  console.log('    4. Wait for it to fully load on the canvas');
  console.log('');
  await waitForEnter('  >> Press Enter after the workflow is loaded on canvas: ');

  console.log('\n  Checking captured data...');

  // If we haven't captured a graph yet, the user might need to refresh
  if (capturedGraphs.length === 0) {
    console.log('  No graph captured yet. Try refreshing the page or opening another workflow.');
    await waitForEnter('  >> Press Enter after opening/refreshing a workflow: ');
  }

  // Ask if user wants to also capture a save
  console.log('\n  Want to capture a save payload too?');
  console.log('  If yes: make a small change (move a node) and click Save.');
  await waitForEnter('  >> Press Enter when done (or just press Enter to skip): ');

  // Write output
  console.log('\n[Output] Writing captured data...');

  // Write all captured graphs
  const graphPath = path.join(OUTPUT_DIR, 'captured_workflows.json');
  fs.writeFileSync(graphPath, JSON.stringify({
    captured_at: new Date().toISOString(),
    graphs: capturedGraphs,
    saves: capturedSaves,
  }, null, 2), 'utf-8');
  console.log(`  ✓ ${graphPath}`);
  console.log(`    Graphs captured: ${capturedGraphs.length}`);
  console.log(`    Saves captured: ${capturedSaves.length}`);

  // Write pretty-printed first graph separately for easy reading
  if (capturedGraphs.length > 0) {
    const firstGraph = capturedGraphs[0].data;
    const prettyPath = path.join(OUTPUT_DIR, 'workflow_graph_sample.json');
    
    // If graphJson is a string, parse it
    let graphObj = firstGraph;
    if (firstGraph.graphJson && typeof firstGraph.graphJson === 'string') {
      graphObj = { ...firstGraph, graphJson: JSON.parse(firstGraph.graphJson) };
    }
    
    fs.writeFileSync(prettyPath, JSON.stringify(graphObj, null, 2), 'utf-8');
    console.log(`  ✓ ${prettyPath} (pretty-printed)`);

    // Summary
    const graph = graphObj.graphJson || graphObj;
    if (graph.nodes) {
      console.log(`\n  Workflow summary:`);
      console.log(`    Nodes: ${graph.nodes.length}`);
      console.log(`    Edges: ${graph.edges?.length || 0}`);
      console.log(`    Node types: ${[...new Set(graph.nodes.map(n => n.type))].join(', ')}`);
      if (graph.edges?.length > 0) {
        console.log(`    Edge sample: ${graph.edges[0].source} → ${graph.edges[0].target}`);
      }
    }
  }

  // API calls log
  const apiPath = path.join(OUTPUT_DIR, 'api_calls_capture.json');
  fs.writeFileSync(apiPath, JSON.stringify(allApiCalls, null, 2), 'utf-8');
  console.log(`  ✓ ${apiPath} (${allApiCalls.length} calls)`);

  console.log('\n══════════════════════════════════════════════════════════════');
  console.log('  DONE! Check output/ folder.');
  console.log('══════════════════════════════════════════════════════════════');

  await waitForEnter('\n  >> Press Enter to close browser: ');
  await browser.close();
})();
