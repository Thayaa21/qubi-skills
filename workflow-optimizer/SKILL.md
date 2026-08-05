---
name: workflow-optimizer
description: "Analyze existing qubi Agentic Flows workflows and suggest improvements — reduce steps, fix inefficiencies, add error handling, optimize data flow."
---

# Workflow Optimizer

> Analyze an existing qubi workflow, identify inefficiencies, and generate an optimized version.

## What this skill is

A workflow analysis skill that takes an existing qubi Agentic Flows JSON, examines its structure, and produces an improved version with better error handling, reduced redundancy, and optimized data flow.

## When to invoke

- User says "optimize this workflow" or "improve this flow"
- User asks "what's wrong with this workflow" or "review my flow"
- User provides a workflow JSON and asks for improvements
- User mentions "refactor", "clean up", or "simplify" a workflow

## Phase 1: Analyze the Workflow

Load and examine:
1. **Node count and types** — is it overly complex?
2. **Data flow** — are variables passed efficiently between nodes?
3. **Redundancy** — are there duplicate HTTP calls or unnecessary nodes?
4. **Error handling** — what happens when a node fails?
5. **Naming** — are node names descriptive or generic?
6. **Positioning** — is the layout readable?
7. **Dead ends** — are there orphan nodes with no edges?

## Phase 2: Identify Issues

| Issue | Severity | Example |
|-------|----------|---------|
| Redundant API calls | High | Same endpoint called twice |
| No error handling path | High | HTTP call with no Branch for failure |
| Generic node names | Medium | "Code" instead of "Format Invoice Data" |
| Unnecessary Assign | Low | Setting a variable that's only used once |
| Poor layout | Low | Nodes overlapping or in random positions |
| Missing saveOutputAs | Medium | Node output not captured for downstream use |
| Over-segmented | Medium | 3 Code nodes that could be 1 |

## Phase 3: Generate Optimized Version

Apply improvements:
1. **Merge redundant nodes** — combine sequential Code nodes doing related work
2. **Add error handling** — Branch after Http nodes to handle failures
3. **Fix naming** — descriptive names reflecting what each node does
4. **Optimize data flow** — ensure saveOutputAs is used efficiently
5. **Clean layout** — proper horizontal spacing, branches fork vertically
6. **Remove dead nodes** — delete unreachable nodes

## Phase 4: Present Changes

Show the human:
1. Original summary (node count, edge count)
2. List of issues found
3. What was changed and why
4. Optimized summary (node count, edge count)
5. The new JSON

Ask for confirmation before saving.

## Rules

- Never remove functionality — only restructure
- Preserve all business logic
- If unsure whether something is redundant, keep it and flag it
- Always validate the optimized version
- Don't add nodes unless explicitly needed for error handling
