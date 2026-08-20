---
name: rpa-automation
description: "Call an existing qubi RPA automation from an Agentic Flow. Use when a workflow must drive a desktop application or a legacy system that has no API."
---

# RPA Automation

> `RPA` is the least-used real node type in the schema -- 4 instances across the entire 100-workflow evaluation corpus. This skill exists so the one real rule (never invent an `automationId`) doesn't get skipped just because the node is rare.

## What this skill is

`RPA` triggers an existing desktop/legacy-system automation that was built and registered on the qubi platform separately from the Agentic Flow itself. The flow doesn't define what the automation does -- it just points at one by id and runs it.

## When to invoke

- The user's workflow needs to drive a desktop application, a legacy system without an API, or anything that requires a UI-level automation rather than an HTTP call
- The user mentions RPA, desktop automation, or a legacy system integration
- `qcli flow validate` reports `MISSING_REQUIRED_FIELD` on an `RPA` node

## Node reference

| Field | Required | Notes |
|---|---|---|
| `name` | yes | |
| `automationId` | yes | **Real platform id -- see Phase 1. Never invent one.** |
| `description` | no | |
| `input` | no | |
| `saveOutputAs` | no | |

## Phase 1: Discover the real automationId -- never invent one

```bash
qcli rpa list
```

Present the results to the human and let them pick, the same way an `Agent` node's `agentId` is discovered via `qcli agents list`. There is no offline way to know which automations exist on a given tenant -- `automationId` is exactly as tenant-specific as `agentId`, and the designer dropdown for it was never captured (see Unverified).

If you're building a fixture or example rather than a real workflow, use the sentinel `00000000-0000-0000-0000-000000000000` -- see [fixtures/rpa_single_step.json](fixtures/rpa_single_step.json) -- and say so explicitly rather than letting a plausible-looking fake id sit in the file.

## Phase 2: Gate it with a Branch when the automation is conditional

RPA automations are often expensive or slow, so real workflows gate them behind a check rather than always running them. See [fixtures/rpa_after_branch.json](fixtures/rpa_after_branch.json): fetch pending tasks, a `Code` node decides whether any are high-priority, a `Branch` routes to the `RPA` node only if so, and both branch legs converge at `End` -- see [branch-and-converge](../branch-and-converge/SKILL.md) for the general pattern.

## Phase 3: Validate

```bash
qcli flow validate <file.json>
```

Missing `automationId` produces `MISSING_REQUIRED_FIELD` -- see [fixtures/invalid/rpa_no_automation_id.json](fixtures/invalid/rpa_no_automation_id.json).

## Unverified

| ID | Claim | Why unverifiable offline | How to verify | Status |
|----|-------|---------------------------|----------------|--------|
| UV-RPA-01 | Whether `qcli rpa list` output includes enough detail to disambiguate automations with similar names | Requires a live authenticated session and real tenant data | Run `qcli rpa list -j` against a real tenant and inspect the fields returned | open |

## Operating Rules

**Always:**
- Get `automationId` from `qcli rpa list`, present it to the human, let them pick
- Gate an RPA call behind a `Branch` if it's conditional or expensive
- Use the all-zeros sentinel for any fixture/example, not a plausible-looking fake id

**Never:**
- Invent an `automationId` -- it is exactly as tenant-specific and unguessable as `agentId`
- Assume the same `automationId` works across tenants
