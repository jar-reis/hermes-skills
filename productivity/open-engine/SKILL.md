---
name: open-engine
description: "Operate Linear as a shared agent task queue with receipts."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Linear, Agent-Queue, Receipts, Workflow, Coordination]
---

# Open Engine

Turn Linear into a shared operating surface for AI agents. Agents read assigned issues, move statuses, leave receipts, and use issue history as the audit trail. This skill covers the queue structure, runner loop, receipt vocabulary, and smoke test — not Linear account setup or MCP server installation (see Prerequisites).

## When to Use

- "Set up Open Engine" or "agent queue in Linear"
- "Start the queue runner" or "run a queue pass"
- "Leave an AGENT CLAIMED / AGENT DONE receipt"
- "Resume a blocked issue" or "clear a human hold"
- "Add a teammate to the agent engine"
- "Browse optional standing skills"

## Prerequisites

- A Linear workspace with admin access to create teams, projects, labels, and statuses.
- An MCP-capable agent runtime (Codex, Claude Code, Claude Desktop, Cursor) connected to Linear's official MCP server.
- Linear MCP connection verified: agent can list a workspace, comment on a test issue, and move a test issue's status.
- A local private context file per runtime (e.g. `~/.codex/skills/open-agent-engine/SKILL.md`).

## Quick Reference

| Element | Value |
|---|---|
| Label (exact) | `agent-instructions` |
| Title pattern | `[agent instructions][<agent-code>][<type>] <subject>` |
| Queue statuses | Standing, Agent Todo, Agent Working, Agent Needs Input, Agent Review, Agent Done |
| Completed status | Agent Done |
| Ledger comment | `AGENT STATUS` (one per agent, updated in place) |
| Claim receipt | `AGENT CLAIMED` |
| Done receipt | `AGENT DONE` |
| Block receipt | `AGENT BLOCKED` + move to Agent Needs Input |
| Hold receipt | `AGENT HUMAN HOLD` + move to Agent Needs Input |
| Runner cadence | One task per run, then stop |

## Procedure

### 1. Naming decisions (before creating anything in Linear)

1. Pick or create a Linear team named `Agent Engine`.
2. Create one project: `Personal Agent Engine` (solo) or `Team Agent Engine` (team).
3. Create the exact label `agent-instructions`. The runner filters on this spelling.
4. Choose stable agent codes for every runtime: `alex-codex`, `alex-claude`, etc.
5. Name the private setup issue and status ledger before automation exists.

### 2. Build the six workflow statuses

Create these statuses in order on the chosen team:

| Status | Category | Purpose |
|---|---|---|
| Standing | Active | Durable setup, skills, SOPs, routing maps |
| Agent Todo | Active | Finite tasks waiting for the agent |
| Agent Working | Active | Claim lock — agent has taken the issue |
| Agent Needs Input | Active | Paused, waiting for Linear or human answer |
| Agent Review | Active | Completed, needs human judgment |
| Agent Done | Completed | Finished with receipt, no review needed |

### 3. Create the private context packet

1. Create a local file per runtime (e.g. `~/.codex/skills/open-agent-engine/SKILL.md`).
2. Include: engine version, agent code, Linear team/project, label, allowed sources, status ledger issue ID, optional standing skill directory issue ID, safety boundaries.
3. Create a private Standing setup issue titled `[agent instructions][all agents][standing_skill] Install Open Agent Engine core context v1`.
4. Leave `AGENT APPLIED` only after the runtime has actually installed the context locally.

### 4. Create the status ledger

1. Create a Standing issue: `[agent instructions][all agents][standing_status] Open Agent Engine status ledger`.
2. Apply the `agent-instructions` label.
3. Paste the AGENT STATUS format into the description.
4. Add one manual `AGENT STATUS` comment before automation exists.
5. The runner updates that same comment in place every run — never add new heartbeat comments.

Status comment fields: agent code, runtime, installed version, automation status, last queue result (`checking`, `none`, `completed ISSUE-ID`, `blocked ISSUE-ID`, `holding ISSUE-ID`, `resumed ISSUE-ID`, `failed ISSUE-ID`).

### 5. Run the queue runner

Each run executes these steps in order, then stops:

1. Open the status ledger, update this agent's `AGENT STATUS` comment to `checking`.
2. Run mandatory standing preflight: compare target versions for shared skills, SOPs, routing maps, voice guides, safety rules.
3. Run optional standing skill preflight for subscribed skills only. Apply same-scope updates; do not browse or install new skills.
4. Check `AGENT HUMAN HOLD` issues. Resume only after the human answers in their thread or the agent records `AGENT HUMAN ANSWERED`.
5. Check `AGENT BLOCKED` issues. Resume only after the missing answer appears on the same Linear issue.
6. Check delegated issues this agent routed to others. Leave `AGENT FOLLOW-UP` if anything changed.
7. Claim the oldest eligible `Agent Todo` issue assigned to this operator. Move to `Agent Working`, leave `AGENT CLAIMED`.
8. Process exactly one task. Leave the right receipt. Update the ledger. Stop.

### 6. Receipt vocabulary

| Receipt | When to post |
|---|---|
| `AGENT CLAIMED` | Right after moving to Agent Working |
| `AGENT DONE` | Scoped work finished, no review needed |
| `AGENT BLOCKED` | Missing answer belongs on this Linear issue; move to Agent Needs Input |
| `AGENT UNBLOCKED` | Blocked issue's answer arrived on same issue |
| `AGENT HUMAN HOLD` | Answer belongs in human's agent thread; move to Agent Needs Input |
| `AGENT HUMAN ANSWERED` | Human answered the hold in their thread |
| `AGENT RESUMED` | Continuing a paused issue after UNBLOCKED or HUMAN ANSWERED |
| `AGENT FAILED` | Unrecoverable failure only; record last safe step + retry count |
| `AGENT APPLIED` | Runtime installed/adapted a standing context version locally |
| `AGENT SKILL SUBSCRIBED` | Human approved first install of an optional standing skill |
| `AGENT SKILL INSTALLED` | Runtime installed the optional skill locally |
| `AGENT SKILL UPDATED` | Subscribed skill received a same-scope local update |
| `AGENT SKILL DECLINED` | Human declined or deferred an optional skill |
| `AGENT FOLLOW-UP` | Delegated issue's state changed |
| `AGENT STATUS` | Single ledger comment per agent, updated in place |

### 7. Smoke test

Run three test tasks before trusting the engine:

1. **Hello-world**: `[agent instructions][<agent-code>][task] Say hello from the queue.` Verify `AGENT CLAIMED` → `AGENT DONE` → Agent Done status → ledger says `completed ISSUE-ID`.
2. **Blocked-resume**: Create an intentionally incomplete issue. First run should leave `AGENT BLOCKED` + Agent Needs Input. Answer on the same issue, then verify `AGENT UNBLOCKED` → `AGENT RESUMED` → `AGENT DONE`.
3. **Human-hold**: Ask the agent to request local runtime permission. Verify `AGENT HUMAN HOLD` → ledger says `holding ISSUE-ID` → `AGENT HUMAN ANSWERED` after your reply → completion.

### 8. Team expansion

- Create a private routing map: human, Linear assignee, runtime, agent code, ownership area.
- Assign cross-agent work to the human who owns the target agent — never to yourself.
- Write routed tasks so the target agent can read them cold: requester, outcome, sources, acceptance criteria, output location, boundaries, pause rule.
- Onboard one teammate at a time with a tiny smoke test.

## Pitfalls

- **No issue found**: Check assignee, `agent-instructions` label, `Agent Todo` status, the `[agent instructions]` title marker, and that the second title bracket matches this runtime's agent code.
- **Double-claim**: Move to `Agent Working` before task work and leave `AGENT CLAIMED`. The status move is the visible lock. If two runtimes share one operator, scope pickup by agent-code bracket.
- **Ledger spam**: Find the existing `AGENT STATUS` comment for the current agent code and update it in place by comment ID — never add new top-level comments.
- **Blocked issues never resume**: Treat `AGENT BLOCKED` as a pause. Look for the answer on the same issue, then post `AGENT UNBLOCKED` + `AGENT RESUMED`.
- **Agent asks permission questions in Linear**: Use `AGENT HUMAN HOLD`. Ask in the human's own agent thread, keep the issue in `Agent Needs Input`, set ledger to `holding ISSUE-ID`.
- **Optional skills auto-install during setup**: Standard setup records the directory only. First install requires explicit human approval in that runtime's thread.
- **Work assigned to another agent goes nowhere**: Assign the issue to the human who owns the target agent, then check routing map, target heartbeat, label, title marker, and status.
- **Agent tries to publish/deploy/delete**: Add explicit ask-first boundaries to the private context and task body. External or destructive actions require issue-level approval.

## Verification

After the smoke test, verify the full loop with this check via the `terminal` tool:

```bash
# Confirm the three smoke-test issues reached Agent Done
# (run from the agent runtime, using Linear MCP tools)
# Expected: all three issues in Agent Done status,
#   each with AGENT CLAIMED + AGENT DONE receipts,
#   ledger showing completed ISSUE-ID for each.
```

If any smoke-test issue is not in `Agent Done` with the correct receipts, fix the contract and rerun the smoke test before trusting the engine.