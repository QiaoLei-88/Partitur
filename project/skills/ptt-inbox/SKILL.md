---
name: ptt-inbox
description: Show what is new in the records for this session's holder since it last looked (a subordinate's status or done report, an amendment, a note, a review or decision on its request) and what waits on it. Use for: anything new, what needs me, before starting a step. Argument: none or a holder name.
---

# Inbox

The command, or an AtE naming these records, approves the records this skill
writes (it writes none); other work needs AtE (rules file).

1. `<records>/bin/ptt inbox` (the holder bound to this session), or `ptt
   inbox <name>` with the holder name this session got from `/ptt-take` or
   `/ptt-resume`. Looking moves the holder's marker: the next look shows
   only what came after.
2. Report each line with a suggested next step: read a changed `status.md`
   or note and say what it means for your work; read an amendment (`ptt
   show <N>`); answer a review (`/ptt-pr-submit draft reply`); record a
   decided request's outcome in your status; settle what waits on you
   (`/ptt-close`, `/ptt-leave approve`). Act only with the user's command or
   AtE.

In Claude Code a prompt hook runs `ptt inbox --quiet` before each user
message and adds what is new to the conversation; treat such lines like this
report. A holder that is not bound to the session (`/ptt-resume`) gets
nothing from the hook.
