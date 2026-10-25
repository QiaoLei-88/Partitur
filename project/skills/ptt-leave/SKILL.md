---
name: ptt-leave
description: Leave this session's role or task, approve a subordinate's leave request, or free a role or task whose holder is gone. Arguments: none, approve N, free N|designer|integrator.
---

# Leave, approve leaving, or free

The command, or an AtE naming these records, approves the records this skill
writes; other work needs AtE (rules file). `<name>` is your holder name.

## Leave (no argument)

1. Bring your status record up to date: your task's `status.md` (the
   designer's: of `T0000`), or `<records>/handoff/integrator.md`: what is
   done (requests with merge commits), what is open, where it stands;
   nothing only in this conversation. Record it with
   `<records>/bin/ptt record -m "<message>" <file>`.
2. `<records>/bin/ptt leave <name> --status "<one-line summary>"`.
   - Refused while something waits on you as a supervisor (a leave request
     or done report below you), or, for the integrator, while a recorded
     decision is not carried out: settle that first.
   - A task holder only asks: tell the user to run `/ptt-leave approve <N>`
     in the supervisor's session (`ptt whoami <name>` names it), or to
     approve `--as user` when it is vacant. Until then you hold the task;
     the approval reaches this session through its inbox (`/ptt-inbox`, in
     Claude Code with the user's next message).
   - The designer and the integrator leave at once: the user supervises
     them, and the command is the approval.
3. After leaving, offer the user to clear this session.

## Approve (`approve N`)

As task N's supervisor (or `--as user` when vacant): read its `status.md`
and leave request (`<records>/bin/ptt show N`). Clear enough for a
successor: `<records>/bin/ptt approve-leave <N> --as <name>` (the task is
ready again). Otherwise tell the user what is missing; the holder adds it.

## Free (`free N|designer|integrator`)

A supervisor frees a task whose holder is gone (`ptt inbox` lists holders
with no record for seven days):
`<records>/bin/ptt free <N> --as <name> --reason "<why>"`; the task is ready
again, its `status.md` shows where it stood. With recent records the tool
needs `--force`, added only when the user knows the holder is gone. Only the
user frees the designer (`T0000`) or the integrator, in any session:
`<records>/bin/ptt free designer --as user --reason "<why>"` (same
`--force` rule).
