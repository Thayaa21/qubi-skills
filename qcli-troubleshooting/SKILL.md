---
name: qcli-troubleshooting
description: "Fix qubi command failures -- authentication problems, Windows console crashes, flow run not actually running, no flow create. Use when a qubi command errors, hangs, or does something that doesn't match its printed output."
---

# qubi Troubleshooting

> [qubi-cli](../qubi-cli/SKILL.md) is the reference for *what a command does*. This skill is for *why it just failed*, or worse, why it claimed to succeed when it didn't.

## What this skill is

A distinct trigger from `qubi-cli`: that skill answers "how do I run this command," this one answers "I ran it and something's wrong." It also documents three concrete traps in the current CLI that are easy to mistake for user error.

## When to invoke

- A `qubi` command errors, hangs, or exits non-zero for an unclear reason
- The printed output doesn't match what actually happened (e.g. "Workflow started!" but nothing ran)
- Login fails silently, or authenticated commands 401 after a login that appeared to succeed

## Trap 1: `flow run` can report success when nothing started

`client.run_workflow` tries the job-run REST endpoint, then a per-workflow REST endpoint, then probes the SignalR hub purely to explain why neither worked -- and raises if none of them actually started the workflow, so `flow run` now exits non-zero with a real error message on failure. If you see a job id come back, the run genuinely started. If the command exits non-zero with "Could not start the workflow," the workflow likely can only be run from the web UI for now -- that's a real platform limitation, not something to route around locally.

## Trap 2: Windows console crashes on Unicode output

Before the offline validator was hardened, `qubi flow validate`/`flow save`/`login` printed raw `✓`/`✗`/`⚠`/`→` characters, which crash with `UnicodeEncodeError` on a default Windows `cmd.exe` (cp1252 encoding) before any output appears. The validator now detects console encoding support and falls back to `OK`/`X`/`!`/`->`. If you see a `UnicodeEncodeError` traceback instead of a validation report, the installed `qubi` predates that fix -- reinstall from the current branch.

## Trap 3: `flow save` requires a pre-existing workflow

There is no `qubi flow create`. `flow save --workflow-id <id>` can only push to a workflow that already exists on the platform (created once, by hand, in the web UI). If `flow save` reports "workflow not found," the id is either wrong or refers to a workflow that was never created in the UI -- `qubi flow list` shows every workflow id that actually exists.

## Trap 4: `--no-browser` login has a known cookie-scope limitation

Direct API login (`qubi login --no-browser`) captures Identity Server session cookies, not AgentHub cookies -- so `qubi status` may report logged-in while `flow list`/`flow get`/etc. still 401. Prefer the default browser-based login; if debugging why it's stuck, use `qubi login --headed` to watch it happen instead of guessing.

## Diagnostic checklist

1. `qubi status` -- confirms whether there's a session at all, and for whom
2. Re-run the failing command with `-j`/`--json-output` where available -- structured output is easier to diagnose than the human-readable summary
3. For login problems specifically: `qubi login --headed` to watch the browser automation live
4. For `flow run`: read the raised error message, not just the exit code -- it now names which endpoints were tried

## Operating Rules

**Always:**
- Trust a non-zero exit code from `flow run` over a printed "started" message from an older qubi
- Use `qubi flow list` to confirm a workflow id exists before assuming `flow save` is broken
- Prefer default browser login over `--no-browser` unless there's a specific reason not to

**Never:**
- Assume `flow save` can create a workflow -- it can only update one that already exists
- Assume a `UnicodeEncodeError` is a workflow problem -- it's a console-encoding issue in an outdated install
