---
name: document-to-workflow
description: "Convert process documents (PDD, SDD, BRD, SOPs) into qubi Agentic Flows workflow JSON. Accepts PDF, DOCX, images, spreadsheets — any client process documentation."
---

# Document to Workflow Converter

> Read any process document — PDD, SDD, BRD, SOP, flowchart, spreadsheet — understand the process flow, and generate a valid qubi Agentic Flows workflow JSON.

## What this skill is

A document-understanding skill that converts process documentation into executable qubi workflows. It reads the document, identifies the process steps, maps them to qubi node types, and generates a complete, validated workflow graph.

## What it solves

- Converting client-provided process documents into automatable workflows
- Interpreting flowcharts, step-by-step procedures, and decision trees
- Mapping business process steps to the correct qubi node types
- Handling ambiguity in process descriptions by making reasonable automation decisions

## When to invoke

- User provides a PDF, DOCX, image, or spreadsheet containing a process description
- User says "convert this document to a workflow" or "build a flow from this PDD"
- User shares a process diagram, flowchart, or step-by-step procedure
- User mentions PDD, SDD, BRD, SOP, or "process document" with qubi/workflow context

## Phase 1: Read and Understand the Document

1. **Identify the document type:**
   - PDD (Process Design Document) — detailed step-by-step with decision points
   - SDD (Solution Design Document) — technical architecture + integrations
   - BRD (Business Requirements Document) — high-level requirements + rules
   - SOP (Standard Operating Procedure) — sequential tasks
   - Flowchart/diagram — visual process flow
   - Spreadsheet — tabular process steps

2. **Extract the process flow:**
   - Identify each discrete step/action
   - Identify decision points (if/else, branches)
   - Identify integrations (APIs, databases, external systems)
   - Identify human touchpoints (approvals, reviews, data entry)
   - Identify data transformations (parsing, formatting, calculations)
   - Identify inputs and outputs at each step

3. **Map to automation categories:**

   | Process Step | Maps To |
   |-------------|---------|
   | Call an API / fetch data | Http node |
   | AI/LLM processing (summarize, classify, extract) | Agent node |
   | Run code / calculate / transform | Code node |
   | Decision / if-else / routing | Branch node |
   | Set a value / store data | Assign node |
   | Parse JSON response | JsonParser node |
   | Extract with regex | TextParser node |
   | Process a document (OCR, extract) | DocumentAI node |
   | Trigger desktop automation | RPA node |
   | Wait for human approval | HitlTask node |
   | Human review container | Hitl node |

## Phase 2: Design the Workflow

1. **Order the steps** into a linear or branching flow
2. **Name each node** clearly (what it does, not generic names)
3. **Define data flow:**
   - What each node receives as input
   - What each node saves as output (`saveOutputAs`)
   - How variables flow between nodes using `{{variableName}}`
4. **Handle decision points:**
   - Each branch condition becomes a Branch node
   - Map each path to its downstream nodes
5. **Identify unknowns:**
   - If an Agent node is needed → ask human for `agentId` (from `qubi agents list`)
   - If RPA is needed → ask human for `automationId` (from `qubi rpa list`)
   - If specific URLs/endpoints aren't in the document → ask human

## Phase 3: Generate the Workflow JSON

Generate a complete workflow following these rules:

**Structure:**
```json
{
  "nodes": [ ... ],
  "edges": [ ... ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "executionMode": "Sequential"
}
```

**Node format:**
```json
{
  "id": "<uuid-v4>",
  "type": "<NodeType>",
  "position": { "x": <number>, "y": <number> },
  "data": { "type": "<NodeType>", "name": "<descriptive name>", ...fields }
}
```

**Edge format:**
```json
{
  "id": "xy-edge__<sourceId>-<targetId>",
  "source": "<source-node-id>",
  "target": "<target-node-id>"
}
```

**Positioning:**
- Linear flows: space horizontally, 200px apart, same y
- Branches: fork vertically (y ± 100) then reconverge
- Start at x=100, y=200

## Phase 4: Validate

```bash
qubi flow validate <file.json>
```

Fix any errors. Re-validate until clean.

## Phase 5: Present to Human

Show the human:
1. A summary of what was extracted from the document
2. The node list (type + name)
3. The connection flow (A → B → C)
4. Any assumptions made
5. Any questions (missing agentIds, unclear steps, ambiguous routing)

Ask for confirmation before saving.

## Phase 6: Save

```bash
qubi flow save <file.json> --workflow-id <id>
```

## Document Interpretation Rules

**When the document is ambiguous:**
- Prefer Agent nodes for anything that says "analyze", "summarize", "classify", "decide"
- Prefer Http nodes for anything that says "call", "fetch", "send", "post", "integrate"
- Prefer Code nodes for "calculate", "format", "transform", "filter", "convert"
- Prefer Branch nodes for "if", "when", "based on", "depending on", "check"
- Prefer HitlTask for "review", "approve", "verify manually", "human check"

**When steps are too vague:**
- Ask the human for clarification rather than guessing
- If a step says "process the data" without specifics, ask what processing means

**When the document has too many steps:**
- Group related micro-steps into a single Code or Agent node
- Keep the workflow readable (5-15 nodes is ideal for most flows)
- Flag to the human if the document describes 20+ steps

## Node Types Quick Reference

| Type | Required Fields | When to Use |
|------|----------------|-------------|
| Start | name | Always first |
| End | name | Always last |
| Agent | name, agentId | AI/LLM tasks |
| Http | name, method, url | API calls |
| Code | name, language, code | Transforms, logic |
| Branch | name | Decisions |
| Assign | name | Set variables |
| DocumentAI | name, operation | Doc processing |
| RPA | name, automationId | Desktop automation |
| Hitl | name | Human-in-loop container |
| HitlTask | name, taskName, taskType, assignTo | Human tasks |
| JsonParser | name | Parse JSON |
| TextParser | name, regexPattern | Regex extraction |

## Operating Rules

**Always:**
- Read the entire document before generating
- Preserve the process logic faithfully
- Use descriptive node names from the document
- Include Start and End nodes
- Validate before presenting to human
- Ask about missing IDs (agentId, automationId)

**Never:**
- Invent process steps not in the document
- Skip steps because they seem unimportant
- Generate without validating
- Assume agentId or automationId values
- Save without human confirmation
