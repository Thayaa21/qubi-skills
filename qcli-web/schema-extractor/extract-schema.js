/**
 * qubi Agentic Flows — Schema Extractor v3
 * 
 * YOU navigate to the workflow designer canvas manually.
 * Then press Enter — the script takes over and extracts everything.
 * 
 * Usage:
 *   node extract-schema.js
 *   → Browser opens
 *   → You log in, navigate to Agentic Flows, open a workflow canvas
 *   → Press Enter in terminal
 *   → Script extracts all palette elements + properties + captures save payload
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const OpenAI = require('openai');

require('dotenv').config({ path: path.join(__dirname, '.env') });

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const DELAY_MS = 1000;
const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');
const OUTPUT_DIR = path.join(__dirname, 'output');

const PALETTE_ELEMENTS = [
  'Start', 'End', 'Agent', 'Assign', 'Branch', 'Code',
  'DocumentAI', 'HTTP', 'RPA', 'Human In The Loop',
  'HITL Task', 'JsonParser', 'TextParser'
];

// ---------------------------------------------------------------------------
// OpenAI
// ---------------------------------------------------------------------------

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

async function askGPT(systemPrompt, userPrompt) {
  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4o',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ],
      temperature: 0,
      max_tokens: 3000,
    });
    const content = response.choices[0].message.content.trim();
    const cleaned = content.replace(/^```json\n?/, '').replace(/\n?```$/, '');
    return JSON.parse(cleaned);
  } catch (err) {
    console.log(`    [GPT ERROR] ${err.message}`);
    return null;
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function screenshot(page, name) {
  const filePath = path.join(SCREENSHOT_DIR, `${name}.png`);
  await page.screenshot({ path: filePath, fullPage: true });
  console.log(`  [screenshot] ${filePath}`);
}

function waitForEnter(prompt) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise(resolve => {
    rl.question(prompt, () => { rl.close(); resolve(); });
  });
}

// ---------------------------------------------------------------------------
// Network Capture
// ---------------------------------------------------------------------------

const capturedRequests = [];
let savePayload = null;

function setupNetworkCapture(page) {
  page.on('request', (request) => {
    const url = request.url();
    const method = request.method();
    let postData = null;
    try { postData = request.postData(); } catch (_) {}

    capturedRequests.push({ method, url, postData });

    // Only log API calls (skip static assets, blazor noise)
    if (url.includes('/api/') && !url.includes('_blazor')) {
      console.log(`  [API] ${method} ${url}`);
    }
  });
}

// ---------------------------------------------------------------------------
// Deep DOM Extraction — Gets ALL visible elements with their text and position
// ---------------------------------------------------------------------------

async function getFullDOM(page) {
  return await page.evaluate(() => {
    const results = [];

    function walk(el, depth = 0) {
      if (depth > 15) return;
      if (!el || !el.tagName) return;

      const tag = el.tagName.toLowerCase();
      if (['script', 'style', 'noscript', 'path', 'circle', 'line', 'defs', 'clippath'].includes(tag)) return;

      const rect = el.getBoundingClientRect();
      if (rect.width === 0 && rect.height === 0) return;

      // Get direct text (not from children)
      const directText = Array.from(el.childNodes)
        .filter(n => n.nodeType === 3)
        .map(n => n.textContent.trim())
        .join(' ')
        .trim();

      const isInteractive = ['a', 'button', 'input', 'select', 'textarea'].includes(tag) ||
        el.getAttribute('draggable') === 'true' ||
        el.getAttribute('role') === 'button' ||
        el.hasAttribute('onclick') ||
        el.getAttribute('tabindex') === '0';

      if (directText || isInteractive) {
        let selector = '';
        if (el.id) selector = `#${el.id}`;
        else if (el.getAttribute('data-testid')) selector = `[data-testid="${el.getAttribute('data-testid')}"]`;
        else if (el.getAttribute('data-type')) selector = `[data-type="${el.getAttribute('data-type')}"]`;
        else if (el.getAttribute('data-id')) selector = `[data-id="${el.getAttribute('data-id')}"]`;
        else {
          selector = tag;
          if (el.className && typeof el.className === 'string') {
            const cls = el.className.split(' ').filter(c => c && c.length < 40).slice(0, 2).join('.');
            if (cls) selector += '.' + cls;
          }
        }

        const entry = { tag, selector, text: directText.slice(0, 100) };
        entry.x = Math.round(rect.x + rect.width / 2);
        entry.y = Math.round(rect.y + rect.height / 2);
        entry.w = Math.round(rect.width);
        entry.h = Math.round(rect.height);

        if (el.getAttribute('type')) entry.type = el.getAttribute('type');
        if (el.getAttribute('placeholder')) entry.placeholder = el.getAttribute('placeholder');
        if (el.getAttribute('name')) entry.name = el.getAttribute('name');
        if (el.getAttribute('formcontrolname')) entry.formControl = el.getAttribute('formcontrolname');
        if (el.getAttribute('draggable') === 'true') entry.draggable = true;
        if (isInteractive) entry.interactive = true;
        if (el.getAttribute('role')) entry.role = el.getAttribute('role');
        if (el.getAttribute('aria-label')) entry.ariaLabel = el.getAttribute('aria-label');

        results.push(entry);
      }

      for (const child of el.children) {
        walk(child, depth + 1);
      }
    }

    walk(document.body);
    return results;
  });
}

// ---------------------------------------------------------------------------
// Extract palette elements by finding them in DOM and clicking each one
// ---------------------------------------------------------------------------

async function extractPaletteElements(page) {
  console.log('\n[Extraction] Scanning DOM for palette elements...');
  
  const allProperties = {};
  
  // Step 1: Get the full DOM
  let dom = await getFullDOM(page);
  console.log(`  DOM scan: ${dom.length} elements found.`);
  await screenshot(page, '10-canvas-before-extraction');

  // Step 2: Find palette items by matching their text content
  const paletteItems = [];
  for (const name of PALETTE_ELEMENTS) {
    const match = dom.find(el => el.text === name);
    if (match) {
      paletteItems.push({ name, ...match });
    }
  }

  console.log(`\n  Palette items found in DOM: ${paletteItems.length}/${PALETTE_ELEMENTS.length}`);
  for (const item of paletteItems) {
    console.log(`    ✓ ${item.name} at (${item.x}, ${item.y})`);
  }

  const missing = PALETTE_ELEMENTS.filter(n => !paletteItems.find(p => p.name === n));
  if (missing.length > 0) {
    console.log(`  Missing (may need scrolling): ${missing.join(', ')}`);
  }

  // Step 3: Find the canvas area (React Flow container)
  const canvasBox = await page.evaluate(() => {
    // React Flow uses a div with class "react-flow" or similar
    const canvas = document.querySelector('.react-flow, .react-flow__renderer, [class*="react-flow"], [class*="canvas"], [class*="designer"]');
    if (canvas) {
      const rect = canvas.getBoundingClientRect();
      return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
    }
    // Fallback: estimate canvas as the large area to the right of palette
    return { x: 600, y: 200, width: 800, height: 600 };
  });

  console.log(`  Canvas area: x=${canvasBox.x}, y=${canvasBox.y}, w=${canvasBox.width}, h=${canvasBox.height}`);

  // Target position for drops — center of canvas, offset each node to avoid overlap
  const canvasCenterX = canvasBox.x + canvasBox.width / 2;
  const canvasCenterY = canvasBox.y + canvasBox.height / 2;

  // Step 4: For each palette element, DRAG it onto the canvas
  for (let i = 0; i < paletteItems.length; i++) {
    const item = paletteItems[i];
    console.log(`\n  ━━━ ${item.name} ━━━`);

    // Calculate drop position (spread nodes in a grid)
    const col = i % 4;
    const row = Math.floor(i / 4);
    const dropX = canvasCenterX - 200 + (col * 150);
    const dropY = canvasCenterY - 150 + (row * 150);

    // Drag from palette to canvas
    console.log(`    Dragging from (${item.x}, ${item.y}) → (${Math.round(dropX)}, ${Math.round(dropY)})`);
    
    await page.mouse.move(item.x, item.y);
    await sleep(300);
    await page.mouse.down();
    await sleep(300);
    // Move in steps to simulate real drag
    await page.mouse.move(dropX, dropY, { steps: 20 });
    await sleep(300);
    await page.mouse.up();
    await sleep(DELAY_MS);

    // Check if a node appeared — re-scan the DOM for react-flow nodes
    const nodeCount = await page.evaluate(() => {
      return document.querySelectorAll('.react-flow__node, [class*="react-flow__node"]').length;
    });
    console.log(`    Nodes on canvas: ${nodeCount}`);

    if (nodeCount === 0 && i === 0) {
      // If first drag didn't work, maybe we need to use a different approach
      console.log(`    Drag may not have worked. Trying double-click on palette item...`);
      try {
        await page.dblclick(`text="${item.name}"`, { timeout: 3000 });
        await sleep(DELAY_MS);
      } catch(_) {}
    }

    // Click the placed node on canvas to select it and open properties
    // The most recently placed node should be the last .react-flow__node
    try {
      const nodes = await page.$$('.react-flow__node, [class*="react-flow__node"]');
      if (nodes.length > 0) {
        const lastNode = nodes[nodes.length - 1];
        await lastNode.click();
        console.log(`    Clicked node on canvas to open properties.`);
        await sleep(1500);
      }
    } catch(e) {
      console.log(`    Could not click canvas node: ${e.message}`);
    }

    // Extract properties panel
    const fields = await extractPropertiesPanel(page, item.name);
    allProperties[item.name] = { fields };
    console.log(`    Fields found: ${fields.length}`);

    await screenshot(page, `11-element-${item.name.replace(/\s+/g, '_').toLowerCase()}`);

    // Deselect / close panel
    try { await page.keyboard.press('Escape'); } catch(_) {}
    await sleep(500);

    // Re-scan DOM in case palette items shifted after dropping
    if (i < paletteItems.length - 1) {
      dom = await getFullDOM(page);
      // Update remaining palette item positions
      for (let j = i + 1; j < paletteItems.length; j++) {
        const updated = dom.find(el => el.text === paletteItems[j].name);
        if (updated) {
          paletteItems[j].x = updated.x;
          paletteItems[j].y = updated.y;
        }
      }
    }
  }

  // Handle missing elements (scroll palette and retry)
  if (missing.length > 0) {
    console.log(`\n  Scrolling palette to find missing elements...`);
    
    // Scroll the palette list
    const firstItem = paletteItems[0];
    if (firstItem) {
      await page.mouse.move(firstItem.x, firstItem.y);
      await page.mouse.wheel(0, 300);
      await sleep(1000);
    }

    dom = await getFullDOM(page);
    for (const name of missing) {
      const match = dom.find(el => el.text === name);
      if (match) {
        console.log(`    Found: ${name} at (${match.x}, ${match.y})`);
        const col = paletteItems.length % 4;
        const row = Math.floor(paletteItems.length / 4);
        const dropX = canvasCenterX - 200 + (col * 150);
        const dropY = canvasCenterY - 150 + (row * 150);

        await page.mouse.move(match.x, match.y);
        await sleep(300);
        await page.mouse.down();
        await sleep(300);
        await page.mouse.move(dropX, dropY, { steps: 20 });
        await sleep(300);
        await page.mouse.up();
        await sleep(DELAY_MS);

        // Click node and extract
        const nodes = await page.$$('.react-flow__node, [class*="react-flow__node"]');
        if (nodes.length > 0) {
          await nodes[nodes.length - 1].click();
          await sleep(1500);
        }

        const fields = await extractPropertiesPanel(page, name);
        allProperties[name] = { fields };
        console.log(`    Fields: ${fields.length}`);
        try { await page.keyboard.press('Escape'); } catch(_) {}
        await sleep(500);
      } else {
        allProperties[name] = { error: 'not_found_after_scroll', fields: [] };
        console.log(`    Still missing: ${name}`);
      }
    }
  }

  return allProperties;
}

// ---------------------------------------------------------------------------
// Extract properties panel — gets all form fields visible in the right panel
// ---------------------------------------------------------------------------

async function extractPropertiesPanel(page, elementName) {
  // Get all visible inputs/selects/textareas from the properties panel (right side)
  const rawFields = await page.evaluate(() => {
    const results = [];
    
    // Get the page width to determine "right side"
    const pageWidth = window.innerWidth;
    const rightThreshold = pageWidth * 0.5; // anything on right half of page
    
    const inputs = document.querySelectorAll(
      'input:not([type="hidden"]), select, textarea, ' +
      '[role="combobox"], [role="listbox"], [role="checkbox"], [role="switch"], ' +
      '[contenteditable="true"]'
    );

    for (const input of inputs) {
      const rect = input.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) continue;
      // Only include elements on the right side (properties panel)
      if (rect.x < rightThreshold) continue;

      let label = '';
      const id = input.id || input.getAttribute('name') || input.getAttribute('formcontrolname') || '';
      if (id) {
        const labelEl = document.querySelector(`label[for="${id}"]`);
        if (labelEl) label = labelEl.textContent.trim();
      }
      if (!label) {
        const parent = input.closest('[class*="field"], [class*="form-group"], [class*="MuiFormControl"], [class*="MuiGrid"], [class*="property"]');
        if (parent) {
          const lbl = parent.querySelector('label, [class*="label"], [class*="Label"], p, span');
          if (lbl && lbl.textContent.trim().length < 50) label = lbl.textContent.trim();
        }
      }
      if (!label) {
        label = input.getAttribute('placeholder') || input.getAttribute('aria-label') ||
                input.getAttribute('name') || input.getAttribute('formcontrolname') || '';
      }
      if (!label && input.previousElementSibling) {
        const prev = input.previousElementSibling;
        if (['LABEL', 'SPAN', 'P', 'DIV'].includes(prev.tagName)) {
          const t = prev.textContent.trim();
          if (t.length < 50) label = t;
        }
      }

      const tagName = input.tagName.toLowerCase();
      const inputType = tagName === 'select' ? 'select' :
                        input.getAttribute('role') === 'combobox' ? 'select' :
                        input.getAttribute('role') === 'checkbox' ? 'checkbox' :
                        input.getAttribute('role') === 'switch' ? 'toggle' :
                        tagName === 'textarea' ? 'textarea' :
                        input.getAttribute('type') || 'text';

      let options = [];
      if (tagName === 'select') {
        options = Array.from(input.querySelectorAll('option'))
          .map(o => o.textContent.trim()).filter(Boolean);
      }

      // Skip the search box and auto-save toggle (they're global, not per-node)
      if (label === 'Search nodes...' || label.includes('Auto Save')) continue;
      if (input.getAttribute('placeholder') === 'Search nodes...') continue;

      results.push({
        label,
        inputType,
        tagName,
        name: input.getAttribute('name') || input.getAttribute('formcontrolname') || '',
        placeholder: input.getAttribute('placeholder') || '',
        required: input.hasAttribute('required') || input.getAttribute('aria-required') === 'true',
        value: input.value || '',
        options,
      });
    }

    // Also collect ALL visible text from the right panel area for GPT analysis
    const rightPanelTexts = [];
    const allEls = document.querySelectorAll('*');
    for (const el of allEls) {
      const rect = el.getBoundingClientRect();
      if (rect.x < rightThreshold || rect.width === 0) continue;
      const directText = Array.from(el.childNodes)
        .filter(n => n.nodeType === 3)
        .map(n => n.textContent.trim())
        .join(' ').trim();
      if (directText && directText.length > 1 && directText.length < 80) {
        rightPanelTexts.push(directText);
      }
    }

    return { fields: results, panelTexts: [...new Set(rightPanelTexts)] };
  });

  // If we found fields directly, return them
  if (rawFields.fields.length > 0) {
    return rawFields.fields;
  }

  // If no input fields but panel has text, ask GPT to interpret what fields exist
  if (rawFields.panelTexts.length > 2) {
    console.log(`    No input fields detected. Panel text: ${rawFields.panelTexts.slice(0, 8).join(' | ')}`);
    
    const gptResult = await askGPT(
      'You analyze text from a workflow node\'s properties panel. The panel shows configuration options for this node type. Return a JSON array of the configuration fields you can identify from the text. Each: {"label": "field name", "type": "text|select|boolean|code|json|number", "required": false, "description": "what this field does"}. If text says "Select a node to configure" or similar empty state, return [].',
      `Element: "${elementName}"\nProperties panel text content:\n${JSON.stringify(rawFields.panelTexts)}`
    );

    if (gptResult && Array.isArray(gptResult)) {
      return gptResult;
    }
  }

  return [];
}

// ---------------------------------------------------------------------------
// Save & Capture
// ---------------------------------------------------------------------------

async function saveAndCapture(page) {
  console.log('\n[Save] Attempting to save and capture the payload...');

  const savePromise = new Promise((resolve) => {
    const handler = (request) => {
      const url = request.url();
      const method = request.method();
      if ((method === 'POST' || method === 'PUT' || method === 'PATCH') &&
          url.includes('/api/') && !url.includes('_blazor') &&
          (url.includes('workflow') || url.includes('graph') || url.includes('save') || url.includes('flow'))) {
        try {
          const body = request.postData();
          if (body && body.length > 50) {
            resolve({ method, url, body });
            page.removeListener('request', handler);
          }
        } catch (_) {}
      }
    };
    page.on('request', handler);
    setTimeout(() => resolve(null), 30000);
  });

  // Try to click save
  try {
    await page.click('text="save"', { timeout: 3000 });
  } catch(_) {
    try {
      await page.click('button:has-text("Save")', { timeout: 3000 });
    } catch(_) {
      console.log('  Could not find Save button automatically.');
      await waitForEnter('  >> Please click Save manually, then press Enter: ');
    }
  }

  const result = await savePromise;
  if (result) {
    savePayload = result;
    console.log(`  Captured: ${result.method} ${result.url} (${result.body.length} bytes)`);
  } else {
    console.log('  No save request captured in 30s.');
    // Look through all captured requests
    const candidates = capturedRequests.filter(r =>
      (r.method === 'POST' || r.method === 'PUT') &&
      r.url.includes('/api/') && !r.url.includes('_blazor') &&
      r.postData && r.postData.length > 100
    );
    if (candidates.length > 0) {
      const best = candidates[candidates.length - 1];
      savePayload = { method: best.method, url: best.url, body: best.postData };
      console.log(`  Fallback found: ${best.method} ${best.url}`);
    }
  }

  await sleep(2000);
  await screenshot(page, '20-after-save');
}

// ---------------------------------------------------------------------------
// Write Output
// ---------------------------------------------------------------------------

function writeOutput(elementProperties) {
  console.log('\n[Output] Writing files...');
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  // element_properties.json
  const elemPath = path.join(OUTPUT_DIR, 'element_properties.json');
  fs.writeFileSync(elemPath, JSON.stringify(elementProperties, null, 2), 'utf-8');
  console.log(`  ✓ ${elemPath}`);

  // save_payload_sample.json
  const savePath = path.join(OUTPUT_DIR, 'save_payload_sample.json');
  if (savePayload) {
    let obj;
    try { obj = JSON.parse(savePayload.body); } catch(_) { obj = { raw: savePayload.body }; }
    fs.writeFileSync(savePath, JSON.stringify({
      _meta: { method: savePayload.method, url: savePayload.url, captured_at: new Date().toISOString() },
      payload: obj,
    }, null, 2), 'utf-8');
  } else {
    fs.writeFileSync(savePath, JSON.stringify({ error: 'not_captured' }, null, 2), 'utf-8');
  }
  console.log(`  ✓ ${savePath}`);

  // API calls log (only /api/ calls, no noise)
  const apiPath = path.join(OUTPUT_DIR, 'api_calls.json');
  const apiCalls = capturedRequests
    .filter(r => r.url.includes('/api/') && !r.url.includes('_blazor'))
    .map(r => ({ method: r.method, url: r.url, hasBody: !!(r.postData && r.postData.length > 0) }));
  fs.writeFileSync(apiPath, JSON.stringify(apiCalls, null, 2), 'utf-8');
  console.log(`  ✓ ${apiPath} (${apiCalls.length} API calls)`);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

(async () => {
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║  qubi Schema Extractor v3 — You navigate, I extract         ║');
  console.log('╠══════════════════════════════════════════════════════════════╣');
  console.log('║  1. Browser will open                                       ║');
  console.log('║  2. YOU: log in, go to Agentic Flows, open the designer     ║');
  console.log('║  3. Make sure the palette (node list) is visible            ║');
  console.log('║  4. Press Enter in this terminal                            ║');
  console.log('║  5. Script takes over and extracts everything               ║');
  console.log('║                                                             ║');
  console.log('║  Will NOT delete anything.                                  ║');
  console.log('╚══════════════════════════════════════════════════════════════╝\n');

  if (!process.env.OPENAI_API_KEY) {
    console.error('ERROR: Set OPENAI_API_KEY in .env file.');
    process.exit(1);
  }

  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  // Launch browser
  // Launch browser in full screen mode matching your actual monitor
  const browser = await chromium.launch({
    headless: false,
    slowMo: 50,
    args: ['--start-maximized'],
  });

  const context = await browser.newContext({
    viewport: null, // null = use the window size (maximized)
    ignoreHTTPSErrors: true,
  });

  const page = await context.newPage();
  setupNetworkCapture(page);

  // Open the login page for the user
  await page.goto('https://test.agenthub.qubi.com/login', { waitUntil: 'domcontentloaded', timeout: 60000 });

  console.log('  Browser is open. Now:');
  console.log('    1. Log in');
  console.log('    2. Navigate to Agentic Flows');
  console.log('    3. Open a workflow (or create one)');
  console.log('    4. Make sure the left palette is VISIBLE (showing Start, End, Agent, etc.)');
  console.log('');
  await waitForEnter('  >> Press Enter when you are on the designer canvas with palette visible: ');

  console.log('\n  Taking over...');
  await sleep(1000);
  await screenshot(page, '00-handoff');

  try {
    // Extract all palette elements
    const elementProperties = await extractPaletteElements(page);

    // Try to save and capture payload
    await saveAndCapture(page);

    // Write output
    writeOutput(elementProperties);

    console.log('\n══════════════════════════════════════════════════════════════');
    console.log('  DONE! Check output/ folder for results.');
    console.log('  Workflow NOT deleted.');
    console.log('══════════════════════════════════════════════════════════════');

  } catch (err) {
    console.error('\n  ERROR:', err.message);
    await screenshot(page, '99-error');
    writeOutput({});
    console.log('  Partial output written.');
  } finally {
    console.log('\n  Browser left open for you to inspect.');
    await waitForEnter('  >> Press Enter to close: ');
    await browser.close();
  }
})();
