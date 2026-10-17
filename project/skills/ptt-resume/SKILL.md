---
name: ptt-resume
description: Continue as a holder in this session, typically after /clear: binds the holder name to this session and catches up from the records. Argument: the holder name (integrator-1, designer-g1, worker-T0007).
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
   tool gives a session ID: the session that was NAME before can no longer
   write as it. Report every `note:` the tool printed, and remind the user
   to stop using that earlier session.
4. Read what NAME starts from (`/ptt-take`, step 4) and its status record
   (`status.md`, or `<records>/handoff/integrator.md`), then report where it
   stands and the next step.
