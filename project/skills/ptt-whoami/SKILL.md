---
name: ptt-whoami
description: Show what this session holds in a Partitur project (role or task, supervisor, next step) and what waits on it; with a holder name, continue as that holder after the context was cleared; with "all", who holds which role and task. Use when the user asks who this session is, what to do next, who is doing what, or names the holder a fresh session continues as.
---

# Who am I

The user's command (`/ptt-whoami`) is the approval for the records this skill
writes, and for nothing else; the work itself still needs AtE. Agreement in
conversation without the command is not approval.

- With the holder name this session received from `/ptt-take`, run
  `<records>/bin/ptt whoami <name>` and report: the role or task, the
  supervisor, the charter, and every line "waits on you" (leave requests,
  done reports, subordinates with no record for days). Suggest the next
  step for each.
- With a holder name as argument (`/ptt-whoami track-T0007`), typically
  after `/clear`: this session continues as that holder. Run
  `<records>/bin/ptt whoami <name>`, read what that role or task starts from
  (see `/ptt-take`, step 4) and its status record, and report where it
  stands. Use the name as before.
- Without a holder name in this conversation, say so: it holds nothing;
  `/ptt-take` gives it a role or task, or the user names the holder it
  continues as.
- `all`: run `<records>/bin/ptt who` and `<records>/bin/ptt tasks`, and
  report who holds what and which tasks are ready, blocked, or waiting.
