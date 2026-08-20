---
name: branch-and-converge
description: "Build correct conditional flows in qubi Agentic Flows -- Branch conditions, reconverging paths, and guaranteeing every path reaches End. Use when a workflow has an if/else, or when qcli flow validate reports UNREACHABLE_NODE or NO_PATH_TO_END."
---

# Branch and Converge

> Every Branch leg has to actually get somewhere. This skill exists because, historically, that has been the single most common way a generated qubi workflow breaks.

## What this skill is

`Branch` is qubi's only conditional-routing node type, and getting it right is entirely about the *edges* around it, not the node itself. The node's own required field is just `name` -- everything that can go wrong is graph-shaped: a leg that goes nowhere, a `Start` that never connects, two legs that never reconverge before `End`.

## What it solves

This is not a hypothetical risk. When the hardened qcli validator (which adds connectivity checking that the original validator lacked) was run over the 100-workflow evaluation corpus shipped with qcli-web, 95 workflows were perfectly clean and **5 were not** -- `complex/C06` through `complex/C10` each had a `Start` node with no outgoing edge, producing 136 `UNREACHABLE_NODE` and 5 `NO_PATH_TO_END` warnings between them. The original (unhardened) validator reported all 100 as clean. That gap is exactly what this skill is for.

Also worth knowing: `Branch` never appears in any of the 50 "simple" workflows in that corpus (by definition -- simple means linear), so branch-shaped mistakes concentrate in medium/complex work, which is also where they're hardest to spot by eye.

## When to invoke

- The user describes an if/else, a decision point, or "route based on X"
- `qcli flow validate` reports `UNREACHABLE_NODE`, `NO_PATH_TO_END`, `DUPLICATE_START`, or `DUPLICATE_END`
- A downloaded or hand-written workflow has more than one `Branch` node

## Node reference

| Field | Required | Notes |
|---|---|---|
| `name` | yes | |
| `description` | no | |
| `conditions` | no | **Optional, so the validator never inspects its shape -- see Unverified.** |
| `input` | no | |
| `saveOutputAs` | no | |

Because `conditions` is optional and unchecked, a `Branch` node with zero conditions and zero outgoing edges still passes field-level validation. The connectivity checks (below) are what actually catch a broken branch.

## Phase 1: Design the branch before writing nodes

For every `Branch`, decide up front:
1. How many legs (two for if/else, more for a routing table like fraud-risk-level or claim-tier)
2. What each leg does
3. **Where each leg reconverges** -- either at a shared node before `End`, or by every leg independently reaching `End`

Both convergence shapes are valid and both appear in real workflows -- see [fixtures/branch_reconverges.json](fixtures/branch_reconverges.json) (legs meet at a shared notification step) and [fixtures/branch_both_legs_to_end.json](fixtures/branch_both_legs_to_end.json) (legs go straight to separate `End`-adjacent nodes). [fixtures/three_way_branch.json](fixtures/three_way_branch.json) shows a three-leg routing table (fast-track / standard review / SIU referral) converging on a shared payment step -- this is the real shape of the C06 defect, repaired.

## Phase 2: Wire every edge deliberately

The defect class this skill exists to prevent is not "wrong condition logic" -- it's **missing edges**:

- Every `Branch` needs one outgoing edge per leg. A leg with zero edges is a silent dead end (see [fixtures/invalid/dangling_branch_leg.json](fixtures/invalid/dangling_branch_leg.json)).
- `Start` needs at least one outgoing edge. A `Start` with none detaches the entire graph from its own trigger -- this is exactly what happened in C06-C10 (see [fixtures/invalid/detached_start.json](fixtures/invalid/detached_start.json)).
- Every leg's terminal node needs a path forward to `End`, whether directly or through a shared node.

After generating a branching graph, don't just eyeball it -- walk each leg from `Start` and confirm it reaches `End`.

## Phase 3: Validate and read connectivity warnings literally

```bash
qcli flow validate <file.json>
```

| Code | Severity | Meaning | Fix |
|---|---|---|---|
| `UNREACHABLE_NODE` | warning | No path from `Start` reaches this node | Add the missing edge from `Start` or from whatever should precede it |
| `NO_PATH_TO_END` | warning | No path from `Start` reaches `End` | Trace the intended route and add the missing edge(s) |
| `DUPLICATE_START` | warning | More than one `Start` node | Keep exactly one; repoint or remove the rest |
| `DUPLICATE_END` | warning | More than one `End` node, but not all are reachable | Either connect every `End`, or consolidate to one |

**These are warnings, not errors** -- `qcli flow validate` still exits 0 and `qcli flow save` will still let you push a graph with dangling branches. Treat them as must-fix anyway: a workflow with an unreachable node renders as a disconnected island on the canvas and will never execute past the point of detachment.

## Unverified

| ID | Claim | Why unverifiable offline | How to verify | Status |
|----|-------|---------------------------|----------------|--------|
| UV-BRANCH-01 | The shape of `Branch.conditions` (e.g. `{"expression": ..., "targetNodeId": ...}`) | The field is optional, so the validator never inspects it -- captured real graphs show varying shapes | Configure a two-way branch in the designer and download the graph with `qcli flow get` | open |

## Operating Rules

**Always:**
- Give `Start` at least one outgoing edge
- Give every `Branch` leg an outgoing edge
- Trace every leg to `End`, directly or through a shared node
- Treat `UNREACHABLE_NODE` / `NO_PATH_TO_END` as must-fix even though they don't block `flow save`

**Never:**
- Assume a branch is wired correctly because the JSON "looks complete" -- validate connectivity explicitly
- Leave a `conditions` array unfilled and call the branch done -- the validator won't catch it, but a human reading the canvas will notice immediately
