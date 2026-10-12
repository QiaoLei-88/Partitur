---
name: ptt-leave
description: Leave this session's Partitur role or task, approve a subordinate's request to leave, or free a role or task whose holder is gone. Arguments: none (this session leaves), approve N, free N|designer|integrator. Use when the user wants this session to stop holding its role or task, or to settle another session's departure.
---

# Leave, approve leaving, or free

The user's command (`/ptt-leave`) is the approval for the records this skill
writes, and for nothing else; the work itself still needs AtE. Agreement in
conversation without the command is not approval.

The tool is `<records>/bin/ptt`; `<name>` is the holder name this session
received when it took its role or task.

## This session leaves (no argument)

1. Bring your status record up to date: `status.md` of your task, or
   `<records>/handoff/designer.md` / `integrator.md` for a role. It must say
   what is done (requests with merge commits), what is open, and where it
   stands; nothing may exist only in this conversation. Record it:

   ```
   <records>/bin/ptt record -m "<message>" <file>
   ```
2. Run `<records>/bin/ptt leave <name> --status "<one-line summary>"`.
   - The tool refuses while something waits on you as a supervisor (a
     subordinate's leave request or done report), or, for the integrator,
     while a recorded decision is not carried out. Settle that first.
   - A task holder only *asks* to leave: the supervisor shown by
     `<records>/bin/ptt whoami <name>` must approve; if the supervisor is
     vacant, the user approves (`--as user`). Tell the user to run
     `/ptt-leave approve <N>` in the supervisor's session. Until then this
     session still holds the task.
   - A designer or integrator leaves at once: the user is its supervisor,
     and the user's command is the approval.
3. After leaving, offer the user to clear this session (`/clear`).

## Approve a subordinate's request (`approve N`)

As the supervisor of task N (or the user, `--as user`, when the supervisor is
vacant): read its `status.md` and the leave request
(`<records>/bin/ptt show N`). If the status is clear enough for a successor,
run `<records>/bin/ptt approve-leave <N> --as <name>`; the task becomes ready
again. If not, tell the user what is missing; the holder fills it in first.

## Free a role or task whose holder is gone (`free ...`)

A supervisor notices a gone subordinate (`<records>/bin/ptt whoami <name>`
lists holders with no record for seven days) and repairs the gap. The tool
refuses a holder with recent records unless `--force` is added because the
user knows that session is gone:

```
<records>/bin/ptt free <N> --as <name> --reason "<why>"
```

The task becomes ready; its `status.md` shows where it stood. Only the user
frees the designer or integrator role, in any session at the user's
request:

```
<records>/bin/ptt free designer --as user --reason "<why>"
```
