---
name: hitl-workflows
description: "Design human-in-the-loop steps in qubi Agentic Flows using Hitl and HitlTask nodes -- approval gates, escalation, task assignment. Use when a workflow needs a person in the loop, or the user mentions approval, review, or human sign-off."
---

# HITL Workflows

> Put a real person in a qubi Agentic Flow correctly: pause with Hitl, collect a structured decision with HitlTask, and route both outcomes to a real End.

## What this skill is

qubi has two human-in-the-loop node types, and they are easy to confuse: `Hitl` (a bare pause) and `HitlTask` (a structured task with a name, a type, and an assignee). Across the 100-workflow evaluation corpus shipped with qcli-web, `HitlTask` appears 61 times and `Hitl` appears **zero** times -- so almost nothing has ever exercised the plain pause node, and its relationship to `HitlTask` is genuinely unknown (see Unverified below). This skill exists so that gap doesn't get filled by guessing.

## What it solves

- Choosing `Hitl` vs `HitlTask` for a given approval step
- Filling `HitlTask`'s four fields (`taskName`, `taskType`, `assignTo`, plus optional `template`) without inventing values for the three that are platform dropdowns
- Wiring an approval/rejection branch so both outcomes reach `End` (the [branch-and-converge](../branch-and-converge/SKILL.md) skill owns the branch mechanics; this skill owns what happens at the human step itself)

## When to invoke

- The user asks for an approval step, a review step, a human sign-off, or "someone needs to check this first"
- A workflow design mentions escalation, manager approval, or assigning work to a person or group
- `qcli flow validate` reports a problem on a `Hitl` or `HitlTask` node

## Node reference

| Field | Node | Required | Notes |
|---|---|---|---|
| `name` | both | yes | Display name |
| `description` | both | no | |
| `input` | both | no | |
| `saveOutputAs` | both | no | Where the human's response/decision lands |
| `taskName` | HitlTask | yes | What the task is called in the human's queue |
| `taskType` | HitlTask | yes | **Platform dropdown, options never captured.** See Unverified. |
| `assignTo` | HitlTask | yes | **Platform dropdown (user or group), options never captured.** |
| `template` | HitlTask | no | **Platform dropdown, options never captured.** |

## Phase 1: Decide Hitl vs HitlTask

- Need only a pause, with no structured decision to capture? Use `Hitl`.
- Need a named task, assigned to a specific person or group, whose outcome the next node reads (e.g. a Branch checking `approvalResult.status`)? Use `HitlTask`.
- If genuinely unsure which the platform expects for "just wait for a human," say so to the human rather than guessing -- see Unverified.

## Phase 2: Fill HitlTask correctly

`taskType`, `assignTo`, and `template` are all platform dropdowns whose real option lists were never captured (see `schema-extractor/output/element_properties.json` in qcli-web -- each shows `options: null`). Do not invent a plausible-looking value like `"approval"`:

- If the human can supply the real value (from having used the designer), use it.
- Otherwise, use the sentinel `"UNVERIFIED"` for `taskType`/`assignTo` and tell the human explicitly that this field needs to be set from the designer before saving.

```json
{
  "type": "HitlTask",
  "name": "Review Generated Report",
  "taskName": "Review Generated Report",
  "taskType": "UNVERIFIED",
  "assignTo": "UNVERIFIED",
  "saveOutputAs": "approvalResult"
}
```

## Phase 3: Wire both outcomes to End

A `HitlTask` almost always feeds a `Branch` reading its `saveOutputAs` value. Both branch legs must reach `End` -- see [fixtures/approval_gate.json](fixtures/approval_gate.json) for the full worked example (Http generates something, HitlTask reviews it, Branch routes approved vs rejected, both legs converge at End). An approval branch with only one leg wired is the single most common defect class in this schema -- see [branch-and-converge](../branch-and-converge/SKILL.md).

## Phase 4: Validate

```bash
qcli flow validate <file.json>
```

`MISSING_REQUIRED_FIELD` on a HitlTask node almost always means `taskName`, `taskType`, or `assignTo` was left out -- see [fixtures/invalid/hitltask_missing_assignto.json](fixtures/invalid/hitltask_missing_assignto.json).

## Unverified

| ID | Claim | Why unverifiable offline | How to verify | Status |
|----|-------|---------------------------|----------------|--------|
| UV-HITLTASK-01 | `taskType` accepts values like `approval` | Designer dropdown; option list not captured | Open a HitlTask node in the designer and read the Task Type dropdown | open |
| UV-HITLTASK-02 | `assignTo` accepts a user id, a group id, or both | Designer dropdown; option list not captured | Open a HitlTask node in the designer and read the Assign To dropdown | open |
| UV-HITL-01 | Whether a `Hitl` node contains or merely precedes `HitlTask` nodes | The graph format has no nesting field; the designer's behavior is unobserved. `Hitl` never appears in the 100-workflow evaluation corpus. | Drop a `Hitl` node in the designer and see whether it accepts children | open |

## Operating Rules

**Always:**
- Fill `taskName`, `taskType`, and `assignTo` on every `HitlTask` -- they are all required
- Wire every branch leg coming out of a human decision to a real `End`
- Use the `UNVERIFIED` sentinel for a dropdown value you can't confirm, and say so to the human

**Never:**
- Invent a `taskType`, `assignTo`, or `template` value that looks plausible -- `"approval"` is not a confirmed platform value
- Assume `Hitl` nests `HitlTask` nodes without confirming it (see Unverified)
- Leave one branch leg of an approval decision unconnected
