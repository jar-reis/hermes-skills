# Context compression task-list reconciliation — 2026-06-15

## Signal
During a cold-restart wrap, the chat context compressed and replayed an older active task list with several repair tasks still marked `pending`, even though the latest user request was only to wrap, update lifecycle ledgers, notify the fleet, and prepare for cold restart.

## Risk
If the agent treats the preserved task list as an active mandate after the wrap scope has changed, it may resume deferred repair work or leave stale pending tasks in the session state. That makes the final handoff contradictory: the artifacts say "deferred/no mutation," but the live todo list still says "pending."

## Rule
At session close, after the handoff/ledger/snapshot are written and after any context compression or active-task replay, reconcile the live todo list to the wrap outcome:

1. Mark tasks actually completed by the wrap as `completed`.
2. Mark tasks explicitly deferred to cold restart, awaiting approval, or outside the closeout scope as `cancelled` with a short reason.
3. Do not resume deferred work just because the replayed task list still shows it as pending.
4. Mention the reconciliation in the final response so the next session does not infer hidden in-flight work.

## Worked shape
For a wrap request over a broader repair plan:

- `write multi-session coordination artifacts` -> `completed`
- `restore launchd / install deps / move secret backup` -> `cancelled` or deferred with "requires explicit repair approval"
- final answer names the handoff path and the deferred tasks

## Falsifier
If the final handoff says "ready for cold restart / no mutation performed" but `todo()` still shows prerequisite repair tasks as `pending`, the session close is incomplete.