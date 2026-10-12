---
name: ptt-close
description: As a Partitur supervisor (designer or sub-designer), close a task whose holder reported it done, reopen it, or cancel a task nobody holds. Arguments: N, reopen N, cancel N. Use when a subordinate reported a task done, or a task is no longer wanted.
---

# Close, reopen, or cancel a task

The user's command (`/ptt-close`) is the approval for the records this skill
writes, and for nothing else; the work itself still needs AtE. Agreement in
conversation without the command is not approval.

`<name>` is this session's holder name; you must supervise the task. When
the supervisor is vacant (for example its sub-designer left), the user acts
with `--as user`.

## Close (`N`)

1. Read the done report and `status.md` (`<records>/bin/ptt show <N>`), and
   check them against the charter's acceptance criteria and the records
   they cite. Report your assessment to the user.
2. If every criterion is met, close the task; the user's `/ptt-close N` is
   the approval. If a criterion is not met, report what is missing and do
   not close; ask the user with a numbered list (the rules file's form):
   `1. Reopen` (with the missing criteria), `2. Wait` (the holder
   completes it first), `3. No decision, discuss further`, your
   recommendation first.

   ```
   <records>/bin/ptt close <N> --as <name>
   ```

   The task moves to `tasks/done/`. A `design` task closes only after all
   its subtasks are closed or cancelled.
3. Carry what the task found into the design (a request against the design
   document), and offer the task holder's session to be cleared.

## Reopen (`reopen N`)

When the user runs `/ptt-close reopen N` for a criterion not met:

```
<records>/bin/ptt reopen <N> --as <name> --reason "<which criterion, why>"
```

The holder continues.

## Cancel (`cancel N`)

A task nobody holds that is no longer wanted, when the user runs
`/ptt-close cancel N`:

```
<records>/bin/ptt cancel <N> --as <name> --reason "<why>"
```

A held task cannot be cancelled: its holder leaves first, with your
approval (`/ptt-leave approve N`). Only a holder that is gone is freed
(`/ptt-leave free N`, which asks for `--force` while the holder still has
recent records).
