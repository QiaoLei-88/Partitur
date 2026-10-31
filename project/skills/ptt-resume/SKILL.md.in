---
name: ptt-resume
description: "Continue as a holder in a fresh session or reload its handover after context is cleared: binds the holder name to this session and catches up from the records. Argument: the holder name (integrator-1, designer-g1, worker-T0007)."
---

# Continue as a holder

The command, or an AtE naming these records, approves the records this skill
writes; other work needs AtE (rules file).

1. No argument: `<records>/bin/ptt who`; show the holders and ask which one
   this session continues as. Stop.
2. `<records>/bin/ptt resume NAME`. If refused (NAME holds nothing, or this
   session already is another holder), report why and stop; never work
   around it.
3. NAME is your holder name from now on, as if you had taken it
   (`/ptt-take`, step 3). The tool binds it to this session where the agent
   tool gives a session ID. If the binding moved to a different session,
   the earlier session can no longer write as it: remind the user to stop
   using that earlier session. If already bound here, continue to read the
   handover without taking again. Report every `note:` the tool printed.
4. Read what NAME starts from (`/ptt-take`, step 4) and its status record
   (`status.md`, or `<records>/handoff/integrator.md`), then report where it
   stands and the next step.

In Claude Code, `/clear` starts a fresh session ID: use `/ptt-resume NAME`
to continue the holder and reload its handover.

In Codex invoke this skill as `$ptt-resume NAME`. A fresh chat or fork must
resume to take over; continuing or compacting the same thread keeps its
binding. `$ptt-whoami` checks it without changing it.
