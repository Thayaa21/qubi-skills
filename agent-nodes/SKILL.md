---
name: agent-nodes
description: "Add AI Agent nodes to qubi Agentic Flows -- selecting a real agentId, systemPrompt vs userMessage, chaining agent output. Use when a workflow calls a qubi AI agent."
---

# Agent Nodes

> "Never invent an agentId" is the most-repeated rule in this repo. This skill is where the actual discovery procedure lives, not just the warning.

## What this skill is

`Agent` calls an existing AI agent configured on the qubi platform. It's the second most-used node type in the evaluation corpus (69 instances, 51 of 100 workflows) -- and its one hard rule is that `agentId` is not something you can know or guess offline. It's tenant-specific, and the designer's own dropdown for it was never captured (`schema-extractor/output/element_properties.json` shows `Select Agent: options: null`).

## When to invoke

- The user's workflow calls an AI agent, or asks a model to summarize/analyze/generate something as a step
- `qubi flow validate` reports `MISSING_REQUIRED_FIELD` or `INVALID_NODE_DATA` on an `Agent` node

## Node reference

| Field | Required | Notes |
|---|---|---|
| `name` | yes | |
| `agentId` | yes | **Real platform id -- see Phase 1. Never invent one.** |
| `description` | no | |
| `input` | no | |
| `systemPrompt` | no | Sets the agent's role/behavior |
| `userMessage` | no | The actual request; supports `{{variable}}` interpolation |
| `saveOutputAs` | no | |

## Phase 1: Discover the real agentId -- never invent one

```bash
qubi agents list
```

Present the results to the human and let them pick. There is no offline way to know which agents exist on a given tenant. If you're building a fixture or example rather than a real workflow, use the sentinel `00000000-0000-0000-0000-000000000000` and say so explicitly -- see [fixtures/single_agent.json](fixtures/single_agent.json).

## Phase 2: systemPrompt vs userMessage

- `systemPrompt` sets the agent's role or persona ("You are a research assistant") and is usually static
- `userMessage` is the actual request for this invocation, and is where `{{variable}}` interpolation belongs ("Summarize this data: {{rawData}}")

Don't put the whole request in `systemPrompt` -- it makes the node harder to reuse and harder to read on the canvas.

## Phase 3: Chain agents

Multiple `Agent` nodes in sequence, each reading the previous one's `saveOutputAs`, is a common real pattern -- research → strategy → copy, or extract → verify → summarize. See [fixtures/agent_chain.json](fixtures/agent_chain.json).

## Phase 4: Validate

```bash
qubi flow validate <file.json>
```

An `Agent` node with `data: null` or missing `agentId` fails with `MISSING_REQUIRED_FIELD` (plus `INVALID_NODE_DATA`/`DATA_TYPE_MISMATCH` if `data` itself is malformed) -- this was historically the worst gap in the offline validator, since a node with genuinely no agent configured used to validate as clean. See [fixtures/invalid/agent_data_null.json](fixtures/invalid/agent_data_null.json).

## Unverified

| ID | Claim | Why unverifiable offline | How to verify | Status |
|----|-------|---------------------------|----------------|--------|
| UV-AGENT-01 | The example `agentId` in [workflow-builder/examples.md](../workflow-builder/examples.md) is real | It's a genuine captured session value, not invented -- but agentIds are tenant-specific and may not exist on every tenant | Run `qubi agents list` on the human's tenant and confirm | open |

## Operating Rules

**Always:**
- Get `agentId` from `qubi agents list`, present it to the human, let them pick
- Put static role/persona text in `systemPrompt`, the actual request in `userMessage`
- Use the all-zeros sentinel for any fixture/example, not a plausible-looking fake id

**Never:**
- Invent an `agentId` -- there is no way to guess a real one
- Assume the same `agentId` works across tenants
