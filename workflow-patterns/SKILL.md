---
name: workflow-patterns
description: "Reusable qubi Agentic Flow shapes -- retry, error branch, bounded polling, fan-out/fan-in. Use when designing a workflow's structure before writing individual nodes, especially if it needs to handle a failure case."
---

# Workflow Patterns

> Zero of the 100 workflows in qcli-web's evaluation corpus have a retry or an explicit error-handling branch. Every one is a happy path. This skill is the library for the other case.

## What this skill is

This isn't a node-type reference -- it's a structural one. Before writing individual nodes, decide the *shape* of the flow: does an API call need a retry? Does a failure need to be logged and still reach `End` rather than silently vanishing? Does the workflow wait on something that isn't ready yet? Does it need several independent calls before it can proceed? These are the same handful of shapes every time, and getting the shape right first makes writing the individual nodes mechanical.

## When to invoke

- Before writing nodes for a workflow that calls an external system that can fail or be slow
- The user describes retry, error handling, waiting/polling, or "do these things in parallel and combine them"
- A generated workflow only has a happy path and the user asks what happens when something goes wrong

## Pattern 1: Retry

Call, check success, retry once, then give up in a way that still reaches `End`. See [fixtures/retry_with_branch.json](fixtures/retry_with_branch.json): `Http` → `Branch` (succeeded?) → if not, `Http` again → `Branch` (succeeded this time?) → if still not, log the failure → `End`.

qubi's graph format has no loop construct -- there is no way to express "retry until success" as a cycle. A bounded number of explicit attempts, each its own `Http` + `Branch` pair, is the only representable shape. Decide the retry count up front; two attempts is a reasonable default unless the user specifies otherwise.

## Pattern 2: Error branch

Every real external call can fail, and a workflow that doesn't check should be treated as incomplete, not as simple. See [fixtures/error_branch.json](fixtures/error_branch.json): `Http` → `Branch` (did it error?) → success path processes the result, failure path logs it -- **and both paths still reach `End`**. The failure path existing but dead-ending is worse than not having one; see [branch-and-converge](../branch-and-converge/SKILL.md).

## Pattern 3: Bounded polling

qubi has no wait/sleep/loop primitive, so "poll until ready" has to become "check a bounded number of times, then escalate to a human if still not ready." See [fixtures/poll_until_ready.json](fixtures/poll_until_ready.json): check status → `Branch` (ready?) → if not, check again → still not ready → `HitlTask` escalation (see [hitl-workflows](../hitl-workflows/SKILL.md)) → `End`. If the platform later exposes a real wait/loop mechanism, this pattern should be revisited -- flag that explicitly to the human rather than assuming a workaround is the final answer.

## Pattern 4: Fan-out / fan-in

Several independent calls that don't depend on each other's results, converging on one aggregation step. See [fixtures/fan_out_fan_in.json](fixtures/fan_out_fan_in.json): `Start` has three outgoing edges (to three independent `Http` calls), each feeds a shared `Code` node that combines their results, which then reaches `End`. There is no confirmed guarantee the platform actually executes these concurrently rather than sequentially (see Unverified) -- use this shape for *independence*, not for a performance claim.

## Phase: Validate

```bash
qubi flow validate <file.json>
```

All four patterns validate to zero errors and zero warnings when built correctly -- if `UNREACHABLE_NODE` or `NO_PATH_TO_END` appears, an edge in the pattern is missing; see [branch-and-converge](../branch-and-converge/SKILL.md).

## Unverified

| ID | Claim | Why unverifiable offline | How to verify | Status |
|----|-------|---------------------------|----------------|--------|
| UV-PATTERN-01 | Whether fan-out branches (multiple edges out of one node) execute concurrently or sequentially | `executionMode: "Sequential"` is the only value ever observed; no runtime to test against | Run a fan-out workflow with calls slow enough to distinguish concurrent from sequential timing | open |

## Operating Rules

**Always:**
- Decide the failure-handling shape before writing individual nodes, not after
- Make every failure/error path still reach `End`
- Use a bounded number of explicit attempts for anything that would otherwise need a loop

**Never:**
- Assume "call an API" means only the success path needs a node
- Design a cycle -- qubi's graph format doesn't support one; represent repetition as explicit bounded repetition instead
